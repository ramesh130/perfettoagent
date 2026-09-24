"""The metric library: canned SQL the agent runs by name and cites verbatim.

A metric is one `.sql` file in this directory, named for the metric, and nothing else:
adding one is adding a file and its fixture test, with no change to the code here.

A file is a header of `--` comment lines, then the SQL. In the header, the
`-- @field: value` lines are the metadata `list_metrics` reports, and every other line
is a note for whoever edits the file. The SQL starts at the first line that is not a
comment: any `INCLUDE PERFETTO MODULE` lines first, then one SELECT. A scalar metric's
`sql_used` is that SQL verbatim; a keyed metric's wraps it (below), INCLUDE lines
still first and verbatim. Either way it is exactly what the model sees and cites.
ADR-0005 records this result shape.

    @description        what it measures, for the model choosing a metric (required)
    @unit               the unit of every value, e.g. ms, objects, bytes (required)
    @requires_baseline  true if the number means nothing without a baseline (required)
    @key                present for a keyed metric: what its key column names
    @no_data            why the SQL can return NULL: what the trace lacks (optional)

Two shapes of SQL:

- Scalar: one row, one column named `value`. `baseline` and `current` are that value on
  each trace, and `sql_used` is the file's SQL.
- Keyed (has `@key`): one row per key, columns `key` and `value`, e.g. reachable objects
  per class. Values must add up across keys, because an absent key counts as 0 and the
  headline is their sum. The result also has a `breakdown`: the keys that changed most,
  each with its own `sql_used` that returns exactly its one number.

No data is not zero. A metric whose SQL returns NULL on a trace says that the trace
lacks what it reads (a data source was off, or the app it looks for is absent), and
`baseline`/`current` is None for that side. The result then also carries `no_data`,
{side: reason}, with the file's `@no_data` text, so the model is told why in words
and cannot mistake the missing number for a measured 0. ADR-0014 records this.

Why each number carries its own SQL: the verifier (roadmap item 4) re-runs a citation's
SQL through `query_trace`, which returns at most MAX_ROWS rows, and a heap dump has tens
of thousands of classes. SQL narrowed to the one number cited re-runs to that number, on
either trace, which the whole table never could.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from perfettoagent.query import (
    QueryRejected,
    check_select,
    join_includes,
    query_trace,
    split_includes,
)

# Where the shipped metrics live: inside the package, so they ship in the wheel.
METRIC_DIR = files(__name__)

# Rows of a keyed metric's breakdown shown to the model, ranked by growth. What grows in
# a heap is rarely one class: a retained object drags its whole graph along, so several
# classes grow by the same count, and churn (strings, arrays, caches) often grows more.
# The cap has to fit such a cohort below that churn. Each row carries its own sql_used,
# about 150 tokens, so 40 rows is about 6k tokens: a fraction of one agent run, and
# never the whole table (hundreds of classes change between two dumps). `row_count`
# gives the true total, and the model can narrow further with query_trace.
BREAKDOWN_ROWS = 40

# One `-- @field: value` metadata line in a metric file's header (format above).
_FIELD = re.compile(r"--\s*@(\w+):\s*(.*)")

# The header fields, as the module docstring lists them. Any other @field is refused,
# so a misspelt one (`@requires_basline`) fails loudly instead of defaulting.
_REQUIRED = ("description", "unit", "requires_baseline")
_OPTIONAL = ("key", "no_data")

# Exactly these spellings: "yes", "1" or "no" in a hand-edited header are refused
# rather than guessed at.
_BOOLEANS = {"true": True, "false": False}

# The reason a result gives for a NULL value when its file has no @no_data line: all
# that is known then is that the SQL found nothing to measure.
_NO_DATA = "the trace lacks the data this metric reads, so its SQL returned NULL"

# The two sides of a comparison, in the order results report them.
_SIDES = ("baseline", "current")


class MetricError(ValueError):
    """A metric file is malformed, or a metric cannot run on the traces given."""


class UnknownMetric(MetricError, KeyError):
    """No metric has this name."""

    def __str__(self) -> str:  # KeyError would print the message in quotes
        return str(self.args[0])


@dataclass(frozen=True)
class Metric:
    name: str
    description: str
    unit: str
    requires_baseline: bool
    key: str | None
    # Why the SQL can return NULL, for the result's `no_data`.
    no_data: str
    # The file's SQL from its first non-comment line: `sql_used`, verbatim.
    sql: str

    def listing(self) -> dict:
        entry = {
            "name": self.name,
            "description": self.description,
            "unit": self.unit,
            "requires_baseline": self.requires_baseline,
        }
        if self.key is not None:
            entry["key"] = self.key
        return entry


def list_metrics() -> list[dict]:
    """The library, by name: each metric's description, unit, whether it needs a
    baseline, and, for a keyed metric, what its key is. JSON-serialisable."""
    return [m.listing() for m in _load_library().values()]


def compute_metric(
    name: str,
    *,
    current: str | Path,
    baseline: str | Path | None = None,
    binary: Path | None = None,
) -> dict:
    """Runs metric `name` on `current`, and on `baseline` if given, and returns

        {name, unit, baseline, current, delta, sql_used}

    plus `breakdown` for a keyed metric, and `no_data`, {side: reason}, for each trace
    given on which the metric's value is NULL (see the module docstring). `baseline`
    and `delta` are None without a baseline, which only a metric with
    `requires_baseline: false` accepts. `delta` is current - baseline. `sql_used` is
    the SQL that returns `baseline` on the baseline trace and `current` on the current
    one; `split_includes` turns it into the arguments `query_trace` takes.
    JSON-serialisable.

    Raises UnknownMetric for a name not in `list_metrics()`, and MetricError when a
    needed baseline is missing or the SQL returns rows of the wrong shape.
    """
    library = _load_library()
    metric = library.get(name)
    if metric is None:
        raise UnknownMetric(
            f"no metric named {name!r}; the library has: {', '.join(sorted(library))}"
        )
    if metric.requires_baseline and baseline is None:
        raise MetricError(f"{name} needs a baseline trace to compare against")

    traces = dict(zip(_SIDES, (baseline, current), strict=True))
    statement, modules = split_includes(metric.sql)
    if metric.key is None:
        sql_used = metric.sql
    else:
        headline = f"SELECT sum(value) AS value FROM (\n{statement}\n)"
        sql_used = join_includes(headline, modules)
    values = _per_side(traces, lambda t: _scalar_of(sql_used, name, t, binary))

    result = {
        "name": name,
        "unit": metric.unit,
        "baseline": values["baseline"],
        "current": values["current"],
        "delta": _delta(values["baseline"], values["current"]),
        "sql_used": sql_used,
    }
    no_data = {
        side: metric.no_data
        for side, trace in traces.items()
        if trace is not None and values[side] is None
    }
    if no_data:
        result["no_data"] = no_data
    if metric.key is not None:
        result["breakdown"] = _breakdown(metric, statement, modules, traces, binary)
    return result


def _per_side(traces: dict, run) -> dict:
    """{side: run(trace)} for each side, None for a side with no trace."""
    return {side: None if t is None else run(t) for side, t in traces.items()}


def _scalar_of(sql_used: str, name: str, trace, binary):
    """Runs cited SQL whose one row, one column is the value: how every cited number
    is produced, so re-running the citation gives it back."""
    statement, modules = split_includes(sql_used)
    result = query_trace(statement, trace, modules=modules, binary=binary)
    if result["columns"] != ["value"] or result["row_count"] != 1:
        raise MetricError(
            f"{name}: expected one row with one column `value`, got "
            f"{result['row_count']} rows of {result['columns']}"
        )
    return result["rows"][0][0]


def _breakdown(
    metric: Metric,
    statement: str,
    modules: Sequence[str],
    traces: dict,
    binary,
) -> dict:
    """The keys that changed most, or the largest keys without a baseline."""
    per_side = _per_side(
        traces, lambda t: _values_by_key(metric, statement, modules, t, binary)
    )
    base, cur = per_side["baseline"], per_side["current"]
    if base is None:
        rows = [
            {"key": k, "baseline": None, "current": v, "delta": None}
            for k, v in cur.items()
        ]
        rows.sort(key=lambda r: (-r["current"], _sort_key(r["key"])))
    else:
        rows = [
            {
                "key": k,
                "baseline": base.get(k, 0),
                "current": cur.get(k, 0),
                "delta": cur.get(k, 0) - base.get(k, 0),
            }
            for k in base.keys() | cur.keys()
        ]
        # Only what changed; a regression is growth, so the largest growth first.
        rows = [r for r in rows if r["delta"] != 0]
        rows.sort(key=lambda r: (-r["delta"], _sort_key(r["key"])))
    shown = rows[:BREAKDOWN_ROWS]
    for row in shown:
        row["sql_used"] = join_includes(_one_key_sql(statement, row["key"]), modules)
    return {
        "key": metric.key,
        "rows": shown,
        "row_count": len(rows),
        "truncated": len(rows) > len(shown),
    }


def _values_by_key(metric: Metric, statement: str, modules, trace, binary) -> dict:
    """{key: value} for every row of a keyed metric on one trace. Every row, uncapped:
    the join across two traces happens here, before the model sees any of it."""
    result = query_trace(
        statement, trace, modules=modules, binary=binary, max_rows=None
    )
    if result["columns"] != ["key", "value"]:
        raise MetricError(
            f"{metric.name}: a keyed metric returns columns key, value; "
            f"got {result['columns']}"
        )
    values = {key: value for key, value in result["rows"]}
    if len(values) != len(result["rows"]):
        raise MetricError(f"{metric.name}: a key appears in more than one row")
    return values


def _one_key_sql(statement: str, key) -> str:
    """SQL that returns one row, (key, value), on any trace: 0 where the key is absent,
    since a keyed metric's absent key counts as 0. So a citation of a class that is new
    in the current trace still re-runs to a row on the baseline."""
    literal = _sql_literal(key)
    return (
        f"SELECT {literal} AS key, coalesce((SELECT value FROM (\n{statement}\n) "
        f"WHERE key IS {literal}), 0) AS value"
    )


def _sql_literal(value) -> str:
    # ref: https://www.sqlite.org/lang_expr.html#literal_values_constants_
    if value is None:
        return "NULL"
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise MetricError(f"a metric key must be text or a number, not {value!r}")
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return repr(value)


def _sort_key(key) -> tuple:
    """The tie-break between rows of equal value: by key, so the order is the same on
    every run. Python cannot compare text with numbers or None, which one metric's keys
    may mix, so keys sort by type name first, then by value; NULL last."""
    return (key is None, str(type(key)), key if key is not None else 0)


def _delta(baseline, current):
    """current - baseline, or None when either side has no value to subtract."""
    if baseline is None or current is None:
        return None
    return current - baseline


def _load_library() -> dict[str, Metric]:
    """Reads every metric file in METRIC_DIR. Read on each call rather than cached:
    it is a few small files, and a malformed one fails here, loudly, every time."""
    library = {}
    for entry in sorted(METRIC_DIR.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".sql"):
            metric = _parse(entry.name.removesuffix(".sql"), entry.read_text())
            library[metric.name] = metric
    return library


def _parse(name: str, text: str) -> Metric:
    lines = text.splitlines(keepends=True)
    fields: dict[str, str] = {}
    start = len(lines)
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("--"):
            start = i
            break
        if m := _FIELD.fullmatch(stripped):
            field, value = m.group(1), m.group(2).strip()
            if field not in _REQUIRED + _OPTIONAL:
                raise MetricError(f"{name}.sql: unknown field @{field}")
            fields[field] = value
    sql = "".join(lines[start:])

    for field in _REQUIRED:
        if not fields.get(field):
            raise MetricError(f"{name}.sql: missing @{field}")
    requires_baseline = _BOOLEANS.get(fields["requires_baseline"])
    if requires_baseline is None:
        raise MetricError(
            f"{name}.sql: @requires_baseline must be true or false, "
            f"not {fields['requires_baseline']!r}"
        )
    try:
        check_select(split_includes(sql)[0])
    except QueryRejected as e:
        raise MetricError(
            f"{name}.sql: after its INCLUDEs, a metric is one SELECT: {e}"
        ) from e
    return Metric(
        name=name,
        description=fields["description"],
        unit=fields["unit"],
        requires_baseline=requires_baseline,
        key=fields.get("key") or None,
        no_data=fields.get("no_data") or _NO_DATA,
        sql=sql,
    )
