"""The verifier: each rule, with a hand-built bad output it must catch, and a good one
it must leave alone, against the tiny fixture trace and a git repo built per test."""

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import perfettoagent.verify as verify_module
from perfettoagent.diagnosis import DiagnosisInvalid, check_diagnosis
from perfettoagent.verify import RangeError, verify

# --- A small target repo, built at test time --------------------------------------
#
#   p0 (root) -- r0 (base) -- c1 -- c2 -- c3 ------ m1 ------ m2 (head)
#                   \                 \            /          /
#                    x1 (unmerged)     s1 ---------          /
#                                               o1 (a second root)
#
# Inside r0..m2: c1 c2 c3 s1 m1 o1 m2. Outside: p0, r0 (the base itself), x1.

_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
    # Neither the machine's nor the user's git config can reach the fixture.
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


class Repo:
    def __init__(self, path: Path):
        self.path = path
        self.sha: dict[str, str] = {}

    def git(self, *args: str) -> str:
        env = {**os.environ, **_ENV}
        return subprocess.run(
            [
                "git",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "init.defaultBranch=main",
                *args,
            ],
            cwd=self.path,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def commit(self, name: str, files: dict[str, str]) -> str:
        for rel, text in files.items():
            (self.path / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.path / rel).write_text(text)
            self.git("add", "--", rel)
        self.git("commit", "-q", "-m", name)
        self.sha[name] = self.git("rev-parse", "HEAD")
        return self.sha[name]

    def merge(self, name: str, branch: str, *extra: str) -> str:
        self.git("merge", "-q", "--no-ff", "-m", name, *extra, branch)
        self.sha[name] = self.git("rev-parse", "HEAD")
        return self.sha[name]


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> Repo:
    r = Repo(tmp_path_factory.mktemp("target"))
    r.git("init", "-q")
    r.commit("p0", {"app/Main.kt": "fun main() {}\n", "README.md": "app\n"})
    r.commit("r0", {"app/Main.kt": "fun main() { start() }\n"})
    r.git("branch", "unmerged")
    r.commit("c1", {"app/Startup.kt": "fun start() { readConfig() }\n"})
    r.commit("c2", {"docs/notes.md": "notes\n"})
    r.git("branch", "side")
    r.commit("c3", {"README.md": "app, faster\n"})
    r.git("checkout", "-q", "side")
    r.commit("s1", {"app/Cache.kt": "object Cache\n"})
    r.git("checkout", "-q", "main")
    r.merge("m1", "side")
    r.git("checkout", "-q", "--orphan", "vendor")
    r.git("rm", "-rq", "--cached", ".")
    shutil.rmtree(r.path / "app")
    shutil.rmtree(r.path / "docs")
    (r.path / "README.md").unlink()
    r.commit("o1", {"lib/Other.kt": "object Other\n"})
    r.git("checkout", "-q", "-f", "main")
    r.merge("m2", "vendor", "--allow-unrelated-histories")
    r.git("checkout", "-q", "unmerged")
    r.commit("x1", {"app/Startup.kt": "fun start() {}\n"})
    r.git("checkout", "-q", "main")
    # A tag whose name is a sha prefix, on a commit whose sha does not start with it.
    r.git("tag", SHADOWING_TAG, r.sha["c2"])
    return r


SHADOWING_TAG = "abcdef1"


@pytest.fixture(scope="module")
def git_range(repo) -> str:
    return f"{repo.sha['r0'][:10]}..main"


# --- Hand-built model outputs --------------------------------------------------------


def trace(sql: str, which: str = "current") -> dict:
    return {"kind": "trace", "trace": which, "sql": sql}


def commit(sha: str, path: str | None = None) -> dict:
    return {"kind": "commit", "sha": sha, "path": path}


def claim(text: str, *citations: dict) -> dict:
    return {"text": text, "citations": list(citations)}


def output(*claims: dict, culprit=None, metric=None, verdict="regression") -> dict:
    return {
        "verdict": verdict,
        "metric": metric,
        "confidence": "high",
        "culprit": culprit,
        "claims": list(claims),
        "caveats": ["emulator trace"],
    }


def culprit(sha: str) -> dict:
    return {"commit": sha, "files": ["app/Startup.kt"], "attribution": "direct"}


COUNT_SLICES = "SELECT count(*) AS n FROM slice"
NO_ROWS = "SELECT id FROM slice WHERE dur < -1000"


@pytest.fixture
def run_verify(repo, git_range, tiny_trace, trace_processor):
    """verify() against the tiny trace (as both sides) and the fixture repo."""

    def run(out: dict, **kwargs) -> dict:
        args = {
            "current": tiny_trace,
            "baseline": tiny_trace,
            "repo": repo.path,
            "git_range": git_range,
            "binary": trace_processor,
        }
        return verify(out, **{**args, **kwargs})

    return run


@pytest.fixture
def run_verify_git(repo, git_range, tiny_trace):
    """verify() for outputs with commit citations only: needs no trace processor."""

    def run(out: dict, **kwargs) -> dict:
        args = {
            "current": tiny_trace,
            "baseline": tiny_trace,
            "repo": repo.path,
            "git_range": git_range,
            "binary": Path("/nonexistent/trace_processor_shell"),
        }
        return verify(out, **{**args, **kwargs})

    return run


def dropped_reason(result: dict) -> str:
    [d] = result["dropped_claims"]
    return d["reason"]


# --- The control: a good diagnosis passes untouched ----------------------------------


def test_a_good_diagnosis_passes_untouched(run_verify, repo):
    c1 = repo.sha["c1"]
    out = output(
        claim("840 slices in the current trace", trace(COUNT_SLICES)),
        claim("and in the baseline", trace(COUNT_SLICES, "baseline")),
        claim("c1 added the config read", commit(c1[:8], "app/Startup.kt")),
        claim(
            "slices exist, and c1 is in range",
            trace("SELECT id FROM slice"),
            commit(c1),
        ),
        culprit=culprit(c1),  # full sha, cited by short and full shas above
        metric={
            "name": "slice_count",
            "unit": "slices",
            "baseline": 840,
            "current": 840,
            "delta": 0,
            "sql_used": COUNT_SLICES,
        },
    )
    before = copy.deepcopy(out)
    result = run_verify(
        out, run={"tool_calls": 3, "usage": _usage(), "usd": 0.5, "wall_time_s": 9.0}
    )

    assert out == before, "verify must not modify its input"
    assert result["dropped_claims"] == []
    assert [c["id"] for c in result["claims"]] == ["c1", "c2", "c3", "c4"]
    assert [c["text"] for c in result["claims"]] == [c["text"] for c in out["claims"]]
    for field in ("verdict", "metric", "confidence", "culprit", "caveats"):
        assert result[field] == out[field]
    assert result["schema_version"] == 1
    assert result["run"]["tool_calls"] == 3

    first = result["claims"][0]["citations"][0]
    assert (first["row_count"], first["error"]) == (1, None)
    # The fresh row count is the true total, not the 200-row cap.
    assert result["claims"][3]["citations"][0]["row_count"] == 840
    assert result["claims"][2]["citations"][0]["commit"] == c1

    v = result["verification"]
    assert v["verdict_before"] == "regression"
    assert v["explanation"] is v["culprit_dropped"] is v["metric_dropped"] is None
    assert v["citations_checked"] == v["citations_passed"] == 5
    check_diagnosis(result)
    json.dumps(result)


def _usage() -> dict:
    return {
        "input_tokens": 1,
        "output_tokens": 2,
        "cache_read_input_tokens": 3,
        "cache_creation_input_tokens": 4,
    }


# --- Rule 1: a trace citation re-runs to at least one row ---------------------------


def test_a_trace_citation_with_no_rows_is_dropped(run_verify):
    result = run_verify(
        output(claim("ok", trace(COUNT_SLICES)), claim("bad", trace(NO_ROWS)))
    )
    assert [c["text"] for c in result["claims"]] == ["ok"]
    [dropped] = result["dropped_claims"]
    assert dropped["id"] == "c2"
    assert dropped["reason"] == "citation 1: returned 0 rows"
    assert dropped["citations"][0]["row_count"] == 0
    assert result["verification"]["citations_passed"] == 1


@pytest.mark.parametrize(
    ("sql", "reason"),
    [
        ("DELETE FROM slice", "rejected by the SELECT-only gate"),
        ("SELECT 1; SELECT 2", "rejected by the SELECT-only gate"),
        ("SELECT FROM WHERE", "did not run"),
        ("SELECT * FROM no_such_table", "did not run"),
        ("INCLUDE PERFETTO MODULE no.such.module;\nSELECT 1", "did not run"),
    ],
)
def test_a_trace_citation_that_does_not_parse_or_run_is_dropped(
    run_verify, sql, reason
):
    result = run_verify(output(claim("bad", trace(sql))))
    assert reason in dropped_reason(result)
    assert result["dropped_claims"][0]["citations"][0]["row_count"] is None


def test_a_citation_re_runs_with_its_include_lines(run_verify):
    # android_startups exists only once its module is included.
    sql = (
        "INCLUDE PERFETTO MODULE android.startup.startups;\n"
        "SELECT count(*) FROM android_startups"
    )
    result = run_verify(output(claim("startups counted", trace(sql))))
    assert result["dropped_claims"] == []
    bare = run_verify(
        output(claim("no include", trace("SELECT count(*) FROM android_startups")))
    )
    assert "did not run" in dropped_reason(bare)


def test_a_citation_of_a_missing_baseline_is_dropped(run_verify):
    result = run_verify(
        output(claim("bad", trace(COUNT_SLICES, "baseline"))), baseline=None
    )
    assert "none was given" in dropped_reason(result)


def test_the_citation_runs_on_the_trace_it_names(run_verify, tmp_path, tiny_trace):
    # A current trace the SQL finds nothing in: the same SQL passes only on baseline.
    empty = tmp_path / "empty.perfetto-trace"
    empty.write_bytes(b"")
    result = run_verify(
        output(
            claim("baseline", trace("SELECT id FROM slice", "baseline")),
            claim("current", trace("SELECT id FROM slice")),
        ),
        current=empty,
    )
    assert [c["text"] for c in result["claims"]] == ["baseline"]
    assert dropped_reason(result) == "citation 1: returned 0 rows"


# --- Rule 2: a commit citation names a commit in the range that touches its path ----


@pytest.mark.parametrize("name", ["c1", "c2", "c3", "s1", "m1", "o1", "m2"])
def test_every_commit_inside_the_range_passes(run_verify_git, repo, name):
    result = run_verify_git(output(claim("in range", commit(repo.sha[name]))))
    assert result["dropped_claims"] == []


@pytest.mark.parametrize("name", ["p0", "r0", "x1"])
def test_a_commit_outside_the_range_is_dropped(run_verify_git, repo, name):
    # p0 is before the base, r0 is the base itself, x1 was never merged into head.
    result = run_verify_git(output(claim("out of range", commit(repo.sha[name]))))
    assert "is not inside the range" in dropped_reason(result)
    assert result["dropped_claims"][0]["citations"][0]["commit"] == repo.sha[name]


def test_a_range_given_by_full_shas_and_short_shas_means_the_same(run_verify_git, repo):
    for rng in (
        f"{repo.sha['r0']}..{repo.sha['m2']}",
        f"{repo.sha['r0'][:7]}..{repo.sha['m2'][:7]}",
    ):
        result = run_verify_git(
            output(
                claim("head", commit(repo.sha["m2"])),
                claim("base", commit(repo.sha["r0"])),
            ),
            git_range=rng,
        )
        assert [c["text"] for c in result["claims"]] == ["head"]


@pytest.mark.parametrize(
    "sha",
    [
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",  # well-formed, but no such commit
        "abc12",  # too short to be a sha
        "ABCDEF12",  # not lower-case hex
        "main",  # a branch name: a citation names a commit, not a ref
        "HEAD~1",
    ],
)
def test_a_commit_that_does_not_exist_is_dropped(run_verify_git, sha):
    result = run_verify_git(output(claim("bad", commit(sha))))
    assert result["verdict"] == "inconclusive"
    assert result["dropped_claims"][0]["citations"][0]["commit"] is None


def test_a_ref_named_like_a_sha_does_not_answer_for_it(run_verify_git, repo):
    assert not repo.sha["c2"].startswith(SHADOWING_TAG)
    result = run_verify_git(output(claim("tag", commit(SHADOWING_TAG))))
    assert "names no commit" in dropped_reason(result)


def test_a_sha_of_a_non_commit_object_is_dropped(run_verify_git, repo):
    tree = repo.git("rev-parse", "HEAD^{tree}")
    result = run_verify_git(output(claim("a tree", commit(tree))))
    assert "names no commit" in dropped_reason(result)


@pytest.mark.parametrize(
    ("name", "path"),
    [
        ("c1", "app/Startup.kt"),
        ("c1", "app"),  # a directory: the commit changed a file under it
        ("s1", "app/Cache.kt"),
        ("m1", "app/Cache.kt"),  # a merge: what it brought in from the side branch
        ("o1", "lib/Other.kt"),  # a root commit: its whole tree is its change
        ("m2", "lib/Other.kt"),
    ],
)
def test_a_commit_that_touches_its_path_passes(run_verify_git, repo, name, path):
    result = run_verify_git(output(claim("touches", commit(repo.sha[name], path))))
    assert result["dropped_claims"] == []


@pytest.mark.parametrize(
    ("name", "path"),
    [
        ("c1", "README.md"),
        ("c2", "app/Startup.kt"),
        ("m1", "README.md"),  # changed on the merge's first parent, not by the merge
        ("o1", "app/Main.kt"),
        ("c1", "app/Nope.kt"),
    ],
)
def test_a_commit_that_does_not_touch_its_path_is_dropped(
    run_verify_git, repo, name, path
):
    result = run_verify_git(
        output(claim("does not touch", commit(repo.sha[name], path)))
    )
    assert f"does not change {path!r}" in dropped_reason(result)


def test_citation_text_is_never_an_option_to_git(run_verify_git, repo, tmp_path):
    written = tmp_path / "pwned"
    c1 = repo.sha["c1"]
    result = run_verify_git(
        output(
            claim("sha as option", commit("--output=" + str(written))),
            claim("sha as option", commit("-p")),
            claim("path as option", commit(c1, f"--output={written}")),
            claim("path as pathspec magic", commit(c1, ":(glob)**")),
            claim("path as exclusion", commit(c1, ":!README.md")),
        )
    )
    assert not written.exists()
    assert result["claims"] == []
    assert len(result["dropped_claims"]) == 5
    reasons = [d["reason"] for d in result["dropped_claims"]]
    assert "is not a commit sha" in reasons[0] and "is not a commit sha" in reasons[1]
    for reason in reasons[2:]:
        assert "does not change" in reason or "git diff failed" in reason


# --- Rule 3: a claim with a failed citation, or none, is dropped with its reason -----


def test_a_claim_with_one_failed_citation_is_dropped_whole(run_verify, repo):
    result = run_verify(
        output(
            claim(
                "half right",
                trace(COUNT_SLICES),
                commit(repo.sha["x1"]),
                trace(NO_ROWS),
            )
        )
    )
    [dropped] = result["dropped_claims"]
    assert dropped["reason"] == (
        f"citation 2: {repo.sha['x1']} is not inside the range; "
        "citation 3: returned 0 rows"
    )
    # Every citation was still checked, and the one that passed says so.
    assert [c["error"] is None for c in dropped["citations"]] == [True, False, False]
    assert result["verification"]["citations_checked"] == 3


def test_a_claim_with_no_citations_is_dropped(run_verify_git, repo):
    result = run_verify_git(
        output(claim("trust me"), claim("cited", commit(repo.sha["c1"])))
    )
    assert [c["text"] for c in result["claims"]] == ["cited"]
    assert dropped_reason(result) == "the claim cites nothing"


# --- Rule 4: a culprit must be cited by a surviving claim ----------------------------


def test_an_uncited_culprit_is_dropped(run_verify_git, repo):
    out = output(
        claim("c2 is in range", commit(repo.sha["c2"])), culprit=culprit(repo.sha["c1"])
    )
    result = run_verify_git(out)
    assert result["culprit"] is None
    assert (
        "no surviving claim cites the culprit"
        in result["verification"]["culprit_dropped"]
    )
    assert result["verdict"] == "regression"  # a claim survived; only the culprit went
    assert result["confidence"] is None


def test_a_culprit_cited_only_by_a_dropped_claim_is_dropped(run_verify_git, repo):
    c1 = repo.sha["c1"]
    out = output(
        claim("c1 changed the readme", commit(c1, "README.md")),
        claim("c2 is in range", commit(repo.sha["c2"])),
        culprit=culprit(c1),
    )
    result = run_verify_git(out)
    assert result["culprit"] is None
    assert result["verification"]["culprit_dropped"]


def test_a_short_culprit_sha_matches_a_full_citation(run_verify_git, repo):
    c1 = repo.sha["c1"]
    result = run_verify_git(output(claim("c1", commit(c1)), culprit=culprit(c1[:7])))
    assert result["culprit"] == culprit(c1[:7])
    assert result["confidence"] == "high"


@pytest.mark.parametrize("sha", ["deadbeefdeadbeef", "--all", "main"])
def test_a_culprit_that_is_no_commit_is_dropped(run_verify_git, repo, sha):
    result = run_verify_git(
        output(claim("c1", commit(repo.sha["c1"])), culprit=culprit(sha))
    )
    assert result["culprit"] is None
    assert "names no commit" in result["verification"]["culprit_dropped"]


# --- Rule 5: no surviving claim, no verdict ------------------------------------------


def test_when_no_claim_survives_the_verdict_is_inconclusive(run_verify, repo):
    out = output(
        claim("no rows", trace(NO_ROWS)),
        claim("out of range", commit(repo.sha["p0"])),
        culprit=culprit(repo.sha["p0"]),
    )
    result = run_verify(out)
    assert result["verdict"] == "inconclusive"
    assert result["claims"] == []
    assert result["culprit"] is None
    assert result["confidence"] is None
    v = result["verification"]
    assert v["verdict_before"] == "regression"
    assert v["explanation"] == "no claim survived verification: all 2 were dropped"


@pytest.mark.parametrize("verdict", ["regression", "no_regression", "inconclusive"])
def test_a_diagnosis_with_no_claims_is_inconclusive(run_verify_git, verdict):
    result = run_verify_git(output(verdict=verdict))
    assert result["verdict"] == "inconclusive"
    assert result["verification"]["explanation"] == "the model made no claims"


# --- The metric's numbers are cited too ---------------------------------------------


def _metric(sql: str, baseline=1, current=2) -> dict:
    delta = None if baseline is None else current - baseline
    return {
        "name": "m",
        "unit": "x",
        "baseline": baseline,
        "current": current,
        "delta": delta,
        "sql_used": sql,
    }


def test_a_metric_whose_sql_returns_nothing_is_dropped(run_verify, repo):
    result = run_verify(
        output(claim("c1", commit(repo.sha["c1"])), metric=_metric(NO_ROWS))
    )
    assert result["metric"] is None
    assert result["verification"]["metric_dropped"] == (
        "its sql_used on the baseline trace: returned 0 rows"
    )


def test_a_metric_is_checked_only_on_the_sides_it_reports(run_verify, repo):
    # No baseline value, and no baseline trace: its sql_used is run on current only.
    result = run_verify(
        output(
            claim("c1", commit(repo.sha["c1"])),
            metric=_metric(COUNT_SLICES, baseline=None),
        ),
        baseline=None,
    )
    assert result["metric"] is not None


# --- Inputs: the model cannot pre-fill what our code fills ---------------------------


@pytest.mark.parametrize(
    "tamper",
    [
        lambda o: o.update(dropped_claims=[]),
        lambda o: o.update(schema_version=1),
        lambda o: o["claims"][0].update(verified=True),
        lambda o: o["claims"][0].update(id="c1"),
        lambda o: o["claims"][0]["citations"][0].update(row_count=5),
        lambda o: o["claims"][0]["citations"][0].update(error=None),
        lambda o: o.update(verdict="regressed"),
        lambda o: o.pop("caveats"),
    ],
)
def test_output_that_does_not_match_the_schema_is_refused(run_verify_git, repo, tamper):
    out = output(claim("c1", commit(repo.sha["c1"])))
    tamper(out)
    with pytest.raises(DiagnosisInvalid):
        run_verify_git(out)


@pytest.mark.parametrize(
    "rng", ["", "main", "..main", "main..", "r0...main", "nope..main"]
)
def test_a_malformed_range_is_an_error_not_a_verdict(run_verify_git, rng):
    with pytest.raises(RangeError):
        run_verify_git(output(), git_range=rng)


def test_a_missing_trace_is_an_error_not_a_verdict(run_verify_git, tmp_path):
    with pytest.raises(FileNotFoundError):
        run_verify_git(output(), current=tmp_path / "nope.perfetto-trace")


# --- Caching re-run results by hash -------------------------------------------------


def test_the_cache_serves_a_re_run_citation_without_the_trace_processor(
    run_verify, tmp_path, monkeypatch
):
    cache = tmp_path / "cache"
    out = output(claim("slices", trace(COUNT_SLICES)), claim("none", trace(NO_ROWS)))
    first = run_verify(out, cache_dir=cache)
    assert len(list(cache.iterdir())) == 2  # one entry per distinct query and trace

    def no_trace_processor(*args, **kwargs):
        raise AssertionError("the cache should have answered")

    monkeypatch.setattr(verify_module, "query_trace", no_trace_processor)
    second = run_verify(out, cache_dir=cache)
    assert second["claims"] == first["claims"]
    assert second["dropped_claims"] == first["dropped_claims"]


def test_the_cache_key_covers_the_trace_bytes(run_verify, tmp_path, tiny_trace):
    cache = tmp_path / "cache"
    other = tmp_path / "copy.perfetto-trace"
    other.write_bytes(tiny_trace.read_bytes())
    out = output(claim("slices", trace(COUNT_SLICES)))
    run_verify(out, cache_dir=cache)
    run_verify(out, cache_dir=cache, current=other)
    assert len(list(cache.iterdir())) == 1  # same bytes, another path: same entry
    other.write_bytes(b"")
    result = run_verify(out, cache_dir=cache, current=other)
    assert len(list(cache.iterdir())) == 2
    assert result["claims"][0]["citations"][0]["row_count"] == 1


def test_a_failed_query_is_not_cached(run_verify, tmp_path):
    cache = tmp_path / "cache"
    run_verify(
        output(claim("bad", trace("SELECT * FROM no_such_table"))), cache_dir=cache
    )
    assert not cache.exists() or not list(cache.iterdir())


# --- No model anywhere --------------------------------------------------------------


def test_the_verifier_calls_no_model():
    # Neither imported by the verifier's modules nor loaded by importing them.
    src = Path(verify_module.__file__).parent
    for name in (
        "verify.py",
        "diagnosis.py",
        "git.py",
        "query.py",
        "metrics/__init__.py",
    ):
        text = (src / name).read_text()
        assert "import anthropic" not in text and "from anthropic" not in text
    loaded = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, perfettoagent.verify; print('anthropic' in sys.modules)",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert loaded.stdout.strip() == "False"
