"""Run metadata (`--run-json`, ADR-0025): the file's schema, the range rule, the
caveats it requires and the tool that shows it to the model."""

import json
import re

import pytest
from test_diagnose import build_repo

from perfettoagent import run_metadata
from perfettoagent.run_metadata import (
    CAVEAT_DEBUGGABLE,
    CAVEAT_DIRTY,
    READ_RUN_METADATA,
    RunMetadataInvalid,
)


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> dict:
    return build_repo(tmp_path_factory.mktemp("target") / "checkout-r4")


def metadata(commit: str = "a" * 40, **overrides) -> dict:
    """Valid schema 1 run metadata."""
    value = {
        "schema": 1,
        "commit": commit,
        "tree_dirty": False,
        "debuggable": False,
        "build_type": "benchmark",
        "device": {"model": "sdk_gphone64_arm64", "sdk": "36", "emulator": True},
    }
    return {**value, **overrides}


def write(tmp_path, value) -> str:
    path = tmp_path / "run.json"
    path.write_text(value if isinstance(value, str) else json.dumps(value))
    return path


def test_valid_metadata_loads(tmp_path):
    assert run_metadata.load(write(tmp_path, metadata())) == metadata()


def test_unrecorded_build_type_and_device_are_null(tmp_path):
    value = metadata(build_type=None, device=None)
    assert run_metadata.load(write(tmp_path, value)) == value


@pytest.mark.parametrize(
    "value, error",
    [
        ("{not json", "not JSON"),
        (metadata(schema=2), "$.schema: expected 1"),
        ({k: v for k, v in metadata().items() if k != "commit"}, "missing 'commit'"),
        (metadata(debuggable="no"), "$.debuggable: expected boolean"),
        # A capture tool's own run.json records the plant; it is not this format.
        (metadata(plant={"name": "x"}), "unexpected 'plant'"),
    ],
)
def test_anything_else_is_refused(tmp_path, value, error):
    with pytest.raises(RunMetadataInvalid, match=re.escape(error)):
        run_metadata.load(write(tmp_path, value))


def test_a_commit_inside_the_range_passes(repo):
    for name in ("change", "head"):
        run_metadata.check(metadata(repo["sha"][name]), repo["path"], repo["range"])


@pytest.mark.parametrize("commit", ["base", "unknown", "not-a-sha"])
def test_a_commit_outside_the_range_is_refused(repo, commit):
    sha = {"base": repo["sha"]["base"], "unknown": "f" * 40}.get(commit, commit)
    with pytest.raises(RunMetadataInvalid, match="is not inside the range"):
        run_metadata.check(metadata(sha), repo["path"], repo["range"])


@pytest.mark.parametrize(
    "dirty, debuggable, expected",
    [
        (False, False, []),
        (True, False, [CAVEAT_DIRTY]),
        (False, True, [CAVEAT_DEBUGGABLE]),
        (True, True, [CAVEAT_DIRTY, CAVEAT_DEBUGGABLE]),
    ],
)
def test_a_dirty_tree_or_debuggable_build_is_a_caveat(dirty, debuggable, expected):
    value = metadata(tree_dirty=dirty, debuggable=debuggable)
    assert run_metadata.caveats(value) == expected


def test_no_metadata_needs_no_caveat():
    assert run_metadata.caveats(None) == []


def test_the_tool_is_strict_takes_nothing_and_returns_the_metadata():
    schema = READ_RUN_METADATA.input_schema
    assert schema == {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }
    assert READ_RUN_METADATA.definition()["strict"] is True
    assert READ_RUN_METADATA.call(metadata(), {}) == metadata()
    assert "says nothing about the baseline" in READ_RUN_METADATA.description
