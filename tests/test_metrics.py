"""The metric library: list_metrics, compute_metric, and re-running their sql_used."""

import json

import pytest

import perfettoagent.metrics as metrics
from perfettoagent.metrics import (
    BREAKDOWN_ROWS,
    MetricError,
    UnknownMetric,
    compute_metric,
    list_metrics,
)
from perfettoagent.query import query_trace, split_includes

HEAP = "heap_growth_objects_by_class"
HEAP_MODULE = (
    "INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;"
)


def test_list_metrics_describes_the_library():
    entries = {m["name"]: m for m in list_metrics()}
    assert entries[HEAP] == {
        "name": HEAP,
        "description": entries[HEAP]["description"],
        "unit": "objects",
        "requires_baseline": True,
        "key": "class",
    }
    assert "Reachable Java objects" in entries[HEAP]["description"]
    json.dumps(list_metrics())


def test_unknown_metric_is_a_clear_error(tiny_trace):
    with pytest.raises(UnknownMetric, match=f"no metric named 'nope'.*{HEAP}"):
        compute_metric("nope", current=tiny_trace)


def test_a_metric_that_needs_a_baseline_refuses_to_run_without_one(tiny_trace):
    with pytest.raises(MetricError, match="needs a baseline"):
        compute_metric(HEAP, current=tiny_trace)


# --- Adding a metric is adding a .sql file: the plumbing below is unchanged. ---------


def _write(directory, name, text):
    (directory / f"{name}.sql").write_text(text)


@pytest.fixture
def library(tmp_path, monkeypatch):
    """A metric library of our own, in place of the shipped one."""
    monkeypatch.setattr(metrics, "METRIC_DIR", tmp_path)
    return tmp_path


def test_a_scalar_metric_is_one_sql_file(library, trace_processor, tiny_trace):
    _write(
        library,
        "slice_count",
        "-- @description: Slices in the trace.\n"
        "-- @unit: slices\n"
        "-- @requires_baseline: false\n"
        "SELECT count(*) AS value FROM slice\n",
    )
    assert [m["name"] for m in list_metrics()] == ["slice_count"]
    result = compute_metric("slice_count", current=tiny_trace, binary=trace_processor)
    assert result == {
        "name": "slice_count",
        "unit": "slices",
        "baseline": None,
        "current": 840,
        "delta": None,
        "sql_used": "SELECT count(*) AS value FROM slice\n",
    }
    # With a baseline given anyway, the delta is computed.
    both = compute_metric(
        "slice_count", baseline=tiny_trace, current=tiny_trace, binary=trace_processor
    )
    assert (both["baseline"], both["current"], both["delta"]) == (840, 840, 0)


def test_a_keyed_metric_is_one_sql_file(library, trace_processor, tiny_trace):
    _write(
        library,
        "slices_by_depth",
        "-- @description: Slices per nesting depth.\n"
        "-- @unit: slices\n"
        "-- @requires_baseline: false\n"
        "-- @key: depth\n"
        # process_slice comes from the module, so it must be included to run.
        "INCLUDE PERFETTO MODULE slices.with_context;\n"
        "SELECT depth AS key, count(*) AS value FROM process_slice GROUP BY depth\n",
    )
    result = compute_metric(
        "slices_by_depth", current=tiny_trace, binary=trace_processor
    )
    assert result["sql_used"].startswith(
        "INCLUDE PERFETTO MODULE slices.with_context;\n"
    )
    breakdown = result["breakdown"]
    assert breakdown["key"] == "depth"
    # No baseline: ranked by current value, and the headline is the sum over keys.
    currents = [row["current"] for row in breakdown["rows"]]
    assert currents == sorted(currents, reverse=True)
    assert result["current"] == sum(currents) == 840
    assert all(row["baseline"] is None for row in breakdown["rows"])


def test_a_null_value_is_reported_as_no_data(library, trace_processor, tiny_trace):
    # NULL is not 0: the result names each side whose value is NULL, and why, from the
    # file's @no_data line, or a generic reason for a file without one (ADR-0014).
    header = "-- @description: x\n-- @unit: y\n-- @requires_baseline: false\n"
    select = "SELECT (SELECT sum(dur) FROM slice WHERE name = 'absent') AS value\n"
    _write(library, "with_reason", header + "-- @no_data: nothing absent\n" + select)
    _write(library, "without_reason", header + select)

    result = compute_metric(
        "with_reason", baseline=tiny_trace, current=tiny_trace, binary=trace_processor
    )
    assert (result["baseline"], result["current"], result["delta"]) == (None,) * 3
    assert result["no_data"] == {
        "baseline": "nothing absent",
        "current": "nothing absent",
    }
    alone = compute_metric("without_reason", current=tiny_trace, binary=trace_processor)
    assert alone["no_data"] == {"current": metrics._NO_DATA}
    # The listing is unchanged by it: the description says when a metric reads NULL.
    assert "no_data" not in list_metrics()[0]


def test_a_value_carries_no_no_data(library, trace_processor, tiny_trace):
    _write(
        library,
        "zero",
        "-- @description: x\n-- @unit: y\n-- @requires_baseline: false\n"
        "-- @no_data: never\n"
        "SELECT 0 AS value\n",
    )
    result = compute_metric("zero", current=tiny_trace, binary=trace_processor)
    # A measured 0 is a value, and the side with no trace given is not missing data.
    assert result["current"] == 0
    assert "no_data" not in result


