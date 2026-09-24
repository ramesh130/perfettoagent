"""The thread and memory metrics, main_thread_blocked_ms, gc_time_ms, binder_wait_ms
and native_unfreed_bytes, on the jank fixtures.

The fixtures are five captures of one scroll-and-tap scenario (conftest.jank_traces): a
baseline, a rerun of the baseline's build, and three captures after three different
changes. The known answers below are what the pinned trace processor (58.2) returns on
them. None of these metrics needs a baseline, so each is computed on each capture alone,
and against the baseline where a change is asserted.
"""

import json

import pytest

import perfettoagent.metrics as metrics
from perfettoagent.metrics import compute_metric, list_metrics
from perfettoagent.query import query_trace, split_includes

BLOCKED = "main_thread_blocked_ms"
GC = "gc_time_ms"
BINDER = "binder_wait_ms"
NATIVE = "native_unfreed_bytes"
THREAD_METRICS = (BLOCKED, GC, BINDER)

# The stdlib modules each metric stands on, in the order its sql_used includes them.
MODULES = {
    BLOCKED: ["android.frames.timeline"],
    GC: ["android.frames.timeline", "android.garbage_collection"],
    BINDER: ["android.binder", "android.frames.timeline"],
    NATIVE: [],
}

# What a meaningful change is: more than the run-to-run spread of the metric over clean
# captures of one build. ADR-0013 measured it over all six clean captures of the jank
# scenario (the fixtures' baseline and rerun among them), over about an hour: the
# largest clean value minus the smallest.
CLEAN_SPREAD = {
    BLOCKED: 29.67,  # 9.25-38.92 ms
    GC: 256.53,  # 171.96-428.49 ms
    BINDER: 133.99,  # 214.33-348.32 ms
}

# Values in ms are nanosecond counts / 1e6, so six decimals are exact.
NS = 1e-6

# Each fixture's known answer, on that capture alone.
KNOWN = {
    "baseline": {BLOCKED: 25.284169, GC: 258.575876, BINDER: 214.334244},
    "rerun": {BLOCKED: 9.254460, GC: 171.956002, BINDER: 227.248289},
    "current_b": {BLOCKED: 46.368412, GC: 10356.094546, BINDER: 145.104664},
    "current_c": {BLOCKED: 73.839125, GC: 13632.500926, BINDER: 907.828238},
    "current_d": {BLOCKED: 731.530503, GC: 436.083127, BINDER: 256.502654},
}
CAPTURES = tuple(KNOWN)

# GC time as the scenario's own report gives it (superPlayer PR #392's capture table,
# from devicelab's jank/sql/gc.sql: every top-level `*GC` slice on the app's
# HeapTaskDaemon, in whole ms). Only the recorded output is copied in; nothing here runs
# it, so this checks the known answers against a second derivation made by hand.
DEVICELAB_GC_MS = {
    "baseline": 259,
    "rerun": 172,
    "current_b": 10356,
    "current_c": 13632,
    "current_d": 436,
}


@pytest.fixture(scope="module")
def alone(trace_processor, jank_traces) -> dict:
    """{(metric, capture): compute_metric on that capture alone}."""
    return {
        (name, capture): compute_metric(
            name, current=getattr(jank_traces, capture), binary=trace_processor
        )
        for name in THREAD_METRICS
        for capture in CAPTURES
    }


def _delta(alone, name, capture):
    """The change from the baseline, from the two single-trace results."""
    return alone[(name, capture)]["current"] - alone[(name, "baseline")]["current"]


def test_the_four_are_listed_without_a_baseline():
    entries = {m["name"]: m for m in list_metrics()}
    units = {BLOCKED: "ms", GC: "ms", BINDER: "ms", NATIVE: "bytes"}
    for name, unit in units.items():
        entry = entries[name]
        assert (entry["unit"], entry["requires_baseline"]) == (unit, False), name
        assert "key" not in entry
        # The model choosing a metric is told when it reads NULL.
        assert "NULL if" in entry["description"], name


def test_the_app_is_the_frame_metrics_app():
    # The three thread metrics choose the app with the frame metrics' own query, kept in
    # step by hand: this catches one being changed without the others.
    library = metrics._load_library()
    shared = {
        _frames_query(library[n].sql) for n in (*THREAD_METRICS, "jank_frames_pct")
    }
    assert len(shared) == 1


