"""The eval cases (ADR-0015): their count, their ranges, the split between what the
model sees and what it should answer, and a scan of everything it sees for the answer.

These read only the committed cases and the fixture bundle, which is plain git, so they
run in any clone. The traces are Git LFS objects that a default fetch leaves out
(`.lfsconfig`), and nothing here reads them beyond their first bytes.
"""

import dataclasses
import json
import re
import subprocess
from pathlib import Path

import pytest
from conftest import LFS_POINTER

from perfettoagent.evalcases import (
    CASE_FILES,
    EVALS_DIR,
    CaseError,
    CaseInputs,
    list_cases,
    load_expected,
    load_inputs,
)
from perfettoagent.metrics import list_metrics

CASES = list_cases()

# Roadmap item 5: five planted cases, and at least as many clean pairs.
PLANTED = 5
MIN_CLEAN = 5

# Roadmap item 5 and the issue: each range holds at least this many commits besides the
# plant, so attribution is a search over the range and not a lookup.
MIN_UNRELATED = 8

# Words that would tell the model what it is looking at, or that it is being tested.
# Each is matched case-insensitively at the start of a word, so "regress" catches
# "regression". The plant's code itself is not scanned for these: `Thread.sleep` in the
# culprit's diff is the evidence the model has to find, not a hint.
HINT_WORDS = (
    "plant",
    "regress",
    "culprit",
    "perfettoagent",
    "devicelab",
    "eval",
    "inject",
    "deliberate",
    "on purpose",
    "leak",
    "jank",
    "thrash",
    "storm",
)


def hints_in(text: str, answers: list[dict]) -> list[str]:
    """Every hint word, plant name or regression name that `text` contains."""
    names = [a["plant"] for a in answers if a["plant"]]
    names += [a["regression"] for a in answers if a["regression"]]
    found = [w for w in HINT_WORDS if re.search(rf"\b{w}", text, re.IGNORECASE)]
    return found + [n for n in names if n.lower() in text.lower()]


@pytest.fixture(scope="module")
def answers() -> list[dict]:
    return [
        json.loads((EVALS_DIR / "answers" / f"{c}.json").read_text()) for c in CASES
    ]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


@pytest.fixture(scope="module")
def checkouts(tmp_path_factory) -> dict[str, Path]:
    """Every case's fixture repo, cloned the way the runner clones it."""
    root = tmp_path_factory.mktemp("cases")
    return {c: load_inputs(c).checkout(root / c) for c in CASES}


def test_five_planted_cases_and_at_least_five_clean_pairs():
    expected = [load_expected(c) for c in CASES]
    planted = [e for e in expected if e.verdict == "regression"]
    clean = [e for e in expected if e.verdict == "no_regression"]
    assert len(planted) == PLANTED
    assert len(clean) >= MIN_CLEAN
    assert all(e.culprit for e in planted)
    assert all(e.culprit is None and e.metrics == () for e in clean)


def test_each_planted_case_is_a_different_plant(answers):
    plants = [a["plant"] for a in answers if a["plant"]]
    assert len(set(plants)) == PLANTED


def test_expected_metrics_are_in_the_library():
    library = {m["name"] for m in list_metrics()}
    for case_id in CASES:
        assert set(load_expected(case_id).metrics) <= library, case_id


# --- What the model sees is apart from what it should answer. -------------------------


def test_inputs_hold_no_expected_answer():
    inputs_fields = {f.name for f in dataclasses.fields(CaseInputs)}
    assert inputs_fields.isdisjoint({"verdict", "metrics", "culprit", "plant", "patch"})
    for case_id in CASES:
        inputs = json.loads((EVALS_DIR / "cases" / case_id / "inputs.json").read_text())
        assert set(inputs) == {"schema", "repo", "range"}, case_id
        assert set(inputs["range"]) == {"base", "head"}, case_id


def test_a_case_directory_holds_its_inputs_and_nothing_else():
    for case_id in CASES:
        names = {p.name for p in (EVALS_DIR / "cases" / case_id).iterdir()}
        assert names == CASE_FILES, case_id


def test_case_ids_are_opaque():
    assert len(CASES) >= PLANTED + MIN_CLEAN
    assert all(re.fullmatch(r"[0-9a-f]{8}", c) for c in CASES)


def test_traces_are_gzip_or_an_lfs_pointer():
    """Trace processor reads gzip as is (ADR-0010); a clone that did not fetch the eval
    traces has pointers in their place."""
    for case_id in CASES:
        inputs = load_inputs(case_id)
        for trace in (inputs.baseline, inputs.current):
            head = trace.read_bytes()[: len(LFS_POINTER)]
            assert head[:2] == b"\x1f\x8b" or head == LFS_POINTER, trace


def test_a_missing_case_is_a_clear_error():
    with pytest.raises(CaseError, match="no such case file"):
        load_inputs("00000000")
    with pytest.raises(CaseError, match="no such case file"):
        load_expected("00000000")


def test_an_answer_must_agree_with_itself(tmp_path):
    (tmp_path / "answers").mkdir()
    path = tmp_path / "answers" / "0badcafe.json"
    path.write_text(
        json.dumps(
            {"schema": 1, "verdict": "regression", "metrics": [], "culprit": None}
        )
    )
    with pytest.raises(CaseError, match="names a culprit"):
        load_expected("0badcafe", root=tmp_path)
    path.write_text(
        json.dumps({"schema": 1, "verdict": "maybe", "metrics": [], "culprit": None})
    )
    with pytest.raises(CaseError, match="not one of"):
        load_expected("0badcafe", root=tmp_path)


