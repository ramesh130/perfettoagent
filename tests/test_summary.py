"""summary.md (ADR-0031) from results sets written by the real runner, with a fake
`diagnose`, over the small evals directory of test_evalrun."""

import json

import pytest
from test_evalrun import CLEAN, PLANTED, FakeDiagnose, culprit, root  # noqa: F401

from perfettoagent import evalrun, summary

TRIAGE = {
    "schema": 1,
    "measured": False,
    "basis": "assumed",
    "cases": [{"case": PLANTED, "minutes": 60, "culprit_found": True}],
}


@pytest.fixture
def results(root, culprit, tmp_path):
    """Sets at two efforts with --metric auto, and one with the named metric."""
    out = tmp_path / "results"
    for effort, metric in (("low", "auto"), ("high", "auto"), ("high", "expected")):
        evalrun.run_eval(
            out / evalrun.results_name("gpt-5.6-luna", effort, metric),
            root=root,
            runs=2,
            effort=effort,
            metric=metric,
            diagnose_fn=FakeDiagnose(root, culprit),
            log=lambda line: None,
        )
    return out


def test_every_set_gets_its_own_row_in_effort_order(results, root):
    text = summary.render(summary.load_sets(results), TRIAGE, root=root)
    table = text.split("## `gpt-5.6-luna`, `--metric auto`: all cases", 1)[1]
    rows = [line for line in table.splitlines() if line.startswith("| low") or
            line.startswith("| high")]  # fmt: skip
    assert [r.split(" |")[0] for r in rows[:2]] == ["| low", "| high"]
    # Every run said regression: the planted case detected, the clean pair a false
    # positive, both runs, in both sets.
    assert "| 100% (2/2) | 100% (2/2) | 100% (2/2) |" in rows[0]


def test_the_numbers_are_the_runner_s_own_scores(results, root):
    scores = json.loads((results / "gpt-5.6-luna-low-auto" / "scores.json").read_text())
    text = summary.render(summary.load_sets(results), TRIAGE, root=root)
    usd = scores["cost"]["usd_per_run"]
    assert f"${usd:.4f}" in text


def test_the_manual_baseline_is_labelled_assumed(results, root):
    text = summary.render(summary.load_sets(results), TRIAGE, root=root)
    assert "| Manual triage (assumed) | – | 60 min | 1/1 cases |" in text
    assert "assumed, not measured: ADR-0030" in text
    measured = {**TRIAGE, "measured": True}
    text = summary.render(summary.load_sets(results), measured, root=root)
    assert "| Manual triage | – | 60 min |" in text


def test_q3_compares_auto_with_the_named_metric_on_planted_cases(
    results,
    root,
):
    text = summary.render(summary.load_sets(results), TRIAGE, root=root)
    q3 = text.split("## Q3", 1)[1].split("## Cache", 1)[0]
    assert "| `gpt-5.6-luna` | high | auto |" in q3
    assert "| `gpt-5.6-luna` | high | expected |" in q3
    assert "the same as the named metric's, within 10: `auto` stands alone" in q3
    named = results / "gpt-5.6-luna-high-expected" / "runs"
    assert {p.name for p in named.iterdir()} == {PLANTED}
    result = json.loads((named / PLANTED / "1" / "result.json").read_text())
    assert result["named_metric"] == "heap_growth_objects_by_class"


def test_what_was_not_run_is_said(results, root):
    text = summary.render(summary.load_sets(results), TRIAGE, root=root)
    assert "`claude-opus-5-5`, the compared model" in text
    assert "## Cache reads" in text


def test_expected_mode_refuses_a_clean_pair_named_explicitly(
    root,
    culprit,
    tmp_path,
):
    with pytest.raises(SystemExit, match="planted cases only"):
        evalrun.run_eval(
            tmp_path / "out",
            root=root,
            cases=[CLEAN],
            metric="expected",
            diagnose_fn=FakeDiagnose(root, culprit),
        )
