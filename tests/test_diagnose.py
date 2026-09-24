"""`diagnose`: the agent loop, its tools, and what it writes (roadmap item 7, #29).

The model is `fake_model.FakeModel`: the SDK's real Tool Runner and streaming parser,
over an in-process transport, answering from a script. No test opens a socket.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest
from conftest import LFS_POINTER
from fake_model import USAGE, FakeModel, reply, text, tool_use
from test_eval_cases import HINT_WORDS, hints_in

from perfettoagent import repo_tools
from perfettoagent.agent import (
    EFFORT,
    MAX_TOKENS,
    MODEL,
    SYSTEM_PROMPT,
    RunFailed,
    UnpricedModel,
    diagnose,
    first_message,
    usd,
)
from perfettoagent.diagnosis import OUTPUT_SCHEMA, DiagnosisInvalid, check_diagnosis
from perfettoagent.evalcases import EVALS_DIR, load_expected, load_inputs
from perfettoagent.git import GitUnavailable
from perfettoagent.metrics import UnknownMetric
from perfettoagent.repo_tools import REPO_TOOLS
from perfettoagent.trace_tools import TRACE_TOOLS
from perfettoagent.verify import RangeError

# A trace processor that is never reached: these tests' citations are commits only,
# and `diagnose` resolves the binary only when none is given.
NO_BINARY = Path("/nonexistent/trace_processor_shell")


# --- A small target repo: a base, one change, and a head ------------------------------


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> dict:
    return build_repo(tmp_path_factory.mktemp("target") / "checkout-q9")


def build_repo(path: Path) -> dict:
    """{path, sha: {base, change, head}, range}: `change` edits app/Feed.kt, and
    `head` edits another file. The directory's name is one no prompt contains."""
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "dev@example.com")
    _git(path, "config", "user.name", "Dev")
    shas = {}
    for name, body in (("base", "a\n"), ("change", "a\nb\n"), ("head", "a\nb\nc\n")):
        file = "app/Feed.kt" if name != "head" else "app/Other.kt"
        (path / "app").mkdir(exist_ok=True)
        (path / file).write_text(body)
        _git(path, "add", "-A")
        _git(path, "commit", "-q", "-m", f"{name} commit")
        shas[name] = _git(path, "rev-parse", "HEAD")
    return {"path": path, "sha": shas, "range": f"{shas['base']}..{shas['head']}"}


def answer(repo, *, culprit=True, **overrides) -> dict:
    """A valid OUTPUT_SCHEMA answer citing the repo's `change` commit."""
    sha = repo["sha"]["change"]
    out = {
        "verdict": "regression",
        "metric": None,
        "confidence": "medium",
        "culprit": (
            {"commit": sha, "files": ["app/Feed.kt"], "attribution": "correlated"}
            if culprit
            else None
        ),
        "claims": [
            {
                "text": "The change commit edits app/Feed.kt.",
                "citations": [{"kind": "commit", "sha": sha, "path": "app/Feed.kt"}],
            }
        ],
        "caveats": ["one capture per side"],
    }
    return {**out, **overrides}


@pytest.fixture
def run(repo, tiny_trace):
    """diagnose() on the tiny trace (as both sides) and the small repo, with `script`
    as the model. Returns (diagnosis, fake)."""

    def go(script, **kwargs):
        fake = FakeModel(script)
        args = {
            "baseline": tiny_trace,
            "current": tiny_trace,
            "repo": repo["path"],
            "git_range": repo["range"],
            "client": fake.client,
            "binary": NO_BINARY,
            "cache_dir": None,
        }
        return diagnose(**{**args, **kwargs}), fake

    return go


# --- The loop: a normal answer, a refusal, a cut-off answer ---------------------------


