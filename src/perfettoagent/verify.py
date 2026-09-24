"""The verifier: the guardrail between the model's output and anything written.

`verify` takes the model's structured output and returns `diagnosis.json` with every
claim that cannot be backed up moved to `dropped_claims`. It is deterministic Python
that re-runs each citation. No prompt instruction replaces it and nothing skips it
(CLAUDE.md). The rules are roadmap item 4's:

1. A trace citation's SQL is re-run on the trace it names. It passes only if it gets
   through the SELECT-only gate, runs, and returns at least one row. The fresh
   `row_count` is recorded on the citation.
2. A commit citation passes only if its sha names a commit, the commit lies inside the
   range, and, when a path is given, the commit changed that path.
3. A claim with a failed citation, or with none, moves to `dropped_claims` with the
   reason.
4. If a culprit is set, at least one surviving claim must cite its commit; otherwise
   the culprit is dropped, with the reason.
5. If no claim survives, the verdict becomes `inconclusive`, with an explanation.

The metric's `sql_used` is checked like a trace citation too, on each trace the metric
reports a value for, since its numbers are claims (ADR-0006).

What passing means, and what it does not: a trace citation that passes proves the SQL
selects something on that trace, not that the claim's prose describes it truly. Nothing
here compares a number the model wrote to the rows; the rule is "runs and returns a
row", and the rows are there for a reader to check (ADR-0006).

"Inside the range" `base..head` means what `git log base..head` lists: `head` and its
ancestors, less `base` and its ancestors. So `head` is inside and `base` is not.

Nothing here imports the Anthropic SDK or calls a model.
"""

import copy
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path

from perfettoagent.diagnosis import (
    SCHEMA_VERSION,
    SIDES,
    check_diagnosis,
    check_output,
)
from perfettoagent.git import (
    SHA,
    GitError,
    changed_paths,
    is_ancestor,
    resolve_commit,
    resolve_sha,
)
from perfettoagent.query import QueryRejected, query_trace, split_includes
from perfettoagent.trace_processor import (
    TraceProcessorError,
    default_cache_dir,
    resolve_trace_processor,
    sha256_of,
)

# Where the agent keeps re-run citation results between runs (ADR-0006). A keyed
# metric's citation takes about 3 s per trace to re-run on a 23 MB heap dump, and an
# eval re-verifies the same citations on the same traces many times over. Outside the
# repo, always. `verify` uses it only when a caller passes it.
QUERY_CACHE_DIR = default_cache_dir() / "verified-queries"

# A trace processor error is a Python-style traceback of any length; a reason in
# dropped_claims only needs its gist.
_MAX_ERROR_CHARS = 500


class RangeError(ValueError):
    """The range is not `base..head` with both ends naming commits."""


@dataclass(frozen=True)
class _Range:
    """`base..head` in `repo`, both ends resolved to full shas."""

    repo: Path
    base: str
    head: str

    @classmethod
    def parse(cls, repo: Path, git_range: str) -> "_Range":
        base, sep, head = git_range.partition("..")
        if not sep or not base or not head or head.startswith("."):
            raise RangeError(f"a range is base..head, not {git_range!r}")
        ends = {}
        for name, rev in (("base", base), ("head", head)):
            full = resolve_commit(repo, rev)
            if full is None:
                raise RangeError(f"the range's {name}, {rev!r}, names no commit")
            ends[name] = full
        return cls(repo, ends["base"], ends["head"])

    def resolve(self, sha: str) -> str | None:
        """The full sha of the commit a model-written `sha` names, or None."""
        return resolve_sha(self.repo, sha)

    def contains(self, commit: str) -> bool:
        """What `git log base..head` lists: an ancestor of head (or head), and not an
        ancestor of base (or base)."""
        return is_ancestor(self.repo, commit, self.head) and not is_ancestor(
            self.repo, commit, self.base
        )


def check_range(repo: str | Path, git_range: str) -> str:
    """`git_range` as `base..head` in full shas. Raises RangeError unless it is
    `base..head` with both ends naming commits in `repo`: what `verify` will require,
    checked before an agent run spends anything on a range it would refuse."""
    rng = _Range.parse(Path(repo), git_range)
    return f"{rng.base}..{rng.head}"


def commit_in_range(repo: str | Path, git_range: str, sha: str) -> bool:
    """Whether `sha` names one commit inside `git_range` in `repo`, by the rule a
    commit citation is held to (ADR-0006). Raises RangeError for a bad range."""
    rng = _Range.parse(Path(repo), git_range)
    if not SHA.fullmatch(sha):
        return False
    full = rng.resolve(sha)
    return full is not None and rng.contains(full)


