"""`diagnose`: two traces and a git range in, a verified `diagnosis.json` out (roadmap
item 7, issue #29).

The loop is the Anthropic SDK's beta Tool Runner, streamed (docs/tech-stack.md "Model
and SDK"). Each tool is a `perfettoagent.tools.Tool` handed to `beta_tool` with its
hand-written strict schema unchanged, and every call goes through `Tool.call`, which
checks the arguments against that schema (ADR-0018). An error the model can correct
(a bad argument, SQL that does not run, a commit that is not there) comes back to it as
an error tool_result. Anything else (git cannot run, the trace processor vanished) is
a failure of the run and is raised, never shown to the model as its own mistake.

What the model answers is structured output, `output_config.format` =
`diagnosis.OUTPUT_SCHEMA`, checked again here with `check_output`, and then always run
through `verify`: no claim reaches the file without its citations being re-run
(CLAUDE.md). Before the verifier, the metric the model names is re-measured with
`compute_metric`, so its numbers and `sql_used` are ours, not the model's copy of them
(ADR-0006).

A run that ends without an answer (the model refused, or ran out of tokens or turns)
is still a diagnosis: `inconclusive`, with no claims and the reason as a caveat, so its
cost is recorded like any other run's. A refusal is never retried.

Eval integrity (CLAUDE.md): the model is shown the range and the metric choice, never
a path. The trace tools name a trace by its side, and the git tools read the repo the
run binds, so nothing it sees says where either came from.

ref: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
ref: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
ref: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
"""

import json
import time
from pathlib import Path
from typing import Any

import anthropic
from anthropic import beta_tool
from anthropic.lib.tools import ToolError

from perfettoagent.diagnosis import (
    METRIC_FIELDS,
    OUTPUT_SCHEMA,
    DiagnosisInvalid,
    check_output,
)
from perfettoagent.git import GitError
from perfettoagent.metrics import MetricError, UnknownMetric, compute_metric
from perfettoagent.metrics import list_metrics as metric_library
from perfettoagent.query import QueryRejected
from perfettoagent.repo_tools import REPO_TOOLS
from perfettoagent.symbolize import TraceContext
from perfettoagent.tools import Tool, ToolInputError
from perfettoagent.trace_processor import TraceProcessorError, resolve_trace_processor
from perfettoagent.trace_tools import TRACE_TOOLS
from perfettoagent.verify import QUERY_CACHE_DIR, check_range, verify

# docs/tech-stack.md and ADR-0001: no date suffix. A constant, so a later switch
# (#43) is a parameter, not an edit.
MODEL = "claude-opus-5-5"

# docs/tech-stack.md: `high` by default. Opus 5.5's own default is `medium` (ADR-0020,
# "The effort mapping"), so it is always sent explicitly.
EFFORT = "high"

# docs/tech-stack.md: the agent loop's per-response ceiling. Streamed, so the SDK's
# HTTP timeout does not apply to a long response.
MAX_TOKENS = 64000

# Model turns before the run stops as inconclusive. A diagnosis takes a few dozen tool
# calls; a loop past this is not converging, and each turn resends the context.
MAX_TURNS = 60

# `--metric auto`: the model picks from list_metrics (roadmap Q3).
AUTO = "auto"

# USD per million tokens, standard tier, for the run's `usd`, keyed by model id. A model
# with no row is refused before any request (ADR-0020), so every run has a cost. Claude
# Opus 5.5: as Anthropic's pricing page gave it on 2026-09-24 (ADR-0020 "Prices"). The
# cache write is the 5-minute one, the only TTL used; thinking is billed as output.
# ref: https://platform.claude.com/docs/en/about-claude/pricing
PRICES_USD_PER_MTOK = {
    "claude-opus-5-5": {
        "input_tokens": 4.00,
        "output_tokens": 20.00,
        "cache_read_input_tokens": 0.20,
        "cache_creation_input_tokens": 5.00,
    },
}

# The usage fields `run.usage` records (ADR-0006), each summed over the run's requests.
USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)

