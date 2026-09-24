"""What the two providers' agent loops share (ADR-0020, ADR-0022): the limits, which
tool errors go back to the model, and how a loop reports how it ended.

Each loop (`anthropic_loop`, `openai_loop`) takes the frozen system prompt, the first
user message, the output schema and the bound tools, runs the conversation, and returns
an `Ending`: the model's answer text, or why there is none. What the answer means is
`agent`'s business, the same for both.
"""

import json
from dataclasses import dataclass, field

from perfettoagent import models
from perfettoagent.git import GitError
from perfettoagent.metrics import MetricError
from perfettoagent.query import QueryRejected
from perfettoagent.tools import Tool, ToolInputError
from perfettoagent.trace_processor import TraceProcessorError

# docs/tech-stack.md: the per-response output ceiling on both providers (`max_tokens`,
# `max_output_tokens`). Streamed, so the SDK's HTTP timeout does not apply to a long
# response.
MAX_TOKENS = 64000

# Model turns before the run stops as inconclusive. A diagnosis takes a few dozen tool
# calls; a loop past this is not converging, and each turn resends the context.
MAX_TURNS = 60

# What a tool raises when the model's call was at fault: it gets the message back as an
# error result, to correct (ADR-0022). A TraceProcessorError counts, because the binary
# is resolved and both traces are checked before the loop, so one raised inside it is
# the SQL's own doing (a syntax error, an unknown table, a timeout). GitUnavailable is
# not a GitError on purpose, and raises (perfettoagent.git).
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


class RunFailed(RuntimeError):
    """The run could not continue for a reason that is not the model's: a tool failed
    in a way the model cannot correct, or the provider ended the response in error.
    The cause is chained."""


@dataclass(frozen=True)
class Ending:
    """How a conversation ended: the model's final text, or, when it gave no answer
    to read, why (a refusal, a cut-off, too many turns). Exactly one is set."""

    text: str | None = None
    unanswered: str | None = None


@dataclass
class Cost:
    """What a conversation cost so far: tool calls, usage in `run.usage`'s shape, and
    USD, priced request by request (models.usd)."""

    model: str
    tool_calls: int = 0
    usage: dict = field(default_factory=lambda: dict.fromkeys(models.USAGE_FIELDS, 0))
    usd: float = 0.0

    def add(self, tool_calls: int, usage: dict) -> None:
        """One response: its tool calls, and its usage in `run.usage`'s shape."""
        self.tool_calls += tool_calls
        for name, count in usage.items():
            self.usage[name] += count
        self.usd += models.usd(self.model, usage)


def refused(reason: str) -> Ending:
    """A refusal: `reason` is its category (Anthropic) or its text (OpenAI)."""
    return Ending(unanswered=f"the model declined to answer (refusal: {reason})")


def cut_off(limit: str) -> Ending:
    """An answer cut off at the output cap, named as the provider names it."""
    return Ending(unanswered=f"the answer was cut off at {limit} ({MAX_TOKENS})")


def out_of_turns() -> Ending:
    reason = f"the run stopped after {MAX_TURNS} turns without an answer"
    return Ending(unanswered=reason)


class ModelError(Exception):
    """A tool call the model got wrong; the message is for the model to read."""


def call_tool(tool: Tool, context, arguments: dict) -> str:
    """One tool call, as the model sees its result: JSON. Raises ModelError for a
    mistake the model can correct, and RunFailed for anything else."""
    try:
        return json.dumps(tool.call(context, arguments))
    except MODEL_ERRORS as e:
        raise ModelError(for_model(str(e))) from e
    except Exception as e:
        raise RunFailed(f"a tool failed: {e}") from e


def for_model(message: str) -> str:
    """An error message as the model is shown it: at most MAX_ERROR_CHARS, keeping
    the end, which names what went wrong."""
    message = message.strip()
    if len(message) <= MAX_ERROR_CHARS:
        return message
    return "…" + message[-MAX_ERROR_CHARS:]
