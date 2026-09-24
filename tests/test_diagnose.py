"""`diagnose`: the agent loops, their tools, and what they write (roadmap item 7, #29,
#43).

The model is `fake_model.FakeModel` (Anthropic) or `fake_openai.FakeOpenAI` (OpenAI):
each SDK's real client and streaming parser over an in-process transport, answering
from a script. Both play the same scripts, so a test of what `diagnose` does with an
answer, a refusal or a tool error runs once per provider (`provider`). No test opens a
socket.
"""

import json
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import LFS_POINTER
from fake_model import USAGE, FakeModel, reply, text, tool_use
from fake_openai import ENCRYPTED, FakeOpenAI
from test_eval_cases import HINT_WORDS, hints_in

from perfettoagent import repo_tools
from perfettoagent.agent import SYSTEM_PROMPT, diagnose, first_message
from perfettoagent.diagnosis import OUTPUT_SCHEMA, DiagnosisInvalid, check_diagnosis
from perfettoagent.evalcases import EVALS_DIR, load_expected, load_inputs
from perfettoagent.git import GitUnavailable
from perfettoagent.loop import MAX_TOKENS, RunFailed
from perfettoagent.metrics import UnknownMetric
from perfettoagent.models import (
    DEFAULT_EFFORT,
    DEFAULT_MODELS,
    DEFAULT_PROVIDER,
    ModelRefused,
    UnpricedModel,
    usd,
)
from perfettoagent.openai_loop import usage_of
from perfettoagent.repo_tools import REPO_TOOLS
from perfettoagent.run_metadata import (
    CAVEAT_DEBUGGABLE,
    CAVEAT_DIRTY,
    RunMetadataInvalid,
)
from perfettoagent.run_metadata import load as load_run_metadata
from perfettoagent.trace_tools import TRACE_TOOLS
from perfettoagent.verify import RangeError

# A trace processor that is never reached: these tests' citations are commits only,
# and `diagnose` resolves the binary only when none is given.
NO_BINARY = Path("/nonexistent/trace_processor_shell")

# Each provider's scripted stand-in.
FAKES = {"anthropic": FakeModel, "openai": FakeOpenAI}


