"""`query_trace`: one read-only SQL query against a trace, capped at MAX_ROWS rows.

This is the code path behind both `perfettoagent tp` and the agent's `query_trace` tool,
so the gate and the row cap below hold for both.

How rows come back. trace_processor_shell prints each result set as CSV, but not
reversibly: embedded double quotes are not escaped, NULL prints as "[NULL]", and reals
print with six decimals. So the query is never read back as CSV. It is wrapped in a temp
view and run twice, each time as a script on stdin:

1. `pragma_table_info` on the view gives the column names, as one JSON array.
2. Each row comes back as one `json_array(...)` value, capped at MAX_ROWS in SQL, and
   `count(*)` over the view gives the true row count.

JSON escapes quotes and newlines, so each row is exactly one output line, and types
survive (null, integers, reals at 15 significant digits, strings). A BLOB comes back as
null, because JSON cannot hold one; select `hex(col)` to see it.

ref: https://perfetto.dev/docs/analysis/trace-processor
ref: https://www.sqlite.org/json1.html#jarray
"""

import json
import re
from collections.abc import Sequence
from pathlib import Path

from perfettoagent.trace_processor import (
    TraceProcessorError,
    resolve_trace_processor,
    run_sql_script,
)

# docs/tech-stack.md: a tool result is read by the model, and every row costs context.
# 200 rows is enough to see a distribution or the top of a ranking; for more, the model
# should aggregate in SQL. `row_count` always gives the true total.
MAX_ROWS = 200

# Names that cannot collide with anything in a trace or the Perfetto stdlib.
_VIEW = "__perfettoagent_query"
_COLUMNS = "__perfettoagent_columns"
_ROW = "__perfettoagent_row"
_COUNT = "__perfettoagent_count"

# A Perfetto stdlib module name, e.g. `android.startup.startups`.
# ref: https://perfetto.dev/docs/analysis/stdlib-docs
_MODULE = re.compile(r"[a-z0-9_]+(\.[a-z0-9_]+)*")

# One `INCLUDE PERFETTO MODULE x;` at the front of cited SQL, with the whitespace and
# `--` comment lines before it. Keywords are case-insensitive in trace processor's SQL.
# ref: https://perfetto.dev/docs/analysis/perfetto-sql-syntax#including-perfettosql-modules
_LEADING_INCLUDE = re.compile(
    r"(?:\s|--[^\n]*\n)*(?i:INCLUDE\s+PERFETTO\s+MODULE)\s+"
    r"([a-z0-9_]+(?:\.[a-z0-9_]+)*)\s*;[ \t]*\n?"
)

# The keywords that can start the main statement after a WITH clause's CTEs. SQLite
# allows `WITH x AS (...) DELETE ...`, so a leading WITH alone proves nothing.
# ref: https://www.sqlite.org/lang_with.html
_MAIN_STATEMENT = {"select", "values", "insert", "update", "delete", "replace"}

# A bare SQLite identifier or keyword.
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_$]*")


class QueryRejected(ValueError):
    """The SQL is not a single SELECT or WITH ... SELECT statement."""


def check_select(sql: str) -> str:
    """Returns `sql` as one read-only statement, or raises QueryRejected.

    Accepts exactly one `SELECT` or `WITH ... SELECT` statement, with any comments and
    whitespace around it and at most a trailing `;`. Everything else is rejected here,
    before it reaches the trace processor: other statements (including `INCLUDE PERFETTO
    MODULE`), a WITH clause in front of anything but SELECT, and a second statement
    after a `;`. The returned text is the statement without its trailing `;`.

    This is a lexer, not a parser: it knows SQLite's comments, string literals and
    quoted identifiers, so a `;` or keyword inside one of those is not mistaken for SQL.
    ref: https://www.sqlite.org/lang_comment.html
    ref: https://www.sqlite.org/lang_keywords.html
    """
    words: list[str] = []  # bare words at parenthesis depth 0, lower-cased
    depth = 0
    end: int | None = None  # index of the statement-ending `;`
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c.isspace():
            i += 1
        elif sql.startswith("--", i):
            newline = sql.find("\n", i)
            i = n if newline < 0 else newline + 1
        elif sql.startswith("/*", i):
            close = sql.find("*/", i + 2)
            if close < 0:
                raise QueryRejected("unterminated /* comment")
            i = close + 2
        elif end is not None:
            raise QueryRejected("only one statement is allowed; found more after `;`")
        elif c in "'\"`[":
            i = _skip_quoted(sql, i)
        elif c == ";":
            end = i
            i += 1
        elif c == "(":
            depth += 1
            i += 1
        elif c == ")":
            depth -= 1
            i += 1
        elif m := _WORD.match(sql, i):
            if depth == 0:
                words.append(m.group().lower())
            i = m.end()
        else:
            i += 1

    if not words:
        raise QueryRejected("no SQL statement found")
    first = words[0]
    if first == "with":
        main = next((w for w in words if w in _MAIN_STATEMENT), None)
        if main != "select":
            raise QueryRejected(
                f"a WITH clause may only lead into SELECT, not {main or 'nothing'}"
            )
    elif first != "select":
        raise QueryRejected(
            f"only SELECT or WITH ... SELECT queries are allowed, not {first.upper()}"
        )
    return sql[:end]