def test_a_normal_end_turn_yields_a_verified_diagnosis(run, repo):
    """The control: one tool call, then an answer, which the verifier keeps."""

    def script(request, turn):
        if turn == 1:
            return reply(
                tool_use("get_git_log", {"range": repo["range"], "paths": None}),
                stop_reason="tool_use",
            )
        return reply(text(answer(repo)))

    diagnosis, fake = run(script)
    check_diagnosis(diagnosis)
    assert diagnosis["verdict"] == "regression"
    assert diagnosis["culprit"]["commit"] == repo["sha"]["change"]
    assert [c["id"] for c in diagnosis["claims"]] == ["c1"]
    assert diagnosis["dropped_claims"] == []
    assert diagnosis["confidence"] == "medium"
    # The tool really ran: its result went back to the model.
    [result] = fake.tool_results(2).values()
    assert not result["is_error"]
    assert result["content"]["commit_count"] == 2
    run_block = diagnosis["run"]
    assert run_block["tool_calls"] == 1
    assert run_block["usage"] == {k: 2 * v for k, v in USAGE.items()}
    assert run_block["usd"] == usd(MODEL, run_block["usage"]) > 0
    assert run_block["wall_time_s"] >= 0


def test_a_refusal_is_inconclusive_with_its_category_and_not_retried(run):
    def script(request, turn):
        return reply(
            stop_reason="refusal",
            stop_details={"type": "refusal", "category": "cyber", "explanation": "x"},
        )

    diagnosis, fake = run(script)
    assert len(fake.requests) == 1
    check_diagnosis(diagnosis)
    assert diagnosis["verdict"] == "inconclusive"
    assert diagnosis["claims"] == diagnosis["dropped_claims"] == []
    assert any("refusal: cyber" in c for c in diagnosis["caveats"])
    # The verifier still ran, and the run's cost is recorded.
    assert diagnosis["verification"]["explanation"] == "the model made no claims"
    assert diagnosis["run"]["usage"]["input_tokens"] == USAGE["input_tokens"]


def test_a_refusal_without_a_category_says_so(run):
    diagnosis, _ = run(lambda request, turn: reply(stop_reason="refusal"))
    assert any("refusal: unspecified" in c for c in diagnosis["caveats"])


def test_max_tokens_is_inconclusive_and_the_cut_off_text_is_never_read(run, repo):
    # Half an answer that would pass if it were read: it must not be.
    half = json.dumps(answer(repo))[:80]
    diagnosis, fake = run(lambda r, t: reply(text(half), stop_reason="max_tokens"))
    assert len(fake.requests) == 1
    assert diagnosis["verdict"] == "inconclusive"
    assert diagnosis["culprit"] is None
    assert any(f"max_tokens ({MAX_TOKENS})" in c for c in diagnosis["caveats"])


# --- Output validation ----------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param("the change commit did it", id="not-json"),
        pytest.param({"verdict": "regression"}, id="missing-fields"),
        pytest.param("pre-filled", id="code-filled-field"),
        pytest.param("bad-verdict", id="bad-enum"),
    ],
)
def test_an_invalid_answer_is_rejected(run, repo, bad):
    if bad == "pre-filled":
        bad = {**answer(repo), "dropped_claims": []}
    elif bad == "bad-verdict":
        bad = answer(repo, verdict="probably")
    with pytest.raises(DiagnosisInvalid):
        run(lambda request, turn: reply(text(bad)))


# --- What the model is sent -----------------------------------------------------------


def test_the_request_follows_the_tech_stack(run, repo, tiny_trace):
    _, fake = run(lambda request, turn: reply(text(answer(repo))))
    [request] = fake.requests
    assert request["model"] == MODEL == "claude-opus-5-5"
    assert request["max_tokens"] == MAX_TOKENS == 64000
    assert request["stream"] is True
    assert request["thinking"] == {"type": "adaptive"}
    assert request["output_config"] == {
        "effort": EFFORT,
        "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
    }
    assert EFFORT == "high"
    # No forced tool choice, no prefill: the one message is the user's.
    assert "tool_choice" not in request
    assert [m["role"] for m in request["messages"]] == ["user"]
    [system] = request["system"]
    assert system == {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }
    # Every tool, with its hand-written schema unchanged, strict.
    expected = {t.name: t.definition() for t in (*TRACE_TOOLS, *REPO_TOOLS)}
    assert {t["name"]: t for t in request["tools"]} == expected