@pytest.mark.parametrize("name", THREAD_METRICS)
def test_known_answers(alone, name):
    for capture in CAPTURES:
        result = alone[(name, capture)]
        assert result["current"] == pytest.approx(KNOWN[capture][name], abs=NS)
        assert (result["baseline"], result["delta"]) == (None, None)
        assert "no_data" not in result
        statement, modules = split_includes(result["sql_used"])
        assert modules == MODULES[name]
    # What the agent's tool returns must be JSON-serialisable.
    json.dumps(list(alone.values()))


def test_a_baseline_gives_the_delta(trace_processor, jank_traces, alone):
    # Not needed, but taken when given: the same numbers, and their difference.
    result = compute_metric(
        BLOCKED,
        baseline=jank_traces.baseline,
        current=jank_traces.current_d,
        binary=trace_processor,
    )
    assert result["baseline"] == alone[(BLOCKED, "baseline")]["current"]
    assert result["current"] == alone[(BLOCKED, "current_d")]["current"]
    assert result["delta"] == pytest.approx(_delta(alone, BLOCKED, "current_d"))


def test_gc_matches_the_scenarios_own_report():
    for capture, ms in DEVICELAB_GC_MS.items():
        # Within a ms: the table drops the fraction (13632.5 is written 13632).
        assert abs(KNOWN[capture][GC] - ms) < 1, capture


def test_main_thread_blocked_shows_the_change_in_current_d(alone):
    # current_d's main thread blocked for 706.2 ms more than the baseline's, 23.8 times
    # the clean spread: more than twice the spread leaves room for a noisier baseline.
    assert _delta(alone, BLOCKED, "current_d") > 2 * CLEAN_SPREAD[BLOCKED]
    # And it dwarfs what the other two changes moved it by (+21.1 and +48.6 ms; the
    # second is above the clean spread, 1.6 times it, ADR-0013): ten times over.
    for other in ("current_b", "current_c"):
        assert _delta(alone, BLOCKED, "current_d") > 10 * _delta(alone, BLOCKED, other)


def test_gc_time_shows_the_change_in_current_b(alone):
    # current_b's collector ran 10.1 s longer than the baseline's, 39 times the clean
    # spread. current_c's ran 13.4 s longer too (it allocates as well, ADR-0013).
    assert _delta(alone, GC, "current_b") > 2 * CLEAN_SPREAD[GC]
    # current_d's change is not in GC time: its delta, 177.5 ms, is inside the spread.
    assert abs(_delta(alone, GC, "current_d")) < CLEAN_SPREAD[GC]


def test_the_clean_pair_shows_no_meaningful_delta(alone):
    # Control: the same build captured twice moves each metric by less than its clean
    # spread, and by less than a tenth of the change it detects.
    for name in THREAD_METRICS:
        assert abs(_delta(alone, name, "rerun")) < CLEAN_SPREAD[name], name
    assert (
        abs(_delta(alone, BLOCKED, "rerun")) < _delta(alone, BLOCKED, "current_d") / 10
    )
    assert abs(_delta(alone, GC, "rerun")) < _delta(alone, GC, "current_b") / 10


def _frames_query(sql: str) -> str:
    """The SQL from WITH to the end of the `frames` CTE, which the files share."""
    start = sql.index("WITH\n  window_frames AS (")
    end = sql.index("\n  )", sql.index("\n  frames AS (", start))
    return sql[start:end]


@pytest.mark.parametrize("capture", ["baseline", "current_d"])
def test_main_thread_blocked_is_aggregated_from_every_state(
    alone, trace_processor, jank_traces, capture
):
    # An independent aggregation: the main thread found by its tid (the process's pid),
    # not from the frame timeline, and the overlap of its blocked states with its
    # top-level slices taken here, so the SQL that intersects them is checked.
    trace = getattr(jank_traces, capture)
    main = (
        "SELECT t.utid FROM thread AS t JOIN process AS p USING (upid) "
        "WHERE p.name = 'com.superplayer.demo' AND t.tid = p.pid"
    )
    states = _rows(
        f"SELECT ts, dur, state FROM thread_state WHERE utid IN ({main}) AND dur > 0",
        trace,
        trace_processor,
    )
    tops = _rows(
        "SELECT s.ts, s.dur, s.name FROM slice AS s "
        "JOIN thread_track AS t ON t.id = s.track_id "
        f"WHERE t.utid IN ({main}) AND s.depth = 0 AND s.dur > 0",
        trace,
        trace_processor,
    )
    work = [(ts, ts + d) for ts, d, name in tops if "Choreographer#doFrame" not in name]
    blocked = [
        (ts, ts + d) for ts, d, state in states if state not in ("Running", "R", "R+")
    ]
    overlap = sum(
        max(0, min(b_end, w_end) - max(b_start, w_start))
        for b_start, b_end in blocked
        for w_start, w_end in work
        if b_start < w_end and w_start < b_end
    )
    assert alone[(BLOCKED, capture)]["current"] == pytest.approx(overlap / 1e6, abs=NS)


