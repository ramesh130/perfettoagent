"""query_trace: the SELECT-only gate, the 200-row cap and the true row count."""

import json

import pytest

from perfettoagent.query import (
    MAX_ROWS,
    QueryRejected,
    join_includes,
    query_trace,
    split_includes,
)
from perfettoagent.trace_processor import TraceProcessorError


@pytest.fixture
def spy_binary(tmp_path):
    """A stand-in trace processor that records that it ran, and prints nothing."""
    marker = tmp_path / "ran"
    script = tmp_path / "spy_trace_processor"
    script.write_text(f"#!/bin/sh\ncat > /dev/null\ntouch {marker}\nexit 1\n")
    script.chmod(0o755)
    return script, marker


REJECTED = [
    "DELETE FROM slice",
    "delete from slice",
    "INSERT INTO slice VALUES (1)",
    "UPDATE slice SET dur = 0",
    "DROP TABLE slice",
    "CREATE TABLE t AS SELECT 1",
    "PRAGMA table_info(slice)",
    "ATTACH DATABASE '/tmp/x.db' AS x",
    "INCLUDE PERFETTO MODULE android.startup.startups",
    "VALUES (1)",
    "SELECT 1; DELETE FROM slice",
    "SELECT 1; SELECT 2",
    "select 1;\n-- fine so far\nDROP TABLE slice;",
    "WITH x AS (SELECT 1) DELETE FROM slice",
    "WITH x AS (SELECT 1) INSERT INTO slice SELECT * FROM x",
    "/* SELECT */ DELETE FROM slice",
    "-- SELECT\nDELETE FROM slice",
    "SELECT ';' ; DELETE FROM slice",
    "SELECT 'unterminated",
    "SELECT 1 /* unterminated",
    "",
    "   -- only a comment",
    ";",
]


@pytest.mark.parametrize("sql", REJECTED)
def test_non_select_is_rejected_before_reaching_the_trace_processor(
    sql, spy_binary, tiny_trace
):
    binary, marker = spy_binary
    with pytest.raises(QueryRejected):
        query_trace(sql, tiny_trace, binary=binary)
    assert not marker.exists()


ACCEPTED = [
    "SELECT 1",
    "select 1;",
    "  \n\tSELECT 1  ;  -- trailing comment",
    "-- leading comment\nSELECT 1",
    "/* leading\n block */ select 1",
    "WITH x AS (SELECT 1 AS a) SELECT a FROM x",
    "with recursive r(n) as (select 1 union all select n + 1 from r where n < 3) "
    "select n from r",
    "SELECT 'DELETE; DROP' AS s",
    'SELECT 1 AS "delete"',
    "SELECT (SELECT 1) AS nested",
    "SELECT 1 -- no trailing newline",
]


@pytest.mark.parametrize("sql", ACCEPTED)
def test_select_and_with_pass_the_gate(sql, spy_binary, tiny_trace):
    # The control for the rejections above: these reach the trace processor, which the
    # spy records (and then fails, since it is not a real one).
    binary, marker = spy_binary
    with pytest.raises(TraceProcessorError):
        query_trace(sql, tiny_trace, binary=binary)
    assert marker.exists()


def test_module_names_are_checked(spy_binary, tiny_trace):
    binary, marker = spy_binary
    with pytest.raises(QueryRejected):
        query_trace(
            "SELECT 1", tiny_trace, modules=["x; DROP TABLE slice"], binary=binary
        )
    assert not marker.exists()


def test_rows_are_capped_and_the_true_row_count_is_reported(
    trace_processor, tiny_trace
):
    result = query_trace(
        "SELECT id FROM slice ORDER BY id", tiny_trace, binary=trace_processor
    )
    assert result["columns"] == ["id"]
    assert len(result["rows"]) == MAX_ROWS
    assert result["row_count"] == 840
    assert result["truncated"] is True
    assert result["rows"][:3] == [[0], [1], [2]]


def test_small_results_are_whole_and_not_truncated(trace_processor, tiny_trace):
    result = query_trace(
        "select count(*) as n from slice", tiny_trace, binary=trace_processor
    )
    assert result == {
        "columns": ["n"],
        "rows": [[840]],
        "row_count": 1,
        "truncated": False,
    }


def test_empty_result_keeps_its_columns(trace_processor, tiny_trace):
    result = query_trace(
        "SELECT id, name FROM slice WHERE 0", tiny_trace, binary=trace_processor
    )
    assert result == {
        "columns": ["id", "name"],
        "rows": [],
        "row_count": 0,
        "truncated": False,
    }


