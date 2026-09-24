"""The agent's tools over the two traces: `query_trace`, `list_metrics` and
`compute_metric`, declared as `Tool`s like the git tools and `symbolize` (ADR-0018,
docs/tech-stack.md "Agent tool surface and limits").

Each is a thin binding of a function that already exists (`perfettoagent.query`,
`perfettoagent.metrics`) to a `TraceContext`, the run's two traces by side. The model
names a side, `baseline` or `current`, never a path: paths are the run's to bind, and a
path can say more about a trace than the trace does.

`query_trace` takes SQL in the same form a trace citation takes: one SELECT or WITH,
optionally preceded by `INCLUDE PERFETTO MODULE` lines (ADR-0005). So the model can
use the Perfetto stdlib modules that docs/tech-stack.md asks for, and what it ran is
exactly what it can cite and the verifier re-runs. The statement after the INCLUDE
lines still has to pass the SELECT-only gate.
"""

from perfettoagent.diagnosis import SIDES
from perfettoagent.metrics import BREAKDOWN_ROWS, compute_metric, list_metrics
from perfettoagent.query import MAX_ROWS, query_trace, split_includes
from perfettoagent.symbolize import SYMBOLIZE, TraceContext
from perfettoagent.tools import STRING, Tool, ToolInputError, described, strict_input

# The side a trace tool runs on. Traces are named by side, never by path.
_WHICH = described(
    {"type": "string", "enum": list(SIDES)}, "The trace to run on: its side."
)


def _trace(context: TraceContext, which: str):
    trace = context.traces.get(which)
    if trace is None:
        raise ToolInputError(f"which: this run has no {which!r} trace")
    return trace


def run_query(context: TraceContext, sql: str, which: str) -> dict:
    """One query on the `which` trace, at most MAX_ROWS rows."""
    statement, modules = split_includes(sql)
    return query_trace(
        statement, _trace(context, which), modules=modules, binary=context.binary
    )


def run_list_metrics(context: TraceContext) -> dict:
    """The metric library. `context` is unused: the library is the same every run."""
    return {"metrics": list_metrics()}


def run_compute_metric(context: TraceContext, name: str) -> dict:
    """Metric `name` on both traces, with the SQL that gives each number."""
    return compute_metric(
        name,
        current=_trace(context, "current"),
        # Optional: a metric that needs a baseline raises MetricError without one.
        baseline=context.traces.get("baseline"),
        binary=context.binary,
    )


QUERY_TRACE = Tool(
    name="query_trace",
    description=(
        "Run one read-only SQL query on one of the two traces with Perfetto's trace "
        "processor. `sql` is one SELECT or WITH ... SELECT statement, optionally "
        "preceded by `INCLUDE PERFETTO MODULE <name>;` lines for the Perfetto "
        "standard library (e.g. android.startup.startups, android.frames.timeline); "
        "nothing else runs. The result has `columns`, at most "
        f"{MAX_ROWS} `rows`, `row_count` (always the true total) and `truncated`; "
        "aggregate in SQL rather than paging. A query you ran can be cited verbatim, "
        "with its trace. It cannot tell you anything the trace did not record (a data "
        "source that was off leaves its tables empty), nor which code or commit "
        "produced a row: that is for the git tools."
    ),
    input_schema=strict_input(
        sql=described(STRING, "One SELECT or WITH query, INCLUDE lines first."),
        which=_WHICH,
    ),
    function=run_query,
)

LIST_METRICS = Tool(
    name="list_metrics",
    description=(
        "List the canned metrics compute_metric can measure: each one's name, what it "
        "measures, its unit, whether it needs a baseline, and, for a metric broken "
        "down by key, what the key names. It cannot tell you which metric changed "
        "between the traces; measure them to find out. It lists this library only, "
        "not everything the traces could be asked with query_trace."
    ),
    input_schema=strict_input(),
    function=run_list_metrics,
)

COMPUTE_METRIC = Tool(
    name="compute_metric",
    description=(
        "Measure one metric from list_metrics on both traces: `baseline`, `current` "
        "and `delta` (current - baseline), with `sql_used`, the SQL that returns each "
        "value on its own trace, to cite verbatim. A value the trace has no data for "
        "is null, never 0, and `no_data` says why. A metric with a key also returns "
        f"`breakdown`: at most {BREAKDOWN_ROWS} keys, those that grew most, each with "
        "its own `sql_used`; `row_count` is the true number of keys that changed. It "
        "cannot tell you whether a delta is beyond run-to-run noise, nor what caused "
        "it."
    ),
    input_schema=strict_input(
        name=described(STRING, "A metric name from list_metrics."),
    ),
    function=run_compute_metric,
)

# In the order the agent is expected to reach for them. All take a TraceContext.
TRACE_TOOLS = (LIST_METRICS, COMPUTE_METRIC, QUERY_TRACE, SYMBOLIZE)