@pytest.fixture(params=list(FAKES))
def provider(request) -> str:
    """Every test that runs `diagnose` runs once per provider, unless it parametrizes
    `provider` itself."""
    return request.param


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
def run(repo, tiny_trace, provider):
    """diagnose() on the tiny trace (as both sides) and the small repo, with `script`
    as `provider`'s model. Returns (diagnosis, fake)."""

    def go(script, **kwargs):
        fake = FAKES[provider](script)
        args = {
            "provider": provider,
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


def test_a_normal_end_turn_yields_a_verified_diagnosis(run, repo, provider):
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
    model = DEFAULT_MODELS[provider]
    assert (run_block["provider"], run_block["model"], run_block["effort"]) == (
        provider,
        model,
        DEFAULT_EFFORT,
    )
    assert run_block["tool_calls"] == 1
    # The same usage in both providers' own terms, recorded in one shape.
    assert run_block["usage"] == {k: 2 * v for k, v in USAGE.items()}
    assert run_block["usd"] == round(2 * usd(model, USAGE), 6) > 0
    assert run_block["wall_time_s"] >= 0


# What a refusal's caveat names: Anthropic gives a category, OpenAI only its text
# (ADR-0020).
REFUSAL_REASON = {"anthropic": "refusal: cyber", "openai": "refusal: I can't help."}


def test_a_refusal_is_inconclusive_with_its_category_and_not_retried(run, provider):
    def script(request, turn):
        return reply(
            stop_reason="refusal",
            stop_details={
                "type": "refusal",
                "category": "cyber",
                "explanation": "I can't   help.",
            },
        )

    diagnosis, fake = run(script)
    assert len(fake.requests) == 1
    check_diagnosis(diagnosis)
    assert diagnosis["verdict"] == "inconclusive"
    assert diagnosis["claims"] == diagnosis["dropped_claims"] == []
    assert any(REFUSAL_REASON[provider] in c for c in diagnosis["caveats"])
    # The verifier still ran, and the run's cost is recorded.
    assert diagnosis["verification"]["explanation"] == "the model made no claims"
    assert diagnosis["run"]["usage"]["input_tokens"] == USAGE["input_tokens"]


def test_a_refusal_without_a_reason_says_so(run, provider):
    diagnosis, _ = run(lambda request, turn: reply(stop_reason="refusal"))
    reason = {"anthropic": "unspecified", "openai": "no reason given"}[provider]
    assert any(f"refusal: {reason}" in c for c in diagnosis["caveats"])


def test_max_tokens_is_inconclusive_and_the_cut_off_text_is_never_read(
    run, repo, provider
):
    # Half an answer that would pass if it were read: it must not be.
    half = json.dumps(answer(repo))[:80]
    diagnosis, fake = run(lambda r, t: reply(text(half), stop_reason="max_tokens"))
    assert len(fake.requests) == 1
    assert diagnosis["verdict"] == "inconclusive"
    assert diagnosis["culprit"] is None
    assert any(
        f"cut off at max_{'output_' * (provider == 'openai')}tokens ({MAX_TOKENS})" in c
        for c in diagnosis["caveats"]
    )


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


@pytest.mark.parametrize("provider", ["anthropic"])
def test_the_anthropic_request_follows_the_tech_stack(run, repo):
    _, fake = run(lambda request, turn: reply(text(answer(repo))))
    [request] = fake.requests
    assert request["model"] == DEFAULT_MODELS["anthropic"] == "claude-opus-5-5"
    assert request["max_tokens"] == MAX_TOKENS == 64000
    assert request["stream"] is True
    assert request["thinking"] == {"type": "adaptive"}
    assert request["output_config"] == {
        "effort": DEFAULT_EFFORT,
        "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
    }
    assert DEFAULT_EFFORT == "high"
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


@pytest.mark.parametrize("provider", ["openai"])
def test_the_openai_request_follows_the_tech_stack(run, repo):
    """ADR-0020's table: the Responses API, streamed, strict tools and structured
    output, effort sent, no state kept on OpenAI's servers, tool choice `auto`."""
    _, fake = run(lambda request, turn: reply(text(answer(repo))))
    [request] = fake.requests
    assert request["model"] == DEFAULT_MODELS["openai"] == "gpt-5.6-luna"
    assert request["stream"] is True
    assert request["max_output_tokens"] == MAX_TOKENS == 64000
    assert request["reasoning"] == {"effort": DEFAULT_EFFORT}
    assert request["store"] is False
    assert "previous_response_id" not in request
    assert request["include"] == ["reasoning.encrypted_content"]
    assert request["tool_choice"] == "auto"
    assert request["text"] == {
        "format": {
            "type": "json_schema",
            "name": "diagnosis",
            "schema": OUTPUT_SCHEMA,
            "strict": True,
        }
    }
    # The frozen prompt first, as a developer item; the volatile inputs after it.
    assert request["input"][0] == {"role": "developer", "content": SYSTEM_PROMPT}
    assert [i["role"] for i in request["input"]] == ["developer", "user"]
    # Every tool, with its hand-written schema unchanged, strict.
    expected = {
        t.name: {
            "type": "function",
            "name": t.name,
            "description": t.description,
            "parameters": t.input_schema,
            "strict": True,
        }
        for t in (*TRACE_TOOLS, *REPO_TOOLS)
    }
    assert {t["name"]: t for t in request["tools"]} == expected


@pytest.mark.parametrize("provider", ["openai"])
def test_the_openai_history_is_replayed_with_its_reasoning(run, repo):
    """With no server state, each request resends the whole history: every output
    item, reasoning included with its encrypted content, then the tool outputs. The
    prefix (prompt, tools, format) is the same bytes each time, so it can be cached."""

    def script(request, turn):
        if turn == 1:
            return reply(
                tool_use("get_git_log", {"range": repo["range"], "paths": None}),
                stop_reason="tool_use",
            )
        return reply(text(answer(repo)))

    _, fake = run(script)
    first, second = fake.requests
    assert second["input"][: len(first["input"])] == first["input"]
    reasoning, call, output = second["input"][len(first["input"]) :]
    assert reasoning["type"] == "reasoning"
    assert reasoning["encrypted_content"] == ENCRYPTED
    assert call["type"] == "function_call"
    assert call["call_id"] == output["call_id"] == "toolu_get_git_log"
    assert output["type"] == "function_call_output"
    for key in ("tools", "text", "reasoning"):
        assert json.dumps(first[key]) == json.dumps(second[key])


@pytest.mark.parametrize("provider", ["openai"])
def test_openai_calls_the_loop_must_answer_itself(run, repo):
    """No SDK runner checks these on OpenAI: arguments that are not JSON, or not an
    object, and a tool that does not exist come back as errors, and the run goes on."""
    calls = [
        tool_use("get_git_log", '{"range": ', id="c1"),
        tool_use("get_git_log", "[1, 2]", id="c2"),
        tool_use("no_such_tool", {}, id="c3"),
    ]

    def script(request, turn):
        if turn == 1:
            return reply(*calls, stop_reason="tool_use")
        return reply(text(answer(repo)))

    diagnosis, fake = run(script)
    results = fake.tool_results(2)
    assert all(r["is_error"] for r in results.values())
    assert "arguments not JSON" in results["c1"]["content"]
    assert "not a JSON object" in results["c2"]["content"]
    assert "no tool named 'no_such_tool'" in results["c3"]["content"]
    assert diagnosis["verdict"] == "regression"


@pytest.mark.parametrize("provider", ["openai"])
def test_an_openai_response_incomplete_for_another_reason_is_inconclusive(run, repo):
    diagnosis, fake = run(
        lambda r, t: reply(text(answer(repo)), incomplete="content_filter")
    )
    assert len(fake.requests) == 1
    assert diagnosis["verdict"] == "inconclusive"
    assert any("incomplete (content_filter)" in c for c in diagnosis["caveats"])


@pytest.mark.parametrize("provider", ["openai"])
def test_an_openai_response_that_failed_fails_the_run(run):
    """The provider's own failure is not an answer, and not the model's to correct."""
    failed = {"code": "server_error", "message": "try again"}
    with pytest.raises(RunFailed, match="failed.*server_error"):
        run(lambda r, t: reply(failed=failed))


def test_the_model_is_shown_no_path(run, repo, tiny_trace):
    _, fake = run(lambda request, turn: reply(text(answer(repo))))
    sent = json.dumps(fake.requests[0])
    for path in (tiny_trace, repo["path"]):
        assert str(path) not in sent
        assert path.name not in sent
    assert repo["range"] in fake.first_message()


def test_the_range_is_shown_as_shas_never_as_names(run, repo):
    """A branch name can say what a range holds (`main..fix-slow-feed`)."""
    base, head = repo["sha"]["base"], repo["sha"]["head"]
    _, fake = run(
        lambda request, turn: reply(text(answer(repo))), git_range=f"{base}..main"
    )
    first = fake.first_message()
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
    assert "startup_ttid_ms" in fake.first_message()
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


def _metadata(commit: str, **overrides) -> dict:
    return {
        "schema": 1,
        "commit": commit,
        "tree_dirty": False,
        "debuggable": False,
        "build_type": None,
        "device": None,
        **overrides,
    }


def test_run_metadata_outside_the_range_is_refused_before_any_request(run, repo):
    with pytest.raises(RunMetadataInvalid, match="not inside the range"):
        run(_no_model, metadata=_metadata(repo["sha"]["base"]))


def test_read_run_metadata_is_offered_only_with_run_metadata(run, repo):
    def names(fake):
        return {t["name"] for t in fake.requests[0]["tools"]}

    _, without = run(lambda request, turn: reply(text(answer(repo))))
    assert "read_run_metadata" not in names(without)

    given = _metadata(repo["sha"]["head"], build_type="release")

    def script(request, turn):
        if turn == 1:
            return reply(tool_use("read_run_metadata", {}), stop_reason="tool_use")
        return reply(text(answer(repo)))

    diagnosis, fake = run(script, metadata=given)
    assert "read_run_metadata" in names(fake)
    [result] = fake.tool_results(2).values()
    assert result["content"] == given
    assert diagnosis["caveats"] == ["one capture per side"]


def test_a_dirty_or_debuggable_build_is_a_caveat_the_model_cannot_omit(run, repo):
    given = _metadata(repo["sha"]["head"], tree_dirty=True, debuggable=True)
    diagnosis, _ = run(lambda request, turn: reply(text(answer(repo))), metadata=given)
    assert diagnosis["caveats"] == [
        CAVEAT_DIRTY,
        CAVEAT_DEBUGGABLE,
        "one capture per side",
    ]


def test_a_model_with_no_price_is_refused_before_any_request(run, provider):
    """ADR-0020: every run records its cost, so a model with no price row cannot run.
    The error names the priced models on that provider."""
    with pytest.raises(UnpricedModel, match=DEFAULT_MODELS[provider]):
        run(_no_model, model="some-other-model")


def test_a_model_on_the_wrong_provider_is_refused_before_any_request(run, provider):
    other = next(m for p, m in DEFAULT_MODELS.items() if p != provider)
    with pytest.raises(ModelRefused, match=f"not {provider}"):
        run(_no_model, model=other)


def test_an_effort_the_model_lacks_is_refused_before_any_request(run):
    """Never rounded to a nearby level: a cost row means the level it names."""
    with pytest.raises(ModelRefused, match="no effort 'max'; it has low, medium"):
        run(_no_model, effort="max")


def test_the_default_is_openai_gpt_5_6_luna():
    """ADR-0020: the default flips to OpenAI when its path ships (#43)."""
    assert DEFAULT_PROVIDER == "openai"
    assert DEFAULT_MODELS[DEFAULT_PROVIDER] == "gpt-5.6-luna"


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
    assert usd("claude-opus-5-5", usage) == pytest.approx(4.00 + 20.00 + 0.20 + 5.00)
    # 3M input tokens is above gpt-5.6-luna's 272K line: the long-context prices.
    assert usd("gpt-5.6-luna", usage) == pytest.approx(0.40 + 1.80 + 0.04 + 0.50)


def test_openai_usage_splits_a_recorded_response_s_input():
    """A real `gpt-5.6-luna` response's usage (ADR-0023): 3,879 input tokens, of which
    3,863 read from the cache and 13 written to it. What is left is uncached."""
    recorded = SimpleNamespace(
        input_tokens=3879,
        input_tokens_details=SimpleNamespace(cached_tokens=3863, cache_write_tokens=13),
        output_tokens=5,
    )
    assert usage_of(recorded) == {
        "input_tokens": 3,
        "output_tokens": 5,
        "cache_read_input_tokens": 3863,
        "cache_creation_input_tokens": 13,
    }


def test_gpt_5_6_luna_s_long_context_price_is_per_request_by_whole_input():
    """The line is the request's whole input, cached or not; under it, the standard
    prices."""
    under = {
        "input_tokens": 100_000,
        "output_tokens": 0,
        "cache_read_input_tokens": 172_000,
        "cache_creation_input_tokens": 0,
    }
    over = {**under, "cache_read_input_tokens": 172_001}
    assert usd("gpt-5.6-luna", under) == pytest.approx(0.02 + 172_000 * 0.02 / 1e6)
    assert usd("gpt-5.6-luna", over) == pytest.approx(0.04 + 172_001 * 0.04 / 1e6)


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


def test_offline_end_to_end_on_a_real_case(
    staged_case, trace_processor, tmp_path, provider
):
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

    fake = FAKES[provider](script)
    diagnosis = diagnose(
        provider=provider,
        baseline=case.baseline,
        current=case.current,
        repo=case.repo,
        git_range=git_range,
        client=fake.client,
        binary=trace_processor,
        cache_dir=tmp_path / "cache",
        # As the eval runner passes it: the case's sanitised run metadata.
        metadata=load_run_metadata(case.run_metadata),
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
    # A benchmark build from the range's head, clean: nothing to caveat.
    assert diagnosis["caveats"] == ["emulator capture"]
    # Nothing the model was sent names the case, the eval tree or the plant.
    sent = json.dumps(fake.requests)
    assert CASE not in sent
    assert "evals/" not in sent
    for path in (case.repo, case.baseline, case.current):
        assert str(path) not in sent
