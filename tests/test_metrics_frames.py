"""The frame metrics, jank_frames_pct, frame_p95_ms, frame_p99_ms and
frame_ui_time_p95_ms, on the jank fixtures.

The fixtures are four captures of one scroll-and-tap scenario (conftest.jank_traces): a
baseline, a rerun of the baseline's build, and two captures after two different
changes, `current_b` and `current_c`. The known answers below are what the pinned trace
processor (58.2) returns on them.
"""

import json
import math
from collections import Counter

import pytest

import perfettoagent.metrics as metrics
from perfettoagent.metrics import compute_metric, list_metrics
from perfettoagent.query import query_trace, split_includes

JANK = "jank_frames_pct"
P95 = "frame_p95_ms"
P99 = "frame_p99_ms"
UI_P95 = "frame_ui_time_p95_ms"
FRAME_METRICS = (JANK, P95, P99, UI_P95)

# The stdlib module every frame metric stands on, and the first line of its sql_used.
MODULE = "android.frames.timeline"
INCLUDE = f"INCLUDE PERFETTO MODULE {MODULE};\n"

# What a meaningful change is: more than the run-to-run spread of the metric over clean
# captures of one build. ADR-0011 measured it over all six clean captures of the jank
# scenario (the fixtures' baseline and rerun among them), over about an hour: the
# largest clean value minus the smallest.
CLEAN_SPREAD = {
    JANK: 17.60,  # 37.14-54.73 %
    P95: 13.69,  # 67.81-81.50 ms
    P99: 38.73,  # 115.78-154.50 ms
    UI_P95: 6.90,  # 32.53-39.43 ms
}

# Values in ms are nanosecond counts / 1e6, so six decimals are exact.
NS = 1e-6

# Each fixture's known answer. Jank is a count of frames over the frames counted, so it
# is written as that fraction.
KNOWN = {
    "baseline": {
        JANK: 100 * 370 / 676,
        P95: 81.499417,
        P99: 154.500750,
        UI_P95: 37.952167,
    },
    "rerun": {
        JANK: 100 * 308 / 730,
        P95: 72.295959,
        P99: 123.526125,
        UI_P95: 36.633750,
    },
    "current_b": {
        JANK: 100 * 284 / 427,
        P95: 87.732584,
        P99: 138.026042,
        UI_P95: 60.259500,
    },
    "current_c": {
        JANK: 100 * 1317 / 1640,
        P95: 92.735583,
        P99: 124.060833,
        UI_P95: 69.289541,
    },
}

# The same captures as read by the scenario's own report (superPlayer devicelab's
# jank/sql/frames.sql and frame_work.sql, PR #392's capture table, to one decimal).
# Those queries read the raw timeline table and the doFrame slices without this
# library's stdlib tables. Only their recorded output is copied in (nothing here runs
# them), so this checks the known answers against a second derivation made by hand.
DEVICELAB = {
    "baseline": {JANK: 54.7, P95: 81.5, P99: 154.5, UI_P95: 38.0},
    "rerun": {JANK: 42.2, P95: 72.3, P99: 123.5, UI_P95: 36.6},
    "current_b": {JANK: 66.5, P95: 87.7, P99: 138.0, UI_P95: 60.3},
    "current_c": {JANK: 80.3, P95: 92.7, P99: 124.1, UI_P95: 69.3},
}

# The captures compared against `baseline`.
OTHERS = ("rerun", "current_b", "current_c")


@pytest.fixture(scope="module")
def results(trace_processor, jank_traces) -> dict:
    """{(metric, other): compute_metric of `other` against the baseline}."""
    return {
        (name, other): compute_metric(
            name,
            baseline=jank_traces.baseline,
            current=getattr(jank_traces, other),
            binary=trace_processor,
        )
        for name in FRAME_METRICS
        for other in OTHERS
    }


def test_every_frame_metric_is_listed():
    entries = {m["name"]: m for m in list_metrics()}
    for name in FRAME_METRICS:
        entry = entries[name]
        unit = "percent" if name == JANK else "ms"
        assert (entry["unit"], entry["requires_baseline"]) == (unit, True)
        assert "key" not in entry
        # The model choosing a metric is told which frames count.
        assert "window" in entry["description"]
    assert "App Deadline Missed" in entries[JANK]["description"]
    for name in (P95, P99, UI_P95):
        assert "nearest rank" in entries[name]["description"]


def test_the_frame_metrics_share_one_frame_set():
    # The four files choose the frames and the app with one query, kept in step by
    # hand: this catches one being changed without the others.
    library = metrics._load_library()
    assert len({_through_frames_cte(library[n].sql) for n in FRAME_METRICS}) == 1
    # And p95 and p99 are one query at two ranks.
    assert library[P95].sql.replace("n * 95 + 99", "n * 99 + 99") == library[P99].sql


@pytest.mark.parametrize("name", FRAME_METRICS)
def test_known_answers(results, name):
    for other in OTHERS:
        result = results[(name, other)]
        assert result["sql_used"].startswith(INCLUDE)
        assert result["baseline"] == pytest.approx(KNOWN["baseline"][name], abs=NS)
        assert result["current"] == pytest.approx(KNOWN[other][name], abs=NS)
    # What the agent's tool returns must be JSON-serialisable.
    json.dumps(list(results.values()))


def test_the_known_answers_match_the_scenarios_own_report():
    for side, expected in DEVICELAB.items():
        for name, value in expected.items():
            assert round(KNOWN[side][name], 1) == value, (side, name)


def test_both_changes_show_in_ui_time(results):
    # Each change's UI-time p95 grew by more than twice the whole clean spread: past any
    # clean capture from any other, with room to spare for a noisier baseline. They are
    # 22.3 ms and 31.3 ms, 3.2 and 4.5 times the spread.
    for other in ("current_b", "current_c"):
        assert results[(UI_P95, other)]["delta"] > 2 * CLEAN_SPREAD[UI_P95]


