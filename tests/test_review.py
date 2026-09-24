"""`review` (roadmap item 10, #32, ADR-0026): each answer, what a feedback line
records, and that nothing but the feedback file is written."""

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from perfettoagent.cli import main
from perfettoagent.review import ReviewRefused, review

REPORTS = Path(__file__).parent / "fixtures" / "reports"
NOW = datetime(2026, 9, 25, 12, 0, tzinfo=UTC)


@pytest.fixture
def out_dir(tmp_path) -> Path:
    """A diagnose output directory holding the regression fixture: claims c0 and c1
    kept, c2 dropped."""
    directory = tmp_path / "run"
    directory.mkdir()
    shutil.copy(REPORTS / "regression.json", directory / "diagnosis.json")
    return directory


def lines(feedback: Path) -> list[dict]:
    return [json.loads(line) for line in feedback.read_text().splitlines()]


def snapshot(root: Path) -> dict:
    return {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_accept_records_the_answer_and_the_inputs_by_content(out_dir, tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    raw = (out_dir / "diagnosis.json").read_bytes()
    line = review(out_dir, "accept", feedback=feedback, now=NOW)
    run = json.loads(raw)["run"]
    assert lines(feedback) == [line]
    assert line == {
        "schema": 1,
        "reviewed_at": "2026-09-25T12:00:00+00:00",
        "answer": "accept",
        "reason": None,
        "claims_accepted": ["c0", "c1"],
        "claims_rejected": [],
        "inputs": {
            "baseline_sha256": run["inputs"]["baseline_sha256"],
            "current_sha256": run["inputs"]["current_sha256"],
            "range": run["inputs"]["range"],
            "diagnosis_sha256": hashlib.sha256(raw).hexdigest(),
        },
        "diagnosis": {
            "verdict": "regression",
            "culprit": "6efb841e56d8a1b2c3d4e5f60718293a4b5c6d7e",
            "metric": "heap_growth_objects_by_class",
            "provider": "openai",
            "model": "gpt-5.6-luna",
            "effort": "high",
        },
    }


def test_reject_records_its_reason_and_every_kept_claim_as_rejected(out_dir, tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    line = review(out_dir, "reject", reason="wrong commit", feedback=feedback)
    assert (line["reason"], line["claims_accepted"], line["claims_rejected"]) == (
        "wrong commit",
        [],
        ["c0", "c1"],
    )


def test_partial_records_the_claims_accepted_and_the_rest_rejected(out_dir, tmp_path):
    line = review(
        out_dir, "partial", claim_ids=["c1"], feedback=tmp_path / "feedback.jsonl"
    )
    assert (line["claims_accepted"], line["claims_rejected"]) == (["c1"], ["c0"])


def test_answers_are_appended(out_dir, tmp_path):
    feedback = tmp_path / "feedback.jsonl"
    review(out_dir, "accept", feedback=feedback)
    review(out_dir, "reject", reason="no", feedback=feedback)
    assert [line["answer"] for line in lines(feedback)] == ["accept", "reject"]


@pytest.mark.parametrize(
    "answer, kwargs, message",
    [
        ("partial", {"claim_ids": ["c9"]}, "no kept claim c9"),
        # c2 was dropped by the verifier: never a finding, so not answerable.
        ("partial", {"claim_ids": ["c0", "c2"]}, "no kept claim c2"),
        ("partial", {"claim_ids": ["c0", "c1"]}, "use accept or reject"),
        ("reject", {"reason": "  "}, "reject needs a reason"),
        ("maybe", {}, "the answer is one of"),
    ],
)
def test_a_bad_answer_is_refused_and_nothing_is_written(
    out_dir, tmp_path, answer, kwargs, message
):
    feedback = tmp_path / "feedback.jsonl"
    with pytest.raises(ReviewRefused, match=message):
        review(out_dir, answer, feedback=feedback, **kwargs)
    assert not feedback.exists()


def test_a_diagnosis_with_no_run_is_refused(tmp_path):
    shutil.copy(REPORTS / "inconclusive.json", tmp_path / "diagnosis.json")
    with pytest.raises(ReviewRefused, match="records no run"):
        review(tmp_path, "accept", feedback=tmp_path / "f.jsonl")


@pytest.mark.parametrize("content", [None, "{not json", '{"verdict": "regression"}'])
def test_no_verified_diagnosis_is_refused(tmp_path, content):
    if content is not None:
        (tmp_path / "diagnosis.json").write_text(content)
    with pytest.raises(ReviewRefused):
        review(tmp_path, "accept", feedback=tmp_path / "f.jsonl")


def test_only_the_feedback_file_is_written(out_dir, tmp_path):
    before = snapshot(tmp_path)
    feedback = tmp_path / "feedback.jsonl"
    review(out_dir, "partial", claim_ids=["c0"], feedback=feedback)
    after = snapshot(tmp_path)
    assert set(after) - set(before) == {feedback}
    assert {p: after[p] for p in before} == before


def test_the_cli_records_each_answer(out_dir, tmp_path, capsys):
    feedback = str(tmp_path / "feedback.jsonl")
    base = ["review", str(out_dir), "--feedback", feedback]
    assert main([*base, "accept"]) == 0
    assert main([*base, "reject", "the", "wrong", "commit"]) == 0
    assert main([*base, "partial", "c0"]) == 0
    recorded = lines(Path(feedback))
    assert [(r["answer"], r["reason"]) for r in recorded] == [
        ("accept", None),
        ("reject", "the wrong commit"),
        ("partial", None),
    ]
    assert "1 claims accepted, 1 rejected" in capsys.readouterr().out


def test_the_cli_refuses_an_unknown_claim_id(out_dir, tmp_path, capsys):
    feedback = tmp_path / "feedback.jsonl"
    argv = ["review", str(out_dir), "--feedback", str(feedback), "partial", "c7"]
    assert main(argv) == 2
    assert not feedback.exists()
    assert "rejected: no kept claim c7" in capsys.readouterr().err