@pytest.mark.parametrize(
    ("text", "error"),
    [
        ("SELECT 1 AS value\n", "@description"),
        (
            "-- @description: x\n-- @unit: y\n-- @requires_baseline: maybe\n"
            "SELECT 1 AS value\n",
            "requires_baseline",
        ),
        (
            "-- @description: x\n-- @unit: y\n-- @requires_baseline: no\n"
            "-- @colour: red\nSELECT 1 AS value\n",
            "@colour",
        ),
        (
            "-- @description: x\n-- @unit: y\n-- @requires_baseline: false\n"
            "DELETE FROM slice\n",
            "SELECT",
        ),
    ],
)
def test_a_malformed_metric_file_is_refused_when_the_library_loads(
    library, text, error
):
    _write(library, "bad", text)
    with pytest.raises(MetricError, match=error):
        list_metrics()


# --- The first real metric, on the fixture pair. -------------------------------------


@pytest.fixture(scope="module")
def heap_result(trace_processor, heap_a_pair):
    baseline, current = heap_a_pair
    return compute_metric(
        HEAP, baseline=baseline, current=current, binary=trace_processor
    )


def test_heap_growth_on_fixture_pair(heap_result):
    assert heap_result["unit"] == "objects"
    # Every reachable object in each trace's heap dump.
    assert heap_result["baseline"] == 423576
    assert heap_result["current"] == 434935
    assert heap_result["delta"] == 11359
    assert heap_result["sql_used"].startswith(HEAP_MODULE + "\n")

    breakdown = heap_result["breakdown"]
    assert breakdown["key"] == "class"
    assert len(breakdown["rows"]) == BREAKDOWN_ROWS
    # Classes whose reachable count changed at all, of about 43k in each dump.
    assert breakdown["row_count"] == 616
    assert breakdown["truncated"] is True
    deltas = [r["delta"] for r in breakdown["rows"]]
    assert deltas == sorted(deltas, reverse=True)
    rows = {
        r["key"]: (r["baseline"], r["current"], r["delta"]) for r in breakdown["rows"]
    }
    # The largest growth is in framework and library classes ...
    assert [r["key"] for r in breakdown["rows"][:3]] == [
        "java.lang.String",
        "androidx.media3.exoplayer.hls.playlist.HlsMediaPlaylist$Segment",
        "java.lang.Object[]",
    ]
    assert rows["java.lang.String"] == (119160, 122363, 3203)
    # ... and below it, seven classes grew by exactly the same count, two of the app's
    # own among them: rows that sit within the cap, where the model can see them.
    assert sum(1 for _, _, delta in rows.values() if delta == 137) == 7
    assert rows["com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1"] == (15, 152, 137)
    assert rows["com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0"] == (
        27,
        164,
        137,
    )
    json.dumps(heap_result)


def test_heap_growth_known_answer_matches_the_raw_tables(
    heap_result, trace_processor, heap_a_pair
):
    # An independent count: the raw heap graph tables and their own reachable flag,
    # not the stdlib aggregation, for the headline and for every row shown. The SQL,
    # quoting included, is written out here rather than built with the code under
    # test, so that a bug there cannot hide in both.
    last_dump = (
        "o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object)"
    )
    shown = heap_result["breakdown"]["rows"]
    names = ", ".join("'" + r["key"].replace("'", "''") + "'" for r in shown)
    for trace, side in zip(heap_a_pair, ("baseline", "current"), strict=True):
        total = query_trace(
            "SELECT count(*) FROM heap_graph_object o "
            f"WHERE o.reachable AND {last_dump}",
            trace,
            binary=trace_processor,
        )
        assert total["rows"] == [[heap_result[side]]]
        per_class = query_trace(
            "SELECT c.name, count(*) FROM heap_graph_object o "
            "JOIN heap_graph_class c ON c.id = o.type_id "
            f"WHERE o.reachable AND {last_dump} AND c.name IN ({names}) "
            "GROUP BY c.name",
            trace,
            binary=trace_processor,
        )
        assert dict(per_class["rows"]) == {r["key"]: r[side] for r in shown if r[side]}


def test_heap_growth_control_is_zero(trace_processor, heap_a_pair):
    # The same trace on both sides: no growth, so the known answer above is not vacuous.
    baseline, _ = heap_a_pair
    result = compute_metric(
        HEAP, baseline=baseline, current=baseline, binary=trace_processor
    )
    assert result["delta"] == 0
    assert result["baseline"] == result["current"] == 423576
    assert result["breakdown"]["rows"] == []
    assert result["breakdown"]["row_count"] == 0


def test_sql_used_reproduces_every_cited_number(
    heap_result, trace_processor, heap_a_pair
):
    # What the verifier does: split the citation, re-run it, get the same number.
    def rerun(cited, trace):
        statement, modules = split_includes(cited)
        return query_trace(statement, trace, modules=modules, binary=trace_processor)

    for trace, side in zip(heap_a_pair, ("baseline", "current"), strict=True):
        assert rerun(heap_result["sql_used"], trace)["rows"] == [[heap_result[side]]]
        row = heap_result["breakdown"]["rows"][0]
        assert HEAP_MODULE in row["sql_used"]
        assert rerun(row["sql_used"], trace)["rows"] == [[row["key"], row[side]]]


def test_a_breakdown_citation_reads_zero_where_its_key_is_absent(
    heap_result, trace_processor, tiny_trace
):
    # A class that is new in the current trace must still re-run to a row, 0, on the
    # baseline; a trace with no heap dump at all stands in for that baseline here.
    row = heap_result["breakdown"]["rows"][0]
    statement, modules = split_includes(row["sql_used"])
    result = query_trace(statement, tiny_trace, modules=modules, binary=trace_processor)
    assert result["rows"] == [[row["key"], 0]]