def verify(
    output: dict,
    *,
    current: str | Path,
    baseline: str | Path | None,
    repo: str | Path,
    git_range: str,
    run: dict | None = None,
    binary: Path | None = None,
    cache_dir: Path | None = None,
) -> dict:
    """Returns `diagnosis.json` (DIAGNOSIS_SCHEMA) for the model's `output`.

    `output` must match OUTPUT_SCHEMA, or DiagnosisInvalid is raised: fields only our
    code fills (`dropped_claims`, a citation's `row_count`) cannot be pre-filled by the
    model. `current` and `baseline` are the trace files; `baseline` may be None, and a
    citation of it then fails. `repo` is the target app's repo, read through git only;
    `git_range` is `base..head`. `run` is the agent run's cost, recorded as given.

    `binary` is the trace processor (default: the pinned one). `cache_dir`, if given,
    keeps each query result on disk under a hash of the trace's bytes, the binary's
    bytes and the SQL, so a citation already re-run on the same inputs is not re-run;
    QUERY_CACHE_DIR is the agent's. Without it, results are shared within this call.

    Raises RangeError for a malformed range, GitError if `repo` cannot be read,
    GitUnavailable if git cannot run, FileNotFoundError for a missing trace, and
    TraceProcessorError if the trace processor cannot be found: those are failures of
    the run, not of a citation, and must not look like a model that cited nothing.
    `output` is not modified.
    """
    started = time.monotonic()
    check_output(output)
    given = {"baseline": baseline, "current": current}
    traces = {side: None if t is None else Path(t) for side, t in given.items()}
    for side, trace in traces.items():
        if trace is not None and not trace.is_file():
            raise FileNotFoundError(f"no {side} trace at {trace}")
    rng = _Range.parse(Path(repo), git_range)
    queries = _Queries(traces, binary, cache_dir)

    diagnosis = copy.deepcopy(output)
    kept, dropped = [], []
    checked = passed = 0
    for i, claim in enumerate(diagnosis.pop("claims"), start=1):
        claim = {"id": f"c{i}", **claim}
        failures = []
        for n, citation in enumerate(claim["citations"], start=1):
            if citation["kind"] == "trace":
                _check_trace(citation, queries)
            else:
                _check_commit(citation, rng)
            checked += 1
            if citation["error"] is None:
                passed += 1
            else:
                failures.append(f"citation {n}: {citation['error']}")
        if not claim["citations"]:
            dropped.append({**claim, "reason": "the claim cites nothing"})
        elif failures:
            dropped.append({**claim, "reason": "; ".join(failures)})
        else:
            kept.append(claim)

    metric_dropped = _check_metric(diagnosis["metric"], queries)
    if metric_dropped:
        diagnosis["metric"] = None

    culprit_dropped = _check_culprit(diagnosis["culprit"], kept, rng)
    if culprit_dropped:
        diagnosis["culprit"] = None

    verdict_before = diagnosis["verdict"]
    explanation = None
    if not kept:
        diagnosis["verdict"] = "inconclusive"
        explanation = (
            "the model made no claims"
            if not dropped
            else f"no claim survived verification: all {len(dropped)} were dropped"
        )
    if diagnosis["verdict"] != verdict_before or culprit_dropped:
        diagnosis["confidence"] = None

    result = {
        "schema_version": SCHEMA_VERSION,
        "verdict": diagnosis["verdict"],
        "metric": diagnosis["metric"],
        "confidence": diagnosis["confidence"],
        "culprit": diagnosis["culprit"],
        "claims": kept,
        "caveats": diagnosis["caveats"],
        "dropped_claims": dropped,
        "verification": {
            "verdict_before": verdict_before,
            "explanation": explanation,
            "culprit_dropped": culprit_dropped,
            "metric_dropped": metric_dropped,
            "citations_checked": checked,
            "citations_passed": passed,
            "wall_time_s": round(time.monotonic() - started, 3),
        },
        "run": copy.deepcopy(run),
    }
    check_diagnosis(result)
    return result


def _check_trace(citation: dict, queries: "_Queries") -> None:
    """Rule 1. Sets the citation's `row_count` and `error`."""
    row_count, error = queries.row_count(citation["trace"], citation["sql"])
    citation["row_count"] = row_count
    citation["error"] = error


def _check_commit(citation: dict, rng: _Range) -> None:
    """Rule 2. Sets the citation's `commit` (full sha) and `error`."""
    sha, path = citation["sha"], citation["path"]
    citation["commit"] = None
    citation["error"] = None
    if not SHA.fullmatch(sha):
        citation["error"] = (
            f"{sha!r} is not a commit sha (7 to 64 lower-case hex digits)"
        )
        return
    full = rng.resolve(sha)
    if full is None:
        citation["error"] = f"{sha} names no commit in the repo (or is ambiguous)"
        return
    citation["commit"] = full
    if not rng.contains(full):
        citation["error"] = f"{sha} is not inside the range"
        return
    if path is None:
        return
    try:
        touched = changed_paths(rng.repo, full, path)
    except GitError as e:
        # git refused the path itself (outside the repo, say): the citation's fault.
        # git failing to run at all is GitUnavailable, not a GitError: it raises.
        citation["error"] = str(e)
        return
    if not touched:
        citation["error"] = f"{sha} does not change {path!r}"


