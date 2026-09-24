"""`diagnose`: two traces and a git range in, a verified `diagnosis.json` out (roadmap
item 7, issues #29 and #43).

The run is the same on both providers (ADR-0020): the frozen system prompt, the tools
and their strict schemas, the output schema, its local check and the verifier. Only the
conversation differs, and each provider's loop runs it: `anthropic_loop` on the
Anthropic SDK's Tool Runner, `openai_loop` on OpenAI's Responses API. Every tool call
goes through `Tool.call`, which checks the arguments against the tool's hand-written
schema (ADR-0018). An error the model can correct (a bad argument, SQL that does not
run, a commit that is not there) comes back to it as an error result. Anything else
(git cannot run, the trace processor vanished) is a failure of the run and is raised,
never shown to the model as its own mistake.

What the model answers is structured output, `diagnosis.OUTPUT_SCHEMA`, checked again
here with `check_output`, and then always run through `verify`: no claim reaches the
file without its citations being re-run (CLAUDE.md). Before the verifier, the metric
the model names is re-measured with `compute_metric`, so its numbers and `sql_used`
are ours, not the model's copy of them (ADR-0006).

A run that ends without an answer (the model refused, or ran out of tokens or turns)
is still a diagnosis: `inconclusive`, with no claims and the reason as a caveat, so its
cost is recorded like any other run's. A refusal is never retried.

Eval integrity (CLAUDE.md): the model is shown the range and the metric choice, never
a path. The trace tools name a trace by its side, and the git tools read the repo the
run binds, so nothing it sees says where either came from.
"""

import json
import time
from pathlib import Path
from typing import Any

import anthropic
import openai

from perfettoagent import models
from perfettoagent.anthropic_loop import AnthropicLoop
from perfettoagent.credentials import api_key
from perfettoagent.diagnosis import (
    METRIC_FIELDS,
    OUTPUT_SCHEMA,
    DiagnosisInvalid,
    check_output,
)
from perfettoagent.git import GitError
from perfettoagent.loop import Ending, RunFailed
from perfettoagent.metrics import MetricError, UnknownMetric, compute_metric
from perfettoagent.metrics import list_metrics as metric_library
from perfettoagent.openai_loop import OpenAILoop
from perfettoagent.repo_tools import REPO_TOOLS
from perfettoagent.symbolize import TraceContext
from perfettoagent.trace_processor import resolve_trace_processor
from perfettoagent.trace_tools import TRACE_TOOLS
from perfettoagent.verify import QUERY_CACHE_DIR, check_range, verify

# `--metric auto`: the model picks from list_metrics (roadmap Q3).
AUTO = "auto"

# Each provider's loop (ADR-0020).
LOOPS = {"anthropic": AnthropicLoop, "openai": OpenAILoop}

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
    provider: str = models.DEFAULT_PROVIDER,
    model: str | None = None,
    effort: str = models.DEFAULT_EFFORT,
) -> dict:
    """Runs the agent on one trace pair and one range, and returns `diagnosis.json`
    (DIAGNOSIS_SCHEMA) as `verify` left it.

    `metric` is `auto` or a name from the library. `provider` is `openai` or
    `anthropic`, and `model` defaults to the provider's own (models.DEFAULT_MODELS).
    `client` is that provider's SDK client (default: one built with the key from the
    environment or `.env`, credentials.api_key). `binary` is the trace processor
    (default: the pinned one) and `cache_dir` where verified query results are kept
    (ADR-0006).

    Raises, before any request: ModelRefused for a model with no price, on the wrong
    provider or at an effort it lacks,
    FileNotFoundError for a missing trace, RangeError for a range verify would refuse,
    UnknownMetric for a metric not in the library, and TraceProcessorError when there
    is no trace processor. During the run: the SDK's API errors, RunFailed, and
    DiagnosisInvalid if the model's answer does not match OUTPUT_SCHEMA; nothing is
    returned for a run that raised.
    """
    started = time.monotonic()
    model = model or models.DEFAULT_MODELS.get(provider, "")
    models.check_model(provider, model, effort)
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
        client = make_client(provider)

    context = TraceContext(traces=traces, binary=binary)
    bound = [(t, context) for t in TRACE_TOOLS] + [(t, Path(repo)) for t in REPO_TOOLS]
    loop = LOOPS[provider](client, model, effort, bound)
    ending = loop.run(SYSTEM_PROMPT, first_message(git_range, metric), OUTPUT_SCHEMA)

    output = _output_of(ending)
    output = _with_measured_metric(output, metric, context)
    run = {
        "provider": provider,
        "model": model,
        "effort": effort,
        "tool_calls": loop.cost.tool_calls,
        "usage": loop.cost.usage,
        "usd": round(loop.cost.usd, 6),
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


def make_client(provider: str):
    """The provider's SDK client, with its key from the environment or `.env`. With
    no key the SDK raises its own error, which names the variable, never a value. An
    Anthropic client with no key given falls back to an `ant auth login` profile."""
    if provider == "openai":
        return openai.OpenAI(api_key=api_key("OPENAI_API_KEY"))
    key = api_key("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=key) if key else anthropic.Anthropic()


def _output_of(ending: Ending) -> dict:
    """The model's OUTPUT_SCHEMA answer, or an inconclusive one for a run that gave
    none. An answer that is not JSON, or not the schema, raises DiagnosisInvalid."""
    if ending.unanswered is not None:
        return _unanswered(ending.unanswered)
    try:
        output = json.loads(ending.text)
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
