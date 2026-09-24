"""Scoring (ADR-0027): each rate over its own denominator, the spread over
repetitions, flips, errors, and never the confidence field. Hand-made diagnoses."""

import copy
import json
from pathlib import Path

import pytest

from perfettoagent.evalcases import Expected
from perfettoagent.scoring import Outcome, outcome_of, score

REPORTS = Path(__file__).parent / "fixtures" / "reports"
PLANT = "6efb841e56d8a1b2c3d4e5f60718293a4b5c6d7e"
OTHER = "1" * 40

EXPECTED = {
    "p1": Expected("p1", "regression", ("heap_growth_objects_by_class",), PLANT),
    "p2": Expected("p2", "regression", ("startup_ttid_ms",), OTHER),
    "k1": Expected("k1", "no_regression", (), None),
    "k2": Expected("k2", "no_regression", (), None),
}


def ran(case, run, verdict, metric=None, culprit=None, checked=4, passed=4, **kw):
    return Outcome(
        case_id=case,
        run=run,
        verdict=verdict,
        metric=metric,
        culprit=culprit,
        citations_checked=checked,
        citations_passed=passed,
        **kw,
    )


def failed(case, run):
    return Outcome(case_id=case, run=run, error="RunFailed: a tool failed")


def test_an_outcome_is_read_from_a_verified_diagnosis():
    diagnosis = json.loads((REPORTS / "regression.json").read_text())
    o = outcome_of("p1", 2, diagnosis)
    assert (o.case_id, o.run, o.verdict, o.metric, o.culprit) == (
        "p1",
        2,
        "regression",
        "heap_growth_objects_by_class",
        PLANT,
    )
    assert (o.citations_checked, o.citations_passed) == (6, 5)
    assert (o.usd, o.wall_time_s, o.error) == (0.023117, 136.2, None)


def test_the_confidence_field_is_never_scored():
    diagnosis = json.loads((REPORTS / "regression.json").read_text())
    low = copy.deepcopy(diagnosis)
    low["confidence"] = "low"
    assert outcome_of("p1", 1, diagnosis) == outcome_of("p1", 1, low)
    assert "confidence" not in Outcome.__dataclass_fields__


def test_each_rate_counts_over_its_own_denominator():
    outcomes = [
        # p1: detected and attributed.
        ran("p1", 1, "regression", "heap_growth_objects_by_class", PLANT),
        # p2: detected, wrong commit.
        ran("p2", 1, "regression", "startup_ttid_ms", PLANT, checked=5, passed=3),
        # k1: a false positive; k2: correct.
        ran("k1", 1, "regression", "startup_ttid_ms", OTHER),
        ran("k2", 1, "no_regression", checked=1, passed=1),
    ]
    rates = score(outcomes, EXPECTED)["rates"]
    assert (rates["detection"]["hits"], rates["detection"]["of"]) == (2, 2)
    assert (rates["attribution"]["hits"], rates["attribution"]["of"]) == (1, 2)
    assert (rates["false_positive"]["hits"], rates["false_positive"]["of"]) == (1, 2)
    assert (rates["citation_validity"]["hits"], rates["citation_validity"]["of"]) == (
        12,
        14,
    )


def test_a_regression_on_the_wrong_metric_is_not_a_detection():
    outcomes = [ran("p1", 1, "regression", "startup_ttid_ms", PLANT)]
    rates = score(outcomes, EXPECTED)["rates"]
    assert rates["detection"]["hits"] == 0
    # Attribution counts detected runs only.
    assert rates["attribution"]["of"] == 0 and rates["attribution"]["rate"] is None


def test_an_error_is_a_miss_on_a_planted_case_and_left_out_on_a_clean_pair():
    outcomes = [failed("p1", 1), failed("k1", 1), ran("k2", 1, "no_regression")]
    scores = score(outcomes, EXPECTED)
    assert scores["errors"] == 2
    assert (
        scores["rates"]["detection"]["hits"],
        scores["rates"]["detection"]["of"],
    ) == (
        0,
        1,
    )
    assert scores["rates"]["false_positive"]["of"] == 1


def test_the_spread_is_each_repetition_s_rate_not_the_best_run():
    outcomes = [
        ran("p1", 1, "regression", "heap_growth_objects_by_class", PLANT),
        ran("p2", 1, "regression", "startup_ttid_ms", OTHER),
        ran("p1", 2, "no_regression"),
        ran("p2", 2, "regression", "startup_ttid_ms", OTHER),
        ran("p1", 3, "no_regression"),
        ran("p2", 3, "no_regression"),
    ]
    detection = score(outcomes, EXPECTED)["rates"]["detection"]
    assert detection["by_run"] == [1.0, 0.5, 0.0]
    assert (detection["min"], detection["max"]) == (0.0, 1.0)
    assert detection["rate"] == pytest.approx(3 / 6)


def test_a_case_whose_runs_disagree_is_listed_as_flipped():
    outcomes = [
        ran("p1", 1, "regression", "heap_growth_objects_by_class", PLANT),
        ran("p1", 2, "regression", "heap_growth_objects_by_class", OTHER),
        ran("k1", 1, "no_regression"),
        ran("k1", 2, "no_regression"),
    ]
    per_case = {c["case"]: c for c in score(outcomes, EXPECTED)["per_case"]}
    # Same verdict both times, but only one run attributed: that is a flip too.
    assert per_case["p1"]["flipped"] is True
    assert per_case["p1"]["attributed"] == [True, False]
    assert per_case["k1"]["flipped"] is False


def test_cost_sums_every_run_and_averages_those_that_gave_a_diagnosis():
    usage = {
        "input_tokens": 10,
        "output_tokens": 100,
        "cache_read_input_tokens": 1000,
        "cache_creation_input_tokens": 0,
    }
    outcomes = [
        ran("k1", 1, "no_regression", usd=0.02, wall_time_s=100.0, usage=usage),
        ran("k1", 2, "no_regression", usd=0.04, wall_time_s=140.0, usage=usage),
        failed("k1", 3),
    ]
    cost = score(outcomes, EXPECTED)["cost"]
    assert cost["usd"] == 0.06 and cost["usd_per_run"] == 0.03
    assert cost["usage"]["cache_read_input_tokens"] == 2000
    assert cost["usage_per_run"]["output_tokens"] == 100
    assert cost["wall_time_s"] == {"mean": 120.0, "min": 100.0, "max": 140.0}


def test_cases_are_counted_by_kind():
    outcomes = [ran(c, 1, "no_regression") for c in EXPECTED]
    assert score(outcomes, EXPECTED)["cases"] == {"planted": 2, "clean": 2}


def test_a_run_of_a_case_with_no_answer_is_refused():
    with pytest.raises(ValueError, match="no expected answer"):
        score([ran("zz", 1, "no_regression")], EXPECTED)


def test_from_the_second_repetition_every_run_must_read_the_cache():
    warm = {
        "input_tokens": 5,
        "output_tokens": 10,
        "cache_read_input_tokens": 900,
        "cache_creation_input_tokens": 0,
    }
    cold = {**warm, "cache_read_input_tokens": 0}
    outcomes = [
        ran("k1", 1, "no_regression", usage=cold),  # the first may be cold
        ran("k1", 2, "no_regression", usage=warm),
        ran("k2", 2, "no_regression", usage=cold),
        failed("k1", 3),  # no diagnosis, no usage to check
    ]
    assert score(outcomes, EXPECTED)["cache"] == {"checked": 2, "missing": ["k2/2"]}