def test_the_model_is_shown_no_path(run, repo, tiny_trace):
    _, fake = run(lambda request, turn: reply(text(answer(repo))))
    sent = json.dumps(fake.requests[0])
    for path in (tiny_trace, repo["path"]):
        assert str(path) not in sent
        assert path.name not in sent
    assert repo["range"] in fake.requests[0]["messages"][0]["content"]


def test_the_range_is_shown_as_shas_never_as_names(run, repo):
    """A branch name can say what a range holds (`main..fix-slow-feed`)."""
    base, head = repo["sha"]["base"], repo["sha"]["head"]
    _, fake = run(
        lambda request, turn: reply(text(answer(repo))), git_range=f"{base}..main"
    )
    first = fake.requests[0]["messages"][0]["content"]
    assert f"`{base}..{head}`" in first
    assert "main" not in first


def test_the_prompts_hint_at_nothing(repo):
    """Neither prompt says what the traces hold. The system prompt may use the output
    schema's own field and value names (every run sees the schema); nothing else."""
    schema_words = set(re.findall(r"[a-z_]+", json.dumps(OUTPUT_SCHEMA)))
    words = re.findall(r"[A-Za-z_]+", SYSTEM_PROMPT)
    assert hints_in(" ".join(w for w in words if w not in schema_words), []) == []
    for metric in ("auto", "startup_ttid_ms"):
        assert hints_in(first_message(repo["range"], metric), []) == []


def test_a_named_metric_is_passed_on_and_measured(run, repo, trace_processor):
    """The model answered with no metric; the one the user named is measured anyway,
    since a measured number with no cause is still worth reporting (ADR-0006)."""
    diagnosis, fake = run(
        lambda request, turn: reply(text(answer(repo))),
        metric="startup_ttid_ms",
        binary=trace_processor,
    )
    assert "startup_ttid_ms" in fake.requests[0]["messages"][0]["content"]
    assert diagnosis["metric"]["name"] == "startup_ttid_ms"
    assert diagnosis["verification"]["metric_dropped"] is None


def test_a_metric_the_library_lacks_is_dropped_with_a_caveat(run, repo):
    made_up = {
        "name": "made_up_ms",
        "unit": "ms",
        "baseline": 1,
        "current": 2,
        "delta": 1,
        "sql_used": "SELECT 1 AS value",
    }
    diagnosis, _ = run(lambda r, t: reply(text(answer(repo, metric=made_up))))
    assert diagnosis["metric"] is None
    assert any("made_up_ms" in c for c in diagnosis["caveats"])


# --- Refused before any request -------------------------------------------------------


def _no_model(request, turn):
    raise AssertionError("no request should be made")


def test_a_bad_range_is_refused_before_any_request(run):
    with pytest.raises(RangeError):
        run(_no_model, git_range="main")


def test_an_unknown_metric_is_refused_before_any_request(run):
    with pytest.raises(UnknownMetric):
        run(_no_model, metric="no_such_metric")


def test_a_missing_trace_is_refused_before_any_request(run, tmp_path):
    with pytest.raises(FileNotFoundError):
        run(_no_model, current=tmp_path / "absent.perfetto-trace")


def test_a_model_with_no_price_is_refused_before_any_request(run):
    """ADR-0020: every run records its cost, so a model with no price row cannot run."""
    with pytest.raises(UnpricedModel, match="claude-opus-5-5"):
        run(_no_model, model="claude-opus-5")


# --- The tools, as the model calls them -----------------------------------------------