# What a tool raises when the model's call was at fault: it gets the message back as an
# error tool_result, to correct. A TraceProcessorError counts, because the binary is
# resolved and both traces are checked before the loop, so one raised inside it is the
# SQL's own doing (a syntax error, an unknown table, a timeout). GitUnavailable is not
# a GitError on purpose, and raises (perfettoagent.git).
MODEL_ERRORS = (
    ToolInputError,
    GitError,
    QueryRejected,
    MetricError,
    TraceProcessorError,
)

# An error message is for the model to act on; a trace processor traceback's end names
# what went wrong, and the rest is context the model pays for.
MAX_ERROR_CHARS = 2000

# Frozen: any change to these bytes misses the prompt cache (docs/tech-stack.md). It
# names no case, path or trace; the output schema's own field and value names are the
# only vocabulary it shares with what is being looked for, and every run sees those.
SYSTEM_PROMPT = """\
You diagnose a performance change in an Android app between two Perfetto traces, a \
baseline capture and a current capture of the same scenario, and attribute it to a \
commit in a git range of the app's repository. You answer with a JSON object in the \
given schema.

Work in this order:

1. Establish the metric delta. Call list_metrics, choose the metric that describes the \
change (or use the one the user message names), and call compute_metric. A single \
capture per side is noisy: a small delta may be noise, and saying so is an answer.
2. Localise it in the trace: the process, thread, slice, span, class or frame the \
difference comes from. Compare both traces with query_trace. Use a metric's breakdown, \
and symbolize for callstack frames.
3. Correlate it with the range. get_git_log lists the commits, get_git_diff shows what \
one changed, and grep_repo finds the code that names what you localised: a thread \
name, a slice name, a class or a method.
4. Blame. git_blame the lines the evidence points at, at the range's head, to confirm \
which commit introduced them.

The tools see only the two traces and the repository. The repository is read at \
commits, never a working tree, and nothing you do changes it.

Every claim must cite what backs it. A checker re-runs every citation before anyone \
reads the answer, and removes each claim that has a citation that fails; if no claim \
survives, the verdict becomes inconclusive.
- A trace citation names its trace (baseline or current) and SQL: a query you ran with \
query_trace, or a sql_used a tool returned, copied verbatim. It must return at least \
one row on that trace.
- A commit citation is a sha inside the range, and optionally a path that commit \
changed.
- Say "likely" only inside a claim that cites what makes it likely. Do not speculate, \
and do not state a number no citation returns.

The fields:
- verdict: whether the metric got worse from baseline to current and the range \
explains it; inconclusive when the evidence cannot say.
- metric: the metric you judged by, as compute_metric returned it. It is re-measured \
from its name, so name a metric from list_metrics.
- confidence: low, medium or high.
- culprit: the commit the change is attributed to, and the files that matter, or null. \
attribution is direct when a trace row points into code the commit changed, and \
correlated when the commit is only the likeliest in the range. Some claim must cite \
the commit, or it is dropped.
- claims: short statements of fact, each with its citations.
- caveats: what limits the answer, such as an emulator capture, a single capture per \
side, or a debuggable build.
"""


class UnpricedModel(ValueError):
    """The model has no row in PRICES_USD_PER_MTOK, so a run could not record its cost
    (ADR-0020)."""


class RunFailed(RuntimeError):
    """The run could not continue for a reason that is not the model's: a tool failed
    in a way the model cannot correct. The cause is chained."""