def _check_metric(metric: dict | None, queries: "_Queries") -> str | None:
    """The metric's sql_used, as a trace citation on each side it has a value for."""
    if metric is None:
        return None
    for side in SIDES:
        if metric[side] is None:
            continue
        _, error = queries.row_count(side, metric["sql_used"])
        if error is not None:
            return f"its sql_used on the {side} trace: {error}"
    return None


def _check_culprit(culprit: dict | None, kept: list, rng: _Range) -> str | None:
    """Rule 4: a surviving claim must cite the culprit, compared as full shas, so a
    short and a full sha of the same commit match."""
    if culprit is None:
        return None
    sha = culprit["commit"]
    full = rng.resolve(sha)
    if full is None:
        return f"{sha!r} names no commit in the repo"
    cited = {
        c["commit"]
        for claim in kept
        for c in claim["citations"]
        if c["kind"] == "commit"
    }
    if full not in cited:
        return f"no surviving claim cites the culprit commit {sha}"
    return None


class _Queries:
    """Re-runs cited SQL, each distinct (trace, SQL) once per call, and on disk across
    calls when given a cache directory."""

    def __init__(self, traces: dict, binary: Path | None, cache_dir: Path | None):
        self._traces = traces
        self._binary = binary
        self._cache_dir = cache_dir
        self._digests: dict[Path, str] = {}
        self._results: dict[tuple, tuple[int | None, str | None]] = {}

    def row_count(self, side: str, sql: str) -> tuple[int | None, str | None]:
        """(row_count, None) if the SQL ran; (None, reason) if it could not."""
        trace = self._traces[side]
        if trace is None:
            return None, f"cites the {side} trace, but none was given"
        key = (side, sql)
        if key not in self._results:
            self._results[key] = self._run(trace, sql)
        row_count, error = self._results[key]
        if error is None and row_count < 1:
            return row_count, "returned 0 rows"
        return row_count, error

    def _run(self, trace: Path, sql: str) -> tuple[int | None, str | None]:
        """(row_count, None) from the cache or a fresh run; (None, reason) if the SQL
        is refused or does not run. Only a run's result is cached, never a failure: a
        timeout on a loaded machine must not become a permanent verdict."""
        statement, modules = split_includes(sql)
        # The binary is resolved here and not per query: a missing trace processor is
        # the run's failure, raised, never a citation's.
        if self._binary is None:
            self._binary = resolve_trace_processor()
        # A timeout is the query's own doing (a runaway join), so it fails the
        # citation like any other query that does not run; it is never cached.
        cached = self._cache_path(trace, statement, modules)
        if cached is not None and cached.is_file():
            try:
                return int(json.loads(cached.read_text())["row_count"]), None
            except (OSError, ValueError, KeyError):
                pass  # a damaged entry is re-run and rewritten
        try:
            result = query_trace(statement, trace, modules=modules, binary=self._binary)
        except QueryRejected as e:
            return None, f"rejected by the SELECT-only gate: {e}"
        except TraceProcessorError as e:
            return None, f"did not run: {_gist(str(e))}"
        if cached is not None:
            # Only the count: it is all a rule reads, and an entry stays tiny.
            _write_atomically(cached, json.dumps({"row_count": result["row_count"]}))
        return result["row_count"], None

    def _cache_path(self, trace: Path, statement: str, modules: list) -> Path | None:
        """The on-disk entry for this query: named by a sha256 over the trace's bytes,
        the trace processor's bytes, the statement and the modules. So an entry is
        never stale: any change to any input is a different name."""
        if self._cache_dir is None:
            return None
        key = json.dumps(
            [self._digest(trace), self._digest(self._binary), statement, modules]
        )
        return self._cache_dir / f"{hashlib.sha256(key.encode()).hexdigest()}.json"

    def _digest(self, path: Path) -> str:
        if path not in self._digests:
            self._digests[path] = sha256_of(path)
        return self._digests[path]


def _write_atomically(path: Path, text: str) -> None:
    """A concurrent verify sees the whole entry or none of it: a rename within one
    directory is atomic. ref: https://docs.python.org/3/library/os.html#os.replace"""
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(f".{os.getpid()}.{time.monotonic_ns()}.tmp")
    partial.write_text(text)
    partial.replace(path)


def _gist(message: str) -> str:
    """An error's last _MAX_ERROR_CHARS, which name what went wrong."""
    message = message.strip()
    return (
        message
        if len(message) <= _MAX_ERROR_CHARS
        else "…" + message[-_MAX_ERROR_CHARS:]
    )