def test_one_change_shows_in_jank(results):
    # current_c's app-jank share grew by 25.6 points, more than the clean spread, but
    # only 1.45 times it: a weaker signal than UI time (ADR-0011).
    assert results[(JANK, "current_c")]["delta"] > CLEAN_SPREAD[JANK]


def test_what_the_timeline_metrics_do_not_separate(results):
    # Recorded so that nothing claims them (ADR-0011): on these captures neither change
    # moves frame_p95_ms or frame_p99_ms by more than its clean spread, and current_b
    # moves jank_frames_pct by 11.8 points, less than the clean pair's own 12.5.
    for other in ("current_b", "current_c"):
        assert abs(results[(P95, other)]["delta"]) < CLEAN_SPREAD[P95]
        assert abs(results[(P99, other)]["delta"]) < CLEAN_SPREAD[P99]
    jank_b = results[(JANK, "current_b")]["delta"]
    assert jank_b < CLEAN_SPREAD[JANK]
    assert jank_b < abs(results[(JANK, "rerun")]["delta"])


def test_the_clean_pair_shows_no_meaningful_delta(results):
    # Control: the same build captured twice moves each metric by less than its clean
    # spread, so the deltas above are not what any two captures differ by.
    for name in FRAME_METRICS:
        assert abs(results[(name, "rerun")]["delta"]) < CLEAN_SPREAD[name], name
    # And small beside the changes UI time detects: the spread above is measured over
    # captures that include this pair, so it is also checked against the smaller change.
    # A tenth leaves room for a noisier clean pair (the spread is a third of the change)
    # while no clean pair could pass for the change. It is 1.3 ms here.
    smaller = min(results[(UI_P95, o)]["delta"] for o in ("current_b", "current_c"))
    assert abs(results[(UI_P95, "rerun")]["delta"]) < smaller / 10


def _through_frames_cte(sql: str) -> str:
    """The SQL up to the end of the `frames` CTE, which the four files share."""
    start = sql.find("\n  frames AS (")
    assert start >= 0, "a frame metric has no `frames` CTE at the expected indent"
    return sql[: sql.index("\n  )", start)]


def _nearest_rank(values, p):
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * p / 100) - 1]


@pytest.mark.parametrize("side", ["baseline", "current_c"])
def test_the_metrics_are_aggregated_from_every_frame(
    results, trace_processor, jank_traces, side
):
    # An independent aggregation: every frame-layer row of the stdlib table, and the
    # filtering, app choice, share and percentiles done here, so the SQL that ranks and
    # filters is checked, not trusted.
    trace = getattr(jank_traces, side)
    rows = query_trace(
        "SELECT f.upid, f.ui_thread_utid, f.layer_name, a.id, a.dur, a.jank_type "
        "FROM android_frames_layers AS f "
        "LEFT JOIN actual_frame_timeline_slice AS a "
        "ON a.id = f.actual_frame_timeline_id",
        trace,
        modules=[MODULE],
        binary=trace_processor,
        max_rows=None,
    )["rows"]
    window = {
        frame_id: (upid, utid, dur, jank)
        for upid, utid, layer, frame_id, dur, jank in rows
        if layer is not None and "SurfaceView" not in layer and dur > 0
    }
    # The process with the most frames, ties to the lowest upid, as the SQL breaks them.
    counts = Counter(upid for upid, _, _, _ in window.values())
    app = min(counts, key=lambda upid: (-counts[upid], upid))
    frames = [f for f in window.values() if f[0] == app]
    durs = [dur for _, _, dur, _ in frames]
    janky = [jank for _, _, _, jank in frames if "App Deadline Missed" in jank]
    ui_threads = {utid for _, utid, _, _ in frames}
    do_frames = query_trace(
        "SELECT d.ui_thread_utid, s.dur "
        "FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)",
        trace,
        modules=[MODULE],
        binary=trace_processor,
        max_rows=None,
    )["rows"]
    ui_times = [dur for utid, dur in do_frames if utid in ui_threads]

    expected = {
        JANK: 100 * len(janky) / len(frames),
        P95: _nearest_rank(durs, 95) / 1e6,
        P99: _nearest_rank(durs, 99) / 1e6,
        UI_P95: _nearest_rank(ui_times, 95) / 1e6,
    }
    column = "baseline" if side == "baseline" else "current"
    for name, value in expected.items():
        assert results[(name, "current_c")][column] == pytest.approx(value), name


def test_sql_used_reproduces_every_cited_number(results, trace_processor, jank_traces):
    # What the verifier does: split the citation, re-run it, get the same number.
    for name in FRAME_METRICS:
        result = results[(name, "current_b")]
        statement, modules = split_includes(result["sql_used"])
        assert modules == [MODULE]
        for trace, side in (
            (jank_traces.baseline, "baseline"),
            (jank_traces.current_b, "current"),
        ):
            rerun = query_trace(
                statement, trace, modules=modules, binary=trace_processor
            )
            assert rerun["rows"] == [[result[side]]]


@pytest.mark.parametrize("name", FRAME_METRICS)
def test_a_trace_without_frames_reads_null(trace_processor, tiny_trace, name):
    # One row whose value is NULL, not an error and not 0: a trace with no window frame
    # on the frame timeline, as the tiny trace has none, has no frame metric, and the
    # delta against it is None.
    result = compute_metric(
        name, baseline=tiny_trace, current=tiny_trace, binary=trace_processor
    )
    assert (result["baseline"], result["current"], result["delta"]) == (
        None,
        None,
        None,
    )