def diagnose(
    *,
    baseline: str | Path,
    current: str | Path,
    repo: str | Path,
    git_range: str,
    metric: str = AUTO,
    client: Any = None,
    binary: Path | None = None,
    cache_dir: Path | None = QUERY_CACHE_DIR,
    model: str = MODEL,
    effort: str = EFFORT,
) -> dict:
    """Runs the agent on one trace pair and one range, and returns `diagnosis.json`
    (DIAGNOSIS_SCHEMA) as `verify` left it.

    `metric` is `auto` or a name from the library. `client` is an `anthropic.Anthropic`
    (default: one built from the environment's credentials). `binary` is the trace
    processor (default: the pinned one) and `cache_dir` where verified query results
    are kept (ADR-0006).

    Raises, before any request: UnpricedModel for a model with no price,
    FileNotFoundError for a missing trace, RangeError for a range verify would refuse,
    UnknownMetric for a metric not in the library, and TraceProcessorError when there
    is no trace processor. During the run: the SDK's API errors, RunFailed, and
    DiagnosisInvalid if the model's answer does not match OUTPUT_SCHEMA; nothing is
    returned for a run that raised.
    """
    started = time.monotonic()
    if model not in PRICES_USD_PER_MTOK:
        raise UnpricedModel(
            f"no price for {model!r}; priced: {', '.join(PRICES_USD_PER_MTOK)}"
        )
    traces = {"baseline": Path(baseline), "current": Path(current)}
    for side, trace in traces.items():
        if not trace.is_file():
            raise FileNotFoundError(f"no {side} trace at {trace}")
    # Shas, not the names given: a branch name can say what the range holds
    # (ADR-0022).
    git_range = check_range(repo, git_range)
    if metric != AUTO and metric not in {m["name"] for m in metric_library()}:
        raise UnknownMetric(f"no metric named {metric!r}; see list_metrics")
    binary = binary or resolve_trace_processor()
    if client is None:
        client = anthropic.Anthropic()

    context = TraceContext(traces=traces, binary=binary)
    bound = [(t, context) for t in TRACE_TOOLS] + [(t, Path(repo)) for t in REPO_TOOLS]
    loop = _Loop(client, model, effort, bound)
    message = loop.run(first_message(git_range, metric))

    output = _output_of(message)
    output = _with_measured_metric(output, metric, context)
    run = {
        "tool_calls": loop.tool_calls,
        "usage": loop.usage,
        "usd": usd(model, loop.usage),
        "wall_time_s": round(time.monotonic() - started, 3),
    }
    try:
        return verify(
            output,
            current=traces["current"],
            baseline=traces["baseline"],
            repo=repo,
            git_range=git_range,
            run=run,
            binary=binary,
            cache_dir=cache_dir,
        )
    except GitError as e:
        # The repo read fine before the run; failing now is not the input's fault.
        raise RunFailed(f"the verifier could not read the repo: {e}") from e


def first_message(git_range: str, metric: str) -> str:
    """The run's volatile inputs, after the cached prefix: the range and the metric.
    No path: see the module docstring."""
    base, _, head = git_range.partition("..")
    choice = (
        "Choose the metric with list_metrics."
        if metric == AUTO
        else f"Judge by the metric {metric}."
    )
    return (
        "The two traces are loaded as `baseline` and `current`. The range is "
        f"`{git_range}`: the commits after {base} up to and including {head}. "
        f"{choice} Diagnose the change."
    )


def usd(model: str, usage: dict) -> float:
    """What `usage` cost on `model`, from PRICES_USD_PER_MTOK."""
    prices = PRICES_USD_PER_MTOK[model]
    return round(sum(usage[f] * prices[f] for f in USAGE_FIELDS) / 1_000_000, 6)