@pytest.mark.parametrize("capture", ["baseline", "current_b"])
def test_gc_and_binder_are_the_raw_slices(alone, trace_processor, jank_traces, capture):
    # The stdlib's tables, checked against the slices they are built from: the app's
    # top-level collections on its HeapTaskDaemon, and the main thread's binder
    # transaction slices, summed here.
    trace = getattr(jank_traces, capture)
    app = "SELECT upid FROM process WHERE name = 'com.superplayer.demo'"
    slices = _rows(
        "SELECT s.name, s.dur, s.depth, t.name, t.tid = p.pid FROM slice AS s "
        "JOIN thread_track AS tt ON tt.id = s.track_id "
        "JOIN thread AS t USING (utid) JOIN process AS p USING (upid) "
        f"WHERE p.upid IN ({app})",
        trace,
        trace_processor,
    )
    # As devicelab's gc.sql counts them: every top-level `*GC` on HeapTaskDaemon.
    gc = sum(
        dur
        for name, dur, depth, thread, _ in slices
        if thread == "HeapTaskDaemon" and depth == 0 and name.endswith("GC")
    )
    binder = sum(
        dur
        for name, dur, _, _, is_main in slices
        if is_main and name == "binder transaction"
    )
    assert alone[(GC, capture)]["current"] == pytest.approx(gc / 1e6, abs=NS)
    assert alone[(BINDER, capture)]["current"] == pytest.approx(binder / 1e6, abs=NS)


def _rows(sql, trace, binary):
    return query_trace(sql, trace, binary=binary, max_rows=None)["rows"]


def test_sql_used_reproduces_every_cited_number(alone, trace_processor, jank_traces):
    # What the verifier does: split the citation, re-run it, get the same number.
    for name in THREAD_METRICS:
        result = alone[(name, "current_d")]
        statement, modules = split_includes(result["sql_used"])
        rerun = query_trace(
            statement, jank_traces.current_d, modules=modules, binary=trace_processor
        )
        assert rerun["rows"] == [[result["current"]]]


# --- No data: NULL with a reason, never 0 (ADR-0014). -------------------------------


@pytest.mark.parametrize("capture", CAPTURES)
def test_native_unfreed_reads_no_data_on_every_fixture(
    trace_processor, jank_traces, capture
):
    # No fixture was captured with heapprofd, so none has a native heap profile: the
    # metric says so instead of reporting 0 bytes unfreed.
    result = compute_metric(
        NATIVE, current=getattr(jank_traces, capture), binary=trace_processor
    )
    assert (result["baseline"], result["current"], result["delta"]) == (
        None,
        None,
        None,
    )
    assert "heapprofd" in result["no_data"]["current"]
    assert list(result["no_data"]) == ["current"]
    # And the citation re-runs to that same NULL, a row the verifier can find.
    statement, modules = split_includes(result["sql_used"])
    assert modules == []
    rerun = query_trace(
        statement, getattr(jank_traces, capture), binary=trace_processor
    )
    assert rerun["rows"] == [[None]]


def test_no_data_names_each_side_that_lacks_it(trace_processor, jank_traces):
    result = compute_metric(
        NATIVE,
        baseline=jank_traces.baseline,
        current=jank_traces.current_d,
        binary=trace_processor,
    )
    assert sorted(result["no_data"]) == ["baseline", "current"]
    assert result["delta"] is None


@pytest.mark.parametrize("name", [*THREAD_METRICS, NATIVE])
def test_a_trace_without_their_data_reads_no_data(trace_processor, tiny_trace, name):
    # The tiny trace has no frame timeline, so no app, and no heap profile.
    result = compute_metric(name, current=tiny_trace, binary=trace_processor)
    assert result["current"] is None
    assert result["no_data"] == {"current": metrics._load_library()[name].no_data}
    json.dumps(result)
