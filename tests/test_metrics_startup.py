"""The startup metrics, startup_ttid_ms and startup_ttfd_ms, on the startup fixtures.

The fixtures are three captures of 20 cold starts each (conftest.startup_a_trio): a
baseline, a current capture after a change, and a rerun of the baseline's build. The
known answers below are what the pinned trace processor (58.2) returns on them.
"""

import json
import math

import pytest

import perfettoagent.metrics as metrics
from perfettoagent.metrics import compute_metric, list_metrics
from perfettoagent.query import query_trace, split_includes

TTID = "startup_ttid_ms"
TTFD = "startup_ttfd_ms"

# The stdlib modules both metrics stand on, and the first lines of their sql_used.
MODULES = ["android.startup.startups", "android.startup.time_to_display"]
INCLUDES = "".join(f"INCLUDE PERFETTO MODULE {m};\n" for m in MODULES)

# What a meaningful change is: more than the run-to-run spread of the metric over clean
# captures of one build. ADR-0009 measured it over all five clean captures of the
# startup scenario (the fixtures' baseline and rerun among them): their TTID p50s span
# 345.47-450.71 ms and their TTFD p50s span 2077.31-2687.14 ms, over about an hour.
TTID_CLEAN_SPREAD_MS = 105.24
TTFD_CLEAN_SPREAD_MS = 609.83

# Values are nanosecond counts / 1e6, so six decimals are exact.
NS = 1e-6


@pytest.fixture(scope="module")
def results(trace_processor, startup_a_trio) -> dict:
    """{(metric, "current" | "rerun"): compute_metric against the baseline}."""
    baseline, current, rerun = startup_a_trio
    return {
        (name, label): compute_metric(
            name, baseline=baseline, current=other, binary=trace_processor
        )
        for name in (TTID, TTFD)
        for label, other in (("current", current), ("rerun", rerun))
    }


def test_both_startup_metrics_are_listed():
    entries = {m["name"]: m for m in list_metrics()}
    for name in (TTID, TTFD):
        entry = entries[name]
        assert (entry["unit"], entry["requires_baseline"]) == ("ms", True)
        assert "key" not in entry
        # The model choosing a metric is told how many starts become one number.
        assert "median (p50, nearest rank)" in entry["description"]
        assert "cold start" in entry["description"]


def test_the_two_metrics_differ_only_in_their_column():
    # The two files are one query over two columns, maintained by hand in step: this
    # catches one being changed without the other.
    library = metrics._load_library()
    ttid, ttfd = library[TTID].sql, library[TTFD].sql
    assert ttid.replace("time_to_initial_display", "time_to_full_display") == ttfd


def test_ttid_known_answers(results):
    pair = results[(TTID, "current")]
    assert pair["unit"] == "ms"
    assert pair["sql_used"].startswith(INCLUDES)
    assert pair["baseline"] == pytest.approx(349.682708, abs=NS)
    assert pair["current"] == pytest.approx(664.881333, abs=NS)
    assert pair["delta"] == pytest.approx(315.198625, abs=NS)
    assert results[(TTID, "rerun")]["current"] == pytest.approx(345.470333, abs=NS)
    # What the agent's tool returns must be JSON-serialisable.
    json.dumps(list(results.values()))


def test_ttfd_known_answers(results):
    pair = results[(TTFD, "current")]
    assert pair["sql_used"].startswith(INCLUDES)
    assert pair["baseline"] == pytest.approx(2077.310959, abs=NS)
    assert pair["current"] == pytest.approx(2723.988335, abs=NS)
    assert results[(TTFD, "rerun")]["current"] == pytest.approx(2282.739626, abs=NS)


def test_the_change_shows_in_ttid(results):
    # The current capture's TTID grew by more than twice the whole clean spread: past
    # any clean capture from any other, with room to spare for a noisier baseline.
    assert results[(TTID, "current")]["delta"] > 2 * TTID_CLEAN_SPREAD_MS


def test_the_clean_pair_shows_no_meaningful_delta(results):
    # Control: the same build captured twice moves each metric by less than its clean
    # spread, so the delta above is not what any two captures differ by. TTID's clean
    # pair differs by 4 ms. TTFD waits on a network fetch and is noisier (205 ms here);
    # ADR-0009 records that it does not separate the change from clean runs.
    assert abs(results[(TTID, "rerun")]["delta"]) < TTID_CLEAN_SPREAD_MS
    assert abs(results[(TTFD, "rerun")]["delta"]) < TTFD_CLEAN_SPREAD_MS
    # And small beside the change itself: the spread above is measured over captures
    # that include this pair, so it is also checked against the other pair's delta.
    # A tenth leaves room for a noisier clean pair (the spread is a third of the change)
    # while no clean pair could pass for the change.
    assert (
        abs(results[(TTID, "rerun")]["delta"])
        < results[(TTID, "current")]["delta"] / 10
    )


@pytest.mark.parametrize(
    ("name", "column"),
    [(TTID, "time_to_initial_display"), (TTFD, "time_to_full_display")],
)
def test_the_metric_is_the_nearest_rank_median_of_every_start(
    results, trace_processor, startup_a_trio, name, column
):
    # An independent aggregation: every start's value from the stdlib table, and the
    # median taken here, so the ranking SQL in the metric is checked, not trusted.
    baseline, current, _ = startup_a_trio
    for trace, side in ((baseline, "baseline"), (current, "current")):
        starts = query_trace(
            f"SELECT s.package, s.startup_type, d.{column} "
            "FROM android_startups s "
            "JOIN android_startup_time_to_display d USING (startup_id)",
            trace,
            modules=MODULES,
            binary=trace_processor,
        )["rows"]
        # One app, 20 cold starts, each with a value: nothing is filtered out here.
        assert {(pkg, kind) for pkg, kind, _ in starts} == {
            ("com.superplayer.demo", "cold")
        }
        values = sorted(ns for _, _, ns in starts)
        assert len(values) == 20 and None not in values
        median = values[math.ceil(len(values) / 2) - 1]
        assert results[(name, "current")][side] == pytest.approx(median / 1e6, abs=NS)


def test_sql_used_reproduces_every_cited_number(
    results, trace_processor, startup_a_trio
):
    # What the verifier does: split the citation, re-run it, get the same number.
    baseline, current, _ = startup_a_trio
    for name in (TTID, TTFD):
        result = results[(name, "current")]
        statement, modules = split_includes(result["sql_used"])
        for trace, side in ((baseline, "baseline"), (current, "current")):
            rerun = query_trace(
                statement, trace, modules=modules, binary=trace_processor
            )
            assert rerun["rows"] == [[result[side]]]


def test_a_trace_without_startups_reads_null(trace_processor, tiny_trace):
    # One row whose value is NULL, not an error and not 0: a trace with no cold start
    # has no startup time, and the delta against it is None.
    result = compute_metric(
        TTID, baseline=tiny_trace, current=tiny_trace, binary=trace_processor
    )
    assert (result["baseline"], result["current"], result["delta"]) == (
        None,
        None,
        None,
    )
