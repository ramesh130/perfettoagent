"""Run metadata: what the capture of the current trace records about its build, given
with `diagnose --run-json` (roadmap item 7's input rules, issue #31, ADR-0025).

The file is this project's own small format, schema 1, not a capture tool's `run.json`
as written: devicelab and jetnews-perf's harness record the same facts under different
keys, and both record the plant, which no model input may name (CLAUDE.md). It holds:

- `commit`: the commit the current trace's build was made from. It must be inside
  `--range`, or the run is refused before any request: a trace built outside the range
  cannot be explained by it.
- `tree_dirty`: the build had uncommitted changes, so the code it ran is not exactly
  `commit`'s.
- `debuggable`: the build was debuggable, so ART ran it with fewer optimisations and
  its timings overstate a release build's.
- `build_type` and `device`, for the model to read, or null when not recorded.

A dirty tree or a debuggable build is never accepted silently: each becomes a caveat,
written by this code, not the model, and shown in the report's header (ADR-0025).

The model reads the file through `read_run_metadata()`, a tool bound only when
`--run-json` was passed.
"""

import json
from pathlib import Path

from perfettoagent.diagnosis import validate
from perfettoagent.tools import STRING, Tool, nullable, strict_input
from perfettoagent.verify import commit_in_range

# Bumped by any change a reader of an older file would misread.
SCHEMA_VERSION = 1

_BOOLEAN = {"type": "boolean"}


RUN_METADATA_SCHEMA = {
    **strict_input(
        schema={"type": "integer", "const": SCHEMA_VERSION},
        commit=STRING,
        tree_dirty=_BOOLEAN,
        debuggable=_BOOLEAN,
        build_type=nullable(STRING),
        device=nullable(strict_input(model=STRING, sdk=STRING, emulator=_BOOLEAN)),
    ),
    "description": "The current trace's capture: its build and device.",
}

CAVEAT_DIRTY = (
    "the current trace's build had uncommitted changes (run metadata: tree_dirty), "
    "so the code it ran is not exactly any commit in the range"
)
CAVEAT_DEBUGGABLE = (
    "the current trace's build was debuggable (run metadata: debuggable), so ART ran "
    "it with fewer optimisations and its timings overstate a release build's"
)


class RunMetadataInvalid(ValueError):
    """The file is not run metadata schema 1, or its commit is outside the range."""


def load(path: str | Path) -> dict:
    """The run metadata in `path`. Raises RunMetadataInvalid for a file that is not
    JSON or not schema 1, and FileNotFoundError for none."""
    try:
        metadata = json.loads(Path(path).read_text())
    except json.JSONDecodeError as e:
        raise RunMetadataInvalid(f"{path}: not JSON: {e}") from e
    errors = validate(metadata, RUN_METADATA_SCHEMA)
    if errors:
        raise RunMetadataInvalid(
            f"{path}: not run metadata schema {SCHEMA_VERSION}: " + "; ".join(errors)
        )
    return metadata


def check(metadata: dict, repo: str | Path, git_range: str) -> None:
    """Raises RunMetadataInvalid unless `metadata`'s commit names a commit inside
    `git_range` in `repo`: what `git log base..head` lists."""
    commit = metadata["commit"]
    if not commit_in_range(repo, git_range, commit):
        raise RunMetadataInvalid(
            f"the run metadata's commit {commit} is not inside the range {git_range}: "
            "the current trace was not built from it"
        )


def caveats(metadata: dict | None) -> list[str]:
    """The caveats `metadata` requires: one for a dirty tree, one for a debuggable
    build. None for no metadata."""
    if metadata is None:
        return []
    found = []
    if metadata["tree_dirty"]:
        found.append(CAVEAT_DIRTY)
    if metadata["debuggable"]:
        found.append(CAVEAT_DEBUGGABLE)
    return found


def _read(metadata: dict) -> dict:
    return metadata


READ_RUN_METADATA = Tool(
    name="read_run_metadata",
    description=(
        "Read what the current trace's capture recorded about its build: `commit`, "
        "the commit it was built from (inside the range); `tree_dirty`, whether the "
        "build had uncommitted changes; `debuggable`; `build_type`; and `device` "
        "(model, sdk, emulator), each null when not recorded. It says nothing about "
        "the baseline trace's build, nor what changed between the builds: that is for "
        "the git tools."
    ),
    input_schema=strict_input(),
    function=_read,
)
