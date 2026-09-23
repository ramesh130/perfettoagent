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
