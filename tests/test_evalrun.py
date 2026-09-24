"""The eval runner (ADR-0027) on a small evals directory built here: staging, what
each run writes, errors, resuming, and that the answers are read only after the runs.
`diagnose` is a fake; nothing opens a socket."""

import gzip
import json
import subprocess
from pathlib import Path

import pytest

from perfettoagent import cli, evalrun
from perfettoagent.cli import main
from perfettoagent.loop import RunFailed

REPORTS = Path(__file__).parent / "fixtures" / "reports"
PLANTED, CLEAN = "a1b2c3d4", "e5f60718"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def root(tmp_path_factory) -> Path:
    """evals/ in miniature: a bundle with one branch per case, each case's inputs and
    run metadata, and the answers apart."""
    root = tmp_path_factory.mktemp("evals")
    work = tmp_path_factory.mktemp("work") / "app"
    work.mkdir()
    _git(work, "init", "-q", "-b", "main")
    _git(work, "config", "user.email", "dev@example.com")
    _git(work, "config", "user.name", "Dev")
    shas = []
    for name in ("base", "change", "head"):
        (work / f"{name}.txt").write_text(name)
        _git(work, "add", "-A")
        _git(work, "commit", "-q", "-m", name)
        shas.append(_git(work, "rev-parse", "HEAD"))
    for case_id in (PLANTED, CLEAN):
        _git(work, "branch", case_id)
    (root / "repos").mkdir()
    _git(work, "bundle", "create", "-q", str(root / "repos" / "app.bundle"),
         PLANTED, CLEAN)  # fmt: skip
    base, change, head = shas
    for case_id in (PLANTED, CLEAN):
        directory = root / "cases" / case_id
        directory.mkdir(parents=True)
        for side in ("baseline", "current"):
            (directory / f"{side}.perfetto-trace.gz").write_bytes(gzip.compress(b"x"))
        inputs = {"schema": 1, "repo": "app", "range": {"base": base, "head": head}}
        (directory / "inputs.json").write_text(json.dumps(inputs))
        metadata = {
            "schema": 1,
            "commit": head,
            "tree_dirty": False,
            "debuggable": False,
            "build_type": "benchmark",
            "device": None,
        }
        (directory / "run.json").write_text(json.dumps(metadata))
    (root / "answers").mkdir()
    answers = {
        PLANTED: ("regression", ["heap_growth_objects_by_class"], change),
        CLEAN: ("no_regression", [], None),
    }
    for case_id, (verdict, metrics, culprit) in answers.items():
        answer = {"schema": 1, "verdict": verdict, "metrics": metrics,
                  "culprit": culprit}  # fmt: skip
        (root / "answers" / f"{case_id}.json").write_text(json.dumps(answer))
    return root


@pytest.fixture(scope="module")
def culprit(root) -> str:
    return json.loads((root / "answers" / f"{PLANTED}.json").read_text())["culprit"]


class FakeDiagnose:
    """Answers every run with the regression fixture, blaming `culprit`, and records
    what it was given. `fail` names (case, run) pairs that raise RunFailed."""

    def __init__(self, root: Path, culprit: str, fail=()):
        self.root, self.culprit, self.fail = root, culprit, set(fail)
        self.calls: list[dict] = []
        self.answers_read = False

    def __call__(self, **kwargs) -> dict:
        assert not self.answers_read, "the answers were read before a run"
        self.calls.append(kwargs)
        repo = Path(kwargs["repo"])
        for path in (kwargs["baseline"], kwargs["current"], repo):
            text = str(path)
            assert str(self.root) not in text
            assert PLANTED not in text and CLEAN not in text
        n = len(self.calls)
        if n in self.fail:
            raise RunFailed("a tool failed: sk-proj-abc123 leaked")
        diagnosis = json.loads((REPORTS / "regression.json").read_text())
        diagnosis["culprit"]["commit"] = self.culprit
        return diagnosis


def run(root, out, fake, **kwargs):
    return evalrun.run_eval(
        out, root=root, diagnose_fn=fake, log=lambda line: None, **kwargs
    )


def test_every_case_runs_n_times_and_each_run_is_written(root, culprit, tmp_path):
    fake = FakeDiagnose(root, culprit)
    scores = run(root, tmp_path / "out", fake, runs=2)
    assert len(fake.calls) == 4
    for case_id in (PLANTED, CLEAN):
        for n in (1, 2):
            directory = tmp_path / "out" / "runs" / case_id / str(n)
            assert {p.name for p in directory.iterdir()} == {
                "diagnosis.json",
                "diagnosis.md",
                "result.json",
            }
            result = json.loads((directory / "result.json").read_text())
            assert (result["provider"], result["model"], result["effort"]) == (
                "openai",
                "gpt-5.6-luna",
                "high",
            )
            assert result["outcome"]["run"] == n
    assert json.loads((tmp_path / "out" / "scores.json").read_text()) == scores
    # Every run said regression: the planted case is detected and attributed, and
    # the clean pair is a false positive, every time.
    rates = scores["rates"]
    assert (rates["detection"]["hits"], rates["detection"]["of"]) == (2, 2)
    assert (rates["attribution"]["hits"], rates["attribution"]["of"]) == (2, 2)
    assert (rates["false_positive"]["hits"], rates["false_positive"]["of"]) == (2, 2)
    assert (
        "| Detection | 100% (2/2) | 100% | 100% |"
        in (tmp_path / "out" / "scores.md").read_text()
    )