@pytest.mark.parametrize("tool", TRACE_TOOLS, ids=lambda t: t.name)
def test_each_trace_tool_schema_is_strict(tool):
    definition = tool.definition()
    assert definition["strict"] is True
    schema = definition["input_schema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == list(schema["properties"])
    code = tool.function.__code__
    assert list(schema["properties"]) == list(code.co_varnames[1 : code.co_argcount])


@pytest.mark.parametrize("tool", TRACE_TOOLS, ids=lambda t: t.name)
def test_each_trace_tool_says_what_it_cannot_tell(tool):
    assert "cannot" in tool.description
    for word in HINT_WORDS:
        assert word not in tool.description.lower()


def test_bad_arguments_come_back_as_error_results(run, repo):
    """Each is the model's mistake, answered as an error it can read, and the run
    goes on to an answer."""
    calls = [
        tool_use("get_git_log", {"range": 5, "paths": None}, id="t1"),  # schema
        tool_use(
            "get_git_diff", {"sha": "f" * 40, "path": None, "max_lines": None}, id="t2"
        ),  # no such commit
        tool_use(
            "query_trace", {"sql": "DELETE FROM slice", "which": "current"}, id="t3"
        ),  # not a SELECT
        tool_use("compute_metric", {"name": "no_such_metric"}, id="t4"),
        tool_use("query_trace", {"sql": "SELECT 1", "which": "neither"}, id="t5"),
    ]

    def script(request, turn):
        if turn == 1:
            return reply(*calls, stop_reason="tool_use")
        return reply(text(answer(repo)))

    diagnosis, fake = run(script)
    results = fake.tool_results(2)
    assert set(results) == {"t1", "t2", "t3", "t4", "t5"}
    assert all(r["is_error"] for r in results.values())
    assert "input.range: expected string" in results["t1"]["content"]
    assert "names no commit" in results["t2"]["content"]
    assert "only SELECT" in results["t3"]["content"]
    assert "no metric named 'no_such_metric'" in results["t4"]["content"]
    assert "input.which: expected one of" in results["t5"]["content"]
    assert diagnosis["verdict"] == "regression"
    assert diagnosis["run"]["tool_calls"] == 5


def test_a_failure_of_the_run_stops_it(run, repo, monkeypatch):
    """git that cannot run is not the model's mistake: raised, no further request."""

    def unavailable(*args, **kwargs):
        raise GitUnavailable("git timed out")

    monkeypatch.setattr(repo_tools, "run_git", unavailable)

    def script(request, turn):
        return reply(
            tool_use("get_git_log", {"range": repo["range"], "paths": None}),
            stop_reason="tool_use",
        )

    fake_requests = []
    with pytest.raises(RunFailed, match="git timed out") as e:
        run(lambda r, t: fake_requests.append(r) or script(r, t))
    assert isinstance(e.value.__cause__, GitUnavailable)
    assert len(fake_requests) == 1


def test_usd_prices_each_kind_of_token():
    usage = {
        "input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
        "cache_read_input_tokens": 1_000_000,
        "cache_creation_input_tokens": 1_000_000,
    }
    assert usd(MODEL, usage) == 4.00 + 20.00 + 0.20 + 5.00


# --- End to end, offline: a scripted model on a real case -----------------------------

# A case whose expected metric is keyed, so an answer can cite a breakdown row. Its
# traces are left out of a default LFS fetch (ADR-0015); fetch them with
#   git lfs pull --include="evals/cases/462439ff/**" --exclude=""
CASE = "462439ff"


@pytest.fixture(scope="module")
def staged_case(tmp_path_factory):
    inputs = load_inputs(CASE)
    for trace in (inputs.baseline, inputs.current):
        with trace.open("rb") as f:
            if f.read(len(LFS_POINTER)) == LFS_POINTER:
                pytest.skip(
                    f"{trace.relative_to(EVALS_DIR.parent)} is an LFS pointer; fetch: "
                    f'git lfs pull --include="evals/cases/{CASE}/**" --exclude=""'
                )
    return inputs.stage(tmp_path_factory.mktemp("staged") / "run")


def test_offline_end_to_end_on_a_real_case(staged_case, trace_processor, tmp_path):
    """The closest offline stand-in for a live run: a scripted model calls the real
    tools on the staged case, and answers with claims citing the SQL they returned
    and a commit in the range. Every claim survives the verifier, and the metric in
    the file is the measured one, not the model's copy."""
    case = staged_case
    git_range = f"{case.range_base}..{case.range_head}"
    # What a model would have to find; the script knows it, the prompt never does.
    expected = load_expected(CASE)
    [metric_name] = expected.metrics

    def script(request, turn):
        if turn == 1:
            return reply(
                tool_use("list_metrics", {}, id="lm"),
                tool_use("get_git_log", {"range": git_range, "paths": None}, id="log"),
                stop_reason="tool_use",
            )
        if turn == 2:
            return reply(
                tool_use("compute_metric", {"name": metric_name}, id="m"),
                stop_reason="tool_use",
            )
        if turn == 3:
            return reply(
                tool_use(
                    "get_git_diff",
                    {"sha": expected.culprit, "path": None, "max_lines": None},
                    id="diff",
                ),
                stop_reason="tool_use",
            )
        return reply(text(scripted_answer()))

    def scripted_answer() -> dict:
        results = {
            **fake.tool_results(2),
            **fake.tool_results(3),
            **fake.tool_results(4),
        }
        metric = results["m"]["content"]
        top = metric["breakdown"]["rows"][0]
        diff = results["diff"]["content"]["diff"]
        changed = re.findall(r"^\+\+\+ b/(\S+)", diff, re.M)
        assert changed, "the diff names no file"
        sha = expected.culprit
        return {
            "verdict": "regression",
            # Numbers the model got wrong: the file must carry the measured ones.
            "metric": {
                **{k: metric[k] for k in ("name", "unit", "sql_used")},
                "baseline": 0,
                "current": 1,
                "delta": 1,
            },
            "confidence": "high",
            "culprit": {"commit": sha, "files": changed, "attribution": "direct"},
            "claims": [
                {
                    "text": "The metric grew.",
                    "citations": [
                        {
                            "kind": "trace",
                            "trace": "current",
                            "sql": metric["sql_used"],
                        },
                        {
                            "kind": "trace",
                            "trace": "baseline",
                            "sql": metric["sql_used"],
                        },
                    ],
                },
                {
                    "text": f"{top['key']} grew most.",
                    "citations": [
                        {"kind": "trace", "trace": "current", "sql": top["sql_used"]},
                    ],
                },
                {
                    "text": "The commit changed that code.",
                    "citations": [
                        {"kind": "commit", "sha": sha[:12], "path": changed[0]},
                    ],
                },
            ],
            "caveats": ["emulator capture"],
        }

    fake = FakeModel(script)
    diagnosis = diagnose(
        baseline=case.baseline,
        current=case.current,
        repo=case.repo,
        git_range=git_range,
        client=fake.client,
        binary=trace_processor,
        cache_dir=tmp_path / "cache",
    )
    # The tools answered for real, with no errors.
    log = fake.tool_results(2)["log"]
    assert not log["is_error"]
    assert expected.culprit in [c["sha"] for c in log["content"]["commits"]]
    assert not any(
        r["is_error"] for t in (2, 3, 4) for r in fake.tool_results(t).values()
    )

    check_diagnosis(diagnosis)
    assert diagnosis["verdict"] == "regression"
    assert diagnosis["dropped_claims"] == []
    assert len(diagnosis["claims"]) == 3
    assert diagnosis["culprit"]["commit"] == expected.culprit
    assert diagnosis["confidence"] == "high"
    # The tool's own compute_metric result, which the script misquoted.
    measured = fake.tool_results(3)["m"]["content"]
    assert diagnosis["metric"] == {
        k: measured[k]
        for k in ("name", "unit", "baseline", "current", "delta", "sql_used")
    }
    assert diagnosis["metric"]["delta"] > 0
    assert diagnosis["run"]["tool_calls"] == 4
    # Nothing the model was sent names the case, the eval tree or the plant.
    sent = json.dumps(fake.requests)
    assert CASE not in sent
    assert "evals/" not in sent
    for path in (case.repo, case.baseline, case.current):
        assert str(path) not in sent