# --- The ranges. ----------------------------------------------------------------------


def test_each_range_has_enough_unrelated_commits(checkouts):
    for case_id, repo in checkouts.items():
        inputs = load_inputs(case_id)
        commits = git(
            repo, "rev-list", f"{inputs.range_base}..{inputs.range_head}"
        ).split()
        culprit = load_expected(case_id).culprit
        unrelated = [c for c in commits if c != culprit]
        assert len(unrelated) >= MIN_UNRELATED, case_id
        # The range's base is the root: the baseline trace's build, with no history
        # before it that a model could search instead.
        assert git(repo, "rev-list", "--max-parents=0", "HEAD").split() == [
            inputs.range_base
        ], case_id


def test_the_culprit_is_one_commit_inside_its_range(checkouts):
    for case_id, repo in checkouts.items():
        culprit = load_expected(case_id).culprit
        if culprit is None:
            continue
        inputs = load_inputs(case_id)
        commits = git(
            repo, "rev-list", f"{inputs.range_base}..{inputs.range_head}"
        ).split()
        assert commits.count(culprit) == 1, case_id


def test_the_culprit_makes_exactly_the_captured_change(checkouts, answers):
    """The culprit's diff is the plant the current trace was built with (the stored
    patch, whose sha256 build_cases.py checked against the capture's run.json)."""
    by_id = dict(zip(CASES, answers, strict=True))
    for case_id, repo in checkouts.items():
        answer = by_id[case_id]
        if answer["culprit"] is None:
            continue
        culprit_diff = git(repo, "diff-tree", "-p", "--no-commit-id", answer["culprit"])
        stored = (EVALS_DIR / "answers" / answer["patch"]).read_text()
        assert patch_id(culprit_diff) == patch_id(stored), case_id


def patch_id(diff: str) -> str:
    """git's content hash of a diff, blind to line numbers and whitespace."""
    out = subprocess.run(
        ["git", "patch-id", "--stable"],
        input=diff,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return out.split()[0]


def test_a_checkout_reaches_its_own_case_and_nothing_else(checkouts):
    heads = {c: load_inputs(c).range_head for c in CASES}
    for case_id, repo in checkouts.items():
        assert git(repo, "for-each-ref", "--format=%(refname)").split() == [
            "refs/heads/main"
        ]
        assert git(repo, "remote") == ""
        assert git(repo, "reflog", "--all") == ""
        assert git(repo, "rev-parse", "HEAD").strip() == heads[case_id]
        for other, head in heads.items():
            if head != heads[case_id]:
                reachable = subprocess.run(
                    ["git", "-C", str(repo), "cat-file", "-e", f"{head}^{{commit}}"],
                    capture_output=True,
                )
                assert reachable.returncode != 0, (
                    f"{other}'s head is in {case_id}'s checkout"
                )


# --- Nothing the model sees names the plant. ------------------------------------------


def test_the_scan_finds_a_named_plant(answers):
    """The control: the scan below is not passing because it cannot see anything."""
    assert hints_in("Revert the feed-tap-sleep plant", answers) == [
        "plant",
        "feed-tap-sleep",
    ]
    assert hints_in("Fix the allocation storm", answers) == [
        "storm",
        "Allocation storm",
    ]
    assert hints_in("Rename the feed's handler", answers) == []


def test_no_model_visible_input_hints_at_the_plant(answers):
    for case_id in CASES:
        assert hints_in(case_id, answers) == []
        directory = EVALS_DIR / "cases" / case_id
        assert hints_in((directory / "inputs.json").read_text(), answers) == [], case_id
        for path in directory.iterdir():
            assert hints_in(path.name, answers) == [], path


def test_no_commit_message_path_or_added_line_hints_at_the_plant(checkouts, answers):
    for case_id, repo in checkouts.items():
        inputs = load_inputs(case_id)
        visible = [
            # Every commit's message and identity, the root's included.
            git(repo, "log", "--format=%an %ae %cn %ce%n%B", "HEAD"),
            # Every path the range touches, and every line it adds.
            git(repo, "diff", "--name-only", inputs.range_base, inputs.range_head),
            "\n".join(
                line
                for line in git(
                    repo, "log", "-p", "--format=", f"{inputs.range_base}..HEAD"
                ).splitlines()
                if line.startswith("+") and not line.startswith("+++")
            ),
        ]
        for text in visible:
            assert hints_in(text, answers) == [], case_id


def test_no_file_in_a_checkout_mentions_plants(checkouts):
    """The snapshot leaves out devicelab/ and every document that describes the plants
    (build_cases.EXCLUDED). What is left must not say "plant" or name this project."""
    for case_id, repo in checkouts.items():
        found = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "grep",
                "-I",
                "-i",
                "-l",
                "-E",
                r"\bplant(s|ed|ing)?\b|perfettoagent",
                "HEAD",
            ],  # fmt: skip
            capture_output=True,
            text=True,
        )
        assert found.stdout == "", f"{case_id}: {found.stdout}"
