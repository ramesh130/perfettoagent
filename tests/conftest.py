import os
from pathlib import Path

import pytest

from perfettoagent.trace_processor import TraceProcessorError, resolve_trace_processor

FIXTURES = Path(__file__).parent / "fixtures"

# A small Android emulator trace: 840 slices, 2542 threads, 375 processes.
TINY_TRACE = FIXTURES / "tiny.perfetto-trace"

# Set to 1 where the binary is known to be present (CI after its fetch step), so a
# missing binary fails the run instead of silently skipping the tests that need it.
REQUIRE_ENV = "PERFETTOAGENT_REQUIRE_TRACE_PROCESSOR"


@pytest.fixture(scope="session")
def trace_processor() -> Path:
    """The real trace processor, from TRACE_PROCESSOR or the verified cache; never
    downloaded, since the suite runs with sockets disabled."""
    try:
        return resolve_trace_processor(allow_download=False)
    except TraceProcessorError as e:
        if os.environ.get(REQUIRE_ENV) == "1":
            pytest.fail(f"{REQUIRE_ENV}=1 but {e}")
        pytest.skip(
            f"needs the real trace processor: {e}. Fetch it once, with network: "
            "uv run perfettoagent tp --trace tests/fixtures/tiny.perfetto-trace "
            '--sql "select 1"'
        )


@pytest.fixture(scope="session")
def tiny_trace() -> Path:
    return TINY_TRACE


# Traces too large for plain git (about 22 MB each) live in Git LFS: ADR-0004 and
# .gitattributes. Named for what they are, a baseline and a current capture, and never
# for what differs between them (CLAUDE.md, eval integrity).
LARGE_FIXTURES = FIXTURES / "large"

# The first line of a Git LFS pointer file, which is what a clone without LFS checks out
# in place of the real file.
# ref: https://github.com/git-lfs/git-lfs/blob/main/docs/spec.md#the-pointer
LFS_POINTER = b"version https://git-lfs.github.com/spec/v1"


def large_fixture(name: str) -> Path:
    """A fixture stored in Git LFS, or a skip if this clone has only its pointer."""
    path = LARGE_FIXTURES / name
    with path.open("rb") as f:
        head = f.read(len(LFS_POINTER))
    if head == LFS_POINTER:
        pytest.skip(
            f"{path.name} is a Git LFS pointer, not the trace: this clone was made "
            "without LFS. Fetch the fixtures with: git lfs install && git lfs pull"
        )
    return path


@pytest.fixture(scope="session")
def heap_a_pair() -> tuple[Path, Path]:
    """(baseline, current): two Java heap dumps of the same app at the same point of the
    same scenario, before and after a change."""
    return (
        large_fixture("heap-a-baseline.perfetto-trace"),
        large_fixture("heap-a-current.perfetto-trace"),
    )