def test_values_survive_the_round_trip(trace_processor, tiny_trace):
    # Everything trace processor's own CSV output mangles: quotes, commas, newlines,
    # NULL, the string "[NULL]", small reals, and numbers stored as text.
    sql = """
        SELECT 'a,"b"' AS quoted, 'x' || char(10) || 'y' AS newline, NULL AS missing,
               '[NULL]' AS null_text, 1e-9 AS tiny, 1.0 / 3 AS third, '42' AS text_num,
               9007199254740993 AS big, 1 AS "odd ""name"", here", 'café ✓' AS utf8
    """
    result = query_trace(sql, tiny_trace, binary=trace_processor)
    assert result["columns"] == [
        "quoted", "newline", "missing", "null_text", "tiny", "third", "text_num", "big",
        'odd "name", here', "utf8",
    ]  # fmt: skip
    assert result["rows"] == [
        ['a,"b"', "x\ny", None, "[NULL]", 1e-9, pytest.approx(1 / 3), "42",
         9007199254740993, 1, "café ✓"],
    ]  # fmt: skip
    json.dumps(result)  # the tool result is JSON-serialisable


def test_order_by_is_kept(trace_processor, tiny_trace):
    result = query_trace(
        "WITH d AS (SELECT id, dur FROM slice) SELECT id FROM d ORDER BY dur DESC, id",
        tiny_trace,
        binary=trace_processor,
    )
    ids = [row[0] for row in result["rows"]]
    assert ids[:3] == [142, 116, 117]


def test_stdlib_modules_are_included_for_canned_sql(trace_processor, tiny_trace):
    # Without the include the stdlib table does not exist; with it the same SELECT runs.
    sql = "SELECT count(*) AS n FROM android_startups"
    with pytest.raises(TraceProcessorError, match="android_startups"):
        query_trace(sql, tiny_trace, binary=trace_processor)
    result = query_trace(
        sql, tiny_trace, modules=["android.startup.startups"], binary=trace_processor
    )
    assert result["columns"] == ["n"]


def test_sql_errors_are_reported(trace_processor, tiny_trace):
    with pytest.raises(TraceProcessorError, match="no such table: nope"):
        query_trace("SELECT * FROM nope", tiny_trace, binary=trace_processor)


def test_missing_trace_is_an_error(spy_binary, tmp_path):
    binary, marker = spy_binary
    with pytest.raises(TraceProcessorError, match="no trace file"):
        query_trace("SELECT 1", tmp_path / "missing.pftrace", binary=binary)
    assert not marker.exists()


def test_max_rows_none_returns_every_row(trace_processor, tiny_trace):
    # For canned metric SQL only; the control is the capped test above.
    result = query_trace(
        "SELECT id FROM slice ORDER BY id",
        tiny_trace,
        binary=trace_processor,
        max_rows=None,
    )
    assert len(result["rows"]) == result["row_count"] == 840
    assert result["truncated"] is False


def test_cited_sql_splits_back_into_statement_and_modules():
    statement = "-- what it counts\nSELECT count(*) AS n FROM android_startups"
    modules = ["android.startup.startups", "slices.with_context"]
    cited = join_includes(statement, modules)
    assert cited == (
        "INCLUDE PERFETTO MODULE android.startup.startups;\n"
        "INCLUDE PERFETTO MODULE slices.with_context;\n" + statement
    )
    assert split_includes(cited) == (statement, modules)


@pytest.mark.parametrize(
    ("text", "statement", "modules"),
    [
        ("SELECT 1", "SELECT 1", []),
        ("include perfetto module a.b;SELECT 1", "SELECT 1", ["a.b"]),
        ("-- note\n  INCLUDE PERFETTO MODULE a;\n\nSELECT 1", "\nSELECT 1", ["a"]),
        # Only a leading INCLUDE is peeled; a later one stays for the gate to reject.
        (
            "SELECT 1; INCLUDE PERFETTO MODULE a;",
            "SELECT 1; INCLUDE PERFETTO MODULE a;",
            [],
        ),
        # What follows the INCLUDEs comes back as it is, for the gate to judge.
        (
            "INCLUDE PERFETTO MODULE a; DROP x;",
            "DROP x;",
            ["a"],
        ),
    ],
)
def test_split_includes_peels_only_leading_includes(text, statement, modules):
    assert split_includes(text) == (statement, modules)


def test_a_split_citation_still_goes_through_the_gate(spy_binary, tiny_trace):
    binary, marker = spy_binary
    statement, modules = split_includes("INCLUDE PERFETTO MODULE a;\nDELETE FROM slice")
    with pytest.raises(QueryRejected):
        query_trace(statement, tiny_trace, modules=modules, binary=binary)
    assert not marker.exists()


def test_cited_sql_reruns_through_query_trace(trace_processor, tiny_trace):
    cited = join_includes(
        "SELECT count(*) AS n FROM android_startups", ["android.startup.startups"]
    )
    statement, modules = split_includes(cited)
    result = query_trace(statement, tiny_trace, modules=modules, binary=trace_processor)
    assert result["columns"] == ["n"]
