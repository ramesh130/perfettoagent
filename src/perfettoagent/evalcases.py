"""Eval cases: what the model is given, and, kept apart, what it should answer
(ADR-0015).

A case is an opaque id. Its model-visible inputs are in `evals/cases/<id>/`: a baseline
and a current trace, `inputs.json`, whose range names two commits in a fixture repo,
and `run.json`, the current trace's run metadata (`perfettoagent.run_metadata`),
sanitised so it names no plant (ADR-0025).
Its expected answers are in `evals/answers/<id>.json`, a directory the runner reads only
to score. `load_inputs` and `load_expected` read one side each, so code that builds the
model's prompt from `load_inputs` has nothing to leak.

The fixture repo is one git bundle holding a branch per case. `stage` gives the runner
what to hand the model: a directory it names, holding a clone of only the case's branch
(as `main`, with no remote, no reflog and no other case's objects) and the two traces,
so no path the model is shown runs through `evals/` or the case id. Staging is the
runner's setup, before the agent starts, so it makes a clone and writes to it; the agent
itself reads the clone through `perfettoagent.git` alone, which allows no write.

`evals/build_cases.py` writes all of this from the devicelab captures.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from perfettoagent.git import _REDIRECTING_ENV, GIT_TIMEOUT_S

# The repo's own evals/ directory. It is not in the wheel: the cases are the repo's
# fixtures, used from a checkout of it.
EVALS_DIR = Path(__file__).resolve().parents[2] / "evals"

# The inputs.json and answers/<id>.json layout this code reads.
SCHEMA_VERSION = 1

# What a case directory holds: its inputs, nothing else (a test checks it).
CASE_FILES = frozenset(
    {
        "inputs.json",
        "run.json",
        "baseline.perfetto-trace.gz",
        "current.perfetto-trace.gz",
    }
)

# The verdicts an answer can expect (the diagnosis schema's, ADR-0006). A case never
# expects `inconclusive`: every case has an answer.
VERDICTS = ("regression", "no_regression")


class CaseError(ValueError):
    """A case is missing, or its files do not have the layout this module reads."""


@dataclass(frozen=True)
class CaseInputs:
    """Everything the model may see about a case, and nothing else."""

    case_id: str
    baseline: Path
    current: Path
    range_base: str
    range_head: str
    # The current trace's run metadata, for `diagnose --run-json` (ADR-0025).
    run_metadata: Path
    # The fixture repo the range is in, holding every case's branch. The runner stages
    # from it; the model is given the staged clone, never this path, and never
    # `baseline` or `current` as they are here: their paths run through evals/.
    bundle: Path

    def stage(self, dest: Path) -> "StagedCase":
        """Everything the model is given, under `dest`, which must not exist yet:
        `dest/repo` and the two traces as `dest/baseline.perfetto-trace.gz` and
        `dest/current.perfetto-trace.gz`, and the run metadata as `dest/run.json`.
        Files are hard links where the filesystem allows, copies where it does not."""
        dest.mkdir(parents=True)
        return StagedCase(
            repo=self.checkout(dest / "repo"),
            baseline=_link(self.baseline, dest / self.baseline.name),
            current=_link(self.current, dest / self.current.name),
            run_metadata=_link(self.run_metadata, dest / self.run_metadata.name),
            range_base=self.range_base,
            range_head=self.range_head,
        )

    def checkout(self, dest: Path) -> Path:
        """Clone this case's history into `dest`, which must not exist yet, and return
        it. The range's commits are then `range_base..range_head` in it."""
        _git("clone", "--quiet", "--single-branch", "--branch", self.case_id,
             "--", str(self.bundle), str(dest))  # fmt: skip
        _git("-C", str(dest), "branch", "--quiet", "-m", "main")
        _git("-C", str(dest), "remote", "remove", "origin")
        _git("-C", str(dest), "reflog", "expire", "--expire=now", "--all")
        # A clone from a bundle copies its whole pack, other cases' commits included.
        # Unreachable now, but `cat-file` would still read them by sha: drop them.
        _git("-C", str(dest), "gc", "--quiet", "--prune=now")
        return dest


@dataclass(frozen=True)
class StagedCase:
    """A case as the model is given it: paths under a directory the runner chose."""

    repo: Path
    baseline: Path
    current: Path
    run_metadata: Path
    range_base: str
    range_head: str


@dataclass(frozen=True)
class Expected:
    """What a case should be diagnosed as. Never shown to the model."""

    case_id: str
    verdict: str
    # Any of these, named as the diagnosis's metric, counts as the right metric: some
    # regressions show on more than one (roadmap item 5).
    metrics: tuple[str, ...]
    # The commit that introduced the regression, or None for a clean pair.
    culprit: str | None


def list_cases(root: Path = EVALS_DIR) -> list[str]:
    """Every case id, sorted: an order that says nothing about what a case is."""
    cases = root / "cases"
    if not cases.is_dir():
        return []
    return sorted(p.name for p in cases.iterdir() if p.is_dir())


def load_inputs(case_id: str, root: Path = EVALS_DIR) -> CaseInputs:
    directory = root / "cases" / case_id
    inputs = _read(directory / "inputs.json")
    try:
        repo_range = inputs["range"]
        return CaseInputs(
            case_id=case_id,
            baseline=directory / "baseline.perfetto-trace.gz",
            current=directory / "current.perfetto-trace.gz",
            range_base=repo_range["base"],
            range_head=repo_range["head"],
            run_metadata=directory / "run.json",
            bundle=root / "repos" / f"{inputs['repo']}.bundle",
        )
    except (KeyError, TypeError) as e:
        raise CaseError(f"{directory / 'inputs.json'}: missing {e}") from None


def load_expected(case_id: str, root: Path = EVALS_DIR) -> Expected:
    path = root / "answers" / f"{case_id}.json"
    answer = _read(path)
    try:
        expected = Expected(
            case_id=case_id,
            verdict=answer["verdict"],
            metrics=tuple(answer["metrics"]),
            culprit=answer["culprit"],
        )
    except (KeyError, TypeError) as e:
        raise CaseError(f"{path}: missing {e}") from None
    if expected.verdict not in VERDICTS:
        raise CaseError(
            f"{path}: verdict {expected.verdict!r} is not one of {VERDICTS}"
        )
    if (expected.verdict == "regression") != (expected.culprit is not None):
        raise CaseError(
            f"{path}: a regression names a culprit, and only a regression does"
        )
    return expected


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except FileNotFoundError:
        raise CaseError(f"no such case file: {path}") from None
    if not isinstance(value, dict) or value.get("schema") != SCHEMA_VERSION:
        raise CaseError(f"{path}: not a schema {SCHEMA_VERSION} case file")
    return value


def _link(source: Path, dest: Path) -> Path:
    try:
        os.link(source, dest)
    except OSError:  # another filesystem, or one without hard links
        shutil.copyfile(source, dest)
    return dest


def _git(*args: str) -> None:
    """git for staging, which writes, so not `perfettoagent.git`, whose allow-list is
    read-only. The same guards otherwise: no redirecting environment, and a timeout."""
    env = {k: v for k, v in os.environ.items() if k not in _REDIRECTING_ENV}
    subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
        env=env,
        timeout=GIT_TIMEOUT_S,
    )