class _Loop:
    """One Tool Runner conversation, and what it cost."""

    def __init__(self, client, model: str, effort: str, bound: list):
        self._client = client
        self._model = model
        self._effort = effort
        self._fatal: list[BaseException] = []
        self._tools = [self._runnable(tool, ctx) for tool, ctx in bound]
        self.tool_calls = 0
        self.usage = dict.fromkeys(USAGE_FIELDS, 0)

    def run(self, user_message: str):
        """The last message of the conversation, once the model stops calling tools
        or MAX_TURNS is reached."""
        runner = self._client.beta.messages.tool_runner(
            model=self._model,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self._effort,
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
            },
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=self._tools,
            messages=[{"role": "user", "content": user_message}],
            max_iterations=MAX_TURNS,
            stream=True,
        )
        message = None
        for stream in runner:
            message = stream.get_final_message()
            self._count(message)
            if message.stop_reason == "tool_use":
                # Run this turn's tools now, not when the runner next asks: a failure
                # of the run must stop it here, before another request. The runner
                # reuses this response rather than calling the tools again.
                runner.generate_tool_call_response()
                if self._fatal:
                    raise RunFailed(f"a tool failed: {self._fatal[0]}") from (
                        self._fatal[0]
                    )
        return message

    def _count(self, message) -> None:
        self.tool_calls += sum(1 for b in message.content if b.type == "tool_use")
        for field in USAGE_FIELDS:
            self.usage[field] += getattr(message.usage, field, None) or 0

    def _runnable(self, tool: Tool, context):
        """`tool` as the Tool Runner takes it: its hand-written schema and description
        unchanged, strict, and answered through `Tool.call`."""

        def call(**arguments) -> str:
            try:
                return json.dumps(tool.call(context, arguments))
            except MODEL_ERRORS as e:
                raise ToolError(_for_model(str(e))) from e
            except Exception as e:
                self._fatal.append(e)
                raise ToolError("internal error; the run is stopping") from e

        return beta_tool(
            call,
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            strict=True,
        )


def _for_model(message: str) -> str:
    message = message.strip()
    if len(message) <= MAX_ERROR_CHARS:
        return message
    return "…" + message[-MAX_ERROR_CHARS:]


def _output_of(message) -> dict:
    """The model's OUTPUT_SCHEMA answer, from its last message. `stop_reason` is read
    first: a refusal or a cut-off answer has no content to trust."""
    reason = message.stop_reason
    if reason == "refusal":
        details = getattr(message, "stop_details", None)
        category = getattr(details, "category", None) or "unspecified"
        return _unanswered(f"the model declined to answer (refusal: {category})")
    if reason == "max_tokens":
        return _unanswered(f"the answer was cut off at max_tokens ({MAX_TOKENS})")
    # The runner returns on a tool_use turn only when max_iterations is reached; any
    # other tool_use turn it answers and continues.
    if reason == "tool_use":
        return _unanswered(f"the run stopped after {MAX_TURNS} turns without an answer")
    if reason not in ("end_turn", "stop_sequence"):
        return _unanswered(f"the run ended without an answer (stop_reason: {reason})")
    text = "".join(b.text for b in message.content if b.type == "text")
    try:
        output = json.loads(text)
    except json.JSONDecodeError as e:
        raise DiagnosisInvalid("the model's output", [f"$: not JSON: {e}"]) from e
    check_output(output)
    return output


def _unanswered(reason: str) -> dict:
    """An OUTPUT_SCHEMA answer for a run that gave none: inconclusive, no claims."""
    return {
        "verdict": "inconclusive",
        "metric": None,
        "confidence": "low",
        "culprit": None,
        "claims": [],
        "caveats": [reason],
    }


def _with_measured_metric(output: dict, requested: str, context) -> dict:
    """`output` with its metric re-measured by name (ADR-0006): the one the user
    named, else the one the model named. A name the library lacks leaves no metric,
    and a caveat that says so."""
    named = output["metric"]["name"] if output["metric"] else None
    name = requested if requested != AUTO else named
    if name is None:
        return output
    try:
        measured = compute_metric(
            name,
            current=context.traces["current"],
            baseline=context.traces["baseline"],
            binary=context.binary,
        )
    except UnknownMetric:
        caveat = f"the model named a metric not in the library, {name!r}; dropped"
        return {**output, "metric": None, "caveats": [*output["caveats"], caveat]}
    except MetricError as e:
        # Its SQL gave rows of the wrong shape on these traces: no number to report.
        caveat = f"the metric {name!r} could not be measured: {e}; dropped"
        return {**output, "metric": None, "caveats": [*output["caveats"], caveat]}
    metric = {field: measured[field] for field in METRIC_FIELDS}
    return {**output, "metric": metric}