def query_trace(
    sql: str,
    trace: str | Path,
    *,
    modules: Sequence[str] = (),
    binary: Path | None = None,
    max_rows: int | None = MAX_ROWS,
) -> dict:
    """Runs one SELECT on `trace` and returns at most `max_rows` of its rows.

    Returns `{"columns": [...], "rows": [[...], ...], "row_count": int,
    "truncated": bool}`, which is JSON-serialisable. `row_count` is the true number of
    rows the query returns, however many are shown; `truncated` says rows were cut.

    `sql` must pass `check_select`. `modules` are Perfetto stdlib modules to include
    first, by name, for canned SQL that needs them; they never come from the SQL text,
    so the gate stays one-statement-SELECT-only. `binary` defaults to the pinned trace
    processor (downloaded on first use).

    `max_rows=None` returns every row. That is for canned metric SQL, whose rows are
    joined across two traces in code before anything reaches the model; the agent's
    tool never passes it, so the model always gets the MAX_ROWS cap.
    """
    statement = check_select(sql)
    # The newline before `;` ends any trailing `--` comment in the statement.
    prelude = join_includes(f"CREATE TEMP VIEW {_VIEW} AS\n{statement}\n;\n", modules)
    binary = binary or resolve_trace_processor()
    trace = Path(trace)

    names = run_sql_script(
        binary,
        trace,
        prelude + f"SELECT json_group_array(name) AS {_COLUMNS} "
        f"FROM pragma_table_info('{_VIEW}');\n",
    )
    columns = _json_line(_single(_result_sets(names), _COLUMNS))

    # Positional names (c0, c1, ...) so the query's own column names need no quoting.
    positional = ", ".join(f"c{k}" for k in range(len(columns)))
    limit = "" if max_rows is None else f" LIMIT {int(max_rows)}"
    out = run_sql_script(
        binary,
        trace,
        prelude + f"WITH q({positional}) AS (SELECT * FROM {_VIEW}) "
        f"SELECT json_array({positional}) AS {_ROW} FROM q{limit};\n"
        f"SELECT count(*) AS {_COUNT} FROM {_VIEW};\n",
    )
    result_sets = _result_sets(out)
    if _ROW not in result_sets:
        raise TraceProcessorError(f"unexpected trace processor output: no {_ROW}")
    rows = [_json_line(line) for line in result_sets[_ROW]]
    row_count = int(_single(result_sets, _COUNT))
    return {
        "columns": columns,
        "rows": rows,
        "row_count": row_count,
        "truncated": row_count > len(rows),
    }


def join_includes(sql: str, modules: Sequence[str]) -> str:
    """Returns `sql` with an `INCLUDE PERFETTO MODULE` line in front for each module.

    This is how canned SQL is shown to the model (a metric's `sql_used`), so a citation
    names the modules its numbers depend on; `split_includes` turns it back into the
    `sql` and `modules` that `query_trace` takes. Raises QueryRejected for a name that
    is not a module name, so nothing but a module can ride in on one.
    """
    for module in modules:
        if not _MODULE.fullmatch(module):
            raise QueryRejected(f"not a Perfetto module name: {module!r}")
    return "".join(f"INCLUDE PERFETTO MODULE {m};\n" for m in modules) + sql


def split_includes(text: str) -> tuple[str, list[str]]:
    """Splits cited SQL into (statement, modules), the inverse of `join_includes`.

    Peels `INCLUDE PERFETTO MODULE <name>;` statements, and any whitespace or comments
    between them, off the front of `text`; the rest is returned verbatim, unchecked.
    So `query_trace(*split_includes(sql_used))` re-runs a citation exactly, and the
    statement still has to pass `check_select` there. An INCLUDE anywhere but in front
    stays in the statement, where the gate rejects it.
    """
    modules: list[str] = []
    end = 0
    while m := _LEADING_INCLUDE.match(text, end):
        modules.append(m.group(1))
        end = m.end()
    # Anything after the last INCLUDE, comments included, is the statement's own.
    return text[end:], modules


def _skip_quoted(sql: str, i: int) -> int:
    """Returns the index just past the literal or quoted identifier starting at `i`."""
    close = {"'": "'", '"': '"', "`": "`", "[": "]"}[sql[i]]
    j = i + 1
    while True:
        j = sql.find(close, j)
        if j < 0:
            raise QueryRejected(f"unterminated {sql[i]} quote")
        # SQLite escapes a quote inside a literal by doubling it ('it''s').
        if close != "]" and sql.startswith(close * 2, j):
            j += 2
            continue
        return j + 1


def _result_sets(stdout: str) -> dict[str, list[str]]:
    """Splits trace processor output into {header: value lines}, one per result set."""
    sets: dict[str, list[str]] = {}
    for block in stdout.strip("\n").split("\n\n"):
        header, *lines = block.split("\n")
        sets[header.strip('"')] = lines
    return sets


def _single(sets: dict[str, list[str]], name: str) -> str:
    lines = sets.get(name)
    if not lines or len(lines) != 1:
        raise TraceProcessorError(f"unexpected trace processor output for {name}")
    return lines[0]


def _json_line(line: str):
    """Decodes one JSON value, which trace processor prints as `"<json>"`."""
    if not (len(line) >= 2 and line[0] == '"' and line[-1] == '"'):
        raise TraceProcessorError(f"unexpected trace processor output: {line!r}")
    return json.loads(line[1:-1])
