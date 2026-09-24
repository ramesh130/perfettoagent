"""diagnosis.md: golden files for each verdict, and the properties the issue asks of
every report, checked on hand-built diagnoses."""

import copy
import json
import os
from pathlib import Path

import pytest

from perfettoagent.diagnosis import DiagnosisInvalid
from perfettoagent.report import render

REPORTS = Path(__file__).parent / "fixtures" / "reports"
VERDICTS = ("regression", "no_regression", "inconclusive")

# UPDATE_GOLDEN=1 rewrites the .md files from the renderer; review the diff by eye.
_UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"


def diagnosis(name: str) -> dict:
    return json.loads((REPORTS / f"{name}.json").read_text())


@pytest.mark.parametrize("name", VERDICTS)
def test_the_report_matches_its_golden_file(name):
    golden = REPORTS / f"{name}.md"
    rendered = render(diagnosis(name))
    if _UPDATE:
        golden.write_text(rendered)
    assert rendered == golden.read_text()


def test_the_first_ten_lines_give_the_verdict_metric_delta_and_culprit():
    head = "\n".join(render(diagnosis("regression")).splitlines()[:10])
    assert head.startswith("# Regression\n")
    assert "`heap_growth_objects_by_class` +2,184 objects" in head
    assert "432,751 → 434,935 objects" in head
    assert "`6efb841e56d8` (direct)" in head


@pytest.mark.parametrize("name", ["no_regression", "inconclusive"])
def test_the_first_ten_lines_say_when_no_culprit_was_attributed(name):
    head = "\n".join(render(diagnosis(name)).splitlines()[:10])
    assert "**Culprit:** none attributed" in head


def test_the_first_ten_lines_say_the_verifier_changed_the_verdict():
    head = "\n".join(render(diagnosis("inconclusive")).splitlines()[:10])
    assert "from `regression`: no claim survived verification" in head
    assert "dropped the model's: no surviving claim cites the culprit" in head


def test_every_claim_is_followed_by_each_citations_evidence():
    report = render(diagnosis("regression"))
    kept = report.split("## Claims", 1)[1].split("## Caveats", 1)[0]
    for claim in diagnosis("regression")["claims"]:
        section = kept.split(f"### {claim['id']}.", 1)[1].split("\n### ", 1)[0]
        for citation in claim["citations"]:
            evidence = citation["sql"] if citation["kind"] == "trace" else None
            assert (evidence or citation["commit"]) in section
    assert "The `current` trace: 1 row." in kept


def test_dropped_claims_and_caveats_are_listed_with_their_reasons():
    report = render(diagnosis("inconclusive"))
    assert "## Dropped claims" in report
    assert "Dropped: citation 1: returned 0 rows" in report
    assert "Failed: returned 0 rows" in report
    caveats = report.split("## Caveats", 1)[1].split("##", 1)[0]
    assert "A single capture per side" in caveats
    assert "the metric was dropped by the verifier" in caveats


def test_a_dropped_claim_never_appears_among_the_kept_ones():
    report = render(diagnosis("regression"))
    kept, dropped = report.split("## Dropped claims")
    assert "A second commit also leaks." not in kept
    assert "A second commit also leaks." in dropped


def test_backticks_in_cited_sql_cannot_close_the_fence():
    report = render(diagnosis("no_regression"))
    assert "````sql\nSELECT `ts`, dur FROM slice WHERE name = 'x ``` y'\n````" in report


def test_model_prose_cannot_start_a_heading_or_list():
    d = diagnosis("regression")
    d["claims"][0]["text"] = "fine\n# Not a heading\n- not a list"
    report = render(d)
    assert "\n# Not a heading" not in report
    assert "fine # Not a heading - not a list" in report


def test_an_unverified_output_is_refused():
    d = diagnosis("regression")
    bad = copy.deepcopy(d)
    del bad["verification"]
    with pytest.raises(DiagnosisInvalid):
        render(bad)
