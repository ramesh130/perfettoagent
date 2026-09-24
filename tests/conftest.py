import os
from pathlib import Path
from typing import NamedTuple

import pytest

from perfettoagent.trace_processor import TraceProcessorError, resolve_trace_processor

FIXTURES = Path(__file__).parent / "fixtures"

# A small Android emulator trace: 840 slices, 2542 threads, 375 processes.
TINY_TRACE = FIXTURES / "tiny.perfetto-trace"

# Set to 1 where the real-trace inputs are known to be present (CI, after its fetch
# step and an LFS checkout), so a missing binary, or an LFS pointer in place of a
# fixture, fails the run instead of silently skipping the tests that need them.
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


# Traces too large for plain git (12-33 MB each) live in Git LFS: ADR-0004 and
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
        message = (
            f"{path.name} is a Git LFS pointer, not the trace: this clone was made "
            "without LFS. Fetch the fixtures with: git lfs install && git lfs pull"
        )
        if os.environ.get(REQUIRE_ENV) == "1":
            pytest.fail(f"{REQUIRE_ENV}=1 but {message}")
        pytest.skip(message)
    return path


@pytest.fixture(scope="session")
def heap_a_pair() -> tuple[Path, Path]:
    """(baseline, current): two Java heap dumps of the same app at the same point of the
    same scenario, before and after a change."""
    return (
        large_fixture("heap-a-baseline.perfetto-trace"),
        large_fixture("heap-a-current.perfetto-trace"),
    )


@pytest.fixture(scope="session")
def startup_a_trio() -> tuple[Path, Path, Path]:
    """(baseline, current, rerun): three startup captures of the same app, each 20 cold
    starts. `current` is after a change; `rerun` is a second capture of the baseline's
    build, for the clean pair. Gzipped, which trace processor reads as is (ADR-0010).
    """
    return (
        large_fixture("startup-a-baseline.perfetto-trace.gz"),
        large_fixture("startup-a-current.perfetto-trace.gz"),
        large_fixture("startup-a-rerun.perfetto-trace.gz"),
    )


class JankTraces(NamedTuple):
    """Five captures of one scripted scroll-and-tap scenario on one app, gzipped
    (ADR-0010). `baseline` and `rerun` are two captures of the same build, the clean
    pair. `current_b`, `current_c` and `current_d` are each a capture after a different
    change, and each is compared against `baseline`. Named for their role, never for
    what changed (CLAUDE.md, eval integrity)."""

    baseline: Path
    rerun: Path
    current_b: Path
    current_c: Path
    current_d: Path


@pytest.fixture(scope="session")
def jank_traces() -> JankTraces:
    return JankTraces(
        baseline=large_fixture("jank-a-baseline.perfetto-trace.gz"),
        rerun=large_fixture("jank-a-rerun.perfetto-trace.gz"),
        current_b=large_fixture("jank-b-current.perfetto-trace.gz"),
        current_c=large_fixture("jank-c-current.perfetto-trace.gz"),
        current_d=large_fixture("jank-d-current.perfetto-trace.gz"),
    )