def test_each_run_gets_the_case_s_run_metadata_and_range(root, culprit, tmp_path):
    fake = FakeDiagnose(root, culprit)
    run(root, tmp_path / "out", fake, runs=1, cases=[PLANTED])
    [call] = fake.calls
    inputs = json.loads((root / "cases" / PLANTED / "inputs.json").read_text())
    assert call["git_range"] == f"{inputs['range']['base']}..{inputs['range']['head']}"
    assert call["metadata"]["commit"] == inputs["range"]["head"]
    assert (call["metric"], call["provider"], call["effort"]) == (
        "auto",
        "openai",
        "high",
    )


def test_a_run_that_raises_is_recorded_redacted_and_the_rest_go_on(
    root, culprit, tmp_path
):
    fake = FakeDiagnose(root, culprit, fail={1})
    scores = run(root, tmp_path / "out", fake, runs=1, cases=[PLANTED, CLEAN])
    assert scores["errors"] == 1
    failed = tmp_path / "out" / "runs" / PLANTED / "1"
    assert not (failed / "diagnosis.json").exists()
    error = json.loads((failed / "result.json").read_text())["outcome"]["error"]
    assert error.startswith("RunFailed: a tool failed")
    assert "sk-proj" not in error
    assert scores["rates"]["detection"]["of"] == 1


def test_a_run_with_a_result_is_not_run_again(root, culprit, tmp_path):
    out = tmp_path / "out"
    run(root, out, FakeDiagnose(root, culprit), runs=1)
    again = FakeDiagnose(root, culprit)
    scores = run(root, out, again, runs=2)
    assert len(again.calls) == 2  # only the second repetition
    assert scores["runs"] == 4


def test_an_unfetched_lfs_trace_stops_the_run_before_any_diagnosis(
    root, culprit, tmp_path
):
    copy = tmp_path / "evals"
    subprocess.run(["cp", "-R", str(root), str(copy)], check=True)
    trace = copy / "cases" / CLEAN / "current.perfetto-trace.gz"
    trace.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
    fake = FakeDiagnose(copy, culprit)
    with pytest.raises(SystemExit, match="Git LFS pointer"):
        run(copy, tmp_path / "out", fake)
    assert fake.calls == []


def test_the_model_and_effort_reach_every_run_and_its_result(root, culprit, tmp_path):
    fake = FakeDiagnose(root, culprit)
    out = tmp_path / "out"
    run(root, out, fake, runs=1, cases=[CLEAN], provider="anthropic",
        model="claude-opus-5-5", effort="low")  # fmt: skip
    [call] = fake.calls
    assert (call["provider"], call["model"], call["effort"]) == (
        "anthropic",
        "claude-opus-5-5",
        "low",
    )
    result = json.loads((out / "runs" / CLEAN / "1" / "result.json").read_text())
    assert (result["provider"], result["model"], result["effort"]) == (
        "anthropic",
        "claude-opus-5-5",
        "low",
    )
    scores = json.loads((out / "scores.json").read_text())
    assert (scores["model"], scores["effort"]) == ("claude-opus-5-5", "low")


def test_results_from_other_settings_are_never_pooled(root, culprit, tmp_path):
    out = tmp_path / "out"
    run(root, out, FakeDiagnose(root, culprit), runs=1, cases=[CLEAN])
    again = FakeDiagnose(root, culprit)
    with pytest.raises(SystemExit, match="never pooled"):
        run(root, out, again, runs=1, cases=[CLEAN], effort="low")
    assert again.calls == []


def test_the_cli_passes_the_model_and_effort_on(monkeypatch, tmp_path):
    asked = {}

    def fake_run_eval(out, **kwargs):
        asked.update(kwargs, out=out)
        return _SCORES

    monkeypatch.setattr(cli, "run_eval", fake_run_eval)
    argv = ["eval", "--provider", "anthropic", "--effort", "medium", "--runs", "1"]
    assert main(argv) == 0
    assert (asked["provider"], asked["model"], asked["effort"]) == (
        "anthropic",
        "claude-opus-5-5",
        "medium",
    )
    assert asked["out"].name == "claude-opus-5-5-medium-auto"


@pytest.mark.parametrize(
    "flags, message",
    [
        (["--provider", "anthropic", "--model", "gpt-5.6-luna"], "not anthropic"),
        (["--effort", "max"], "has no effort 'max'"),
    ],
)
def test_the_cli_refuses_a_model_it_cannot_run(monkeypatch, capsys, flags, message):
    monkeypatch.setattr(cli, "run_eval", lambda *a, **k: pytest.fail("ran"))
    assert main(["eval", *flags]) == 2
    assert message in capsys.readouterr().err


_SCORES = {
    "rates": {
        name: {"hits": 0, "of": 0}
        for name in ("detection", "attribution", "false_positive")
    },
    "errors": 0,
    "cost": {"usd": 0.0},
}


def test_the_cli_rejects_zero_runs(capsys):
    assert main(["eval", "--runs", "0"]) == 2
    assert "at least 1" in capsys.readouterr().err
