"""The large-fixture guard: an LFS pointer skips (fails in CI), and is never read."""

import conftest
import pytest

POINTER = (
    b"version https://git-lfs.github.com/spec/v1\n"
    b"oid sha256:1f76cacda5ec775ee10702aea3155f75fee3164be4b3fed0131a13047172004b\n"
    b"size 23491492\n"
)


@pytest.fixture
def pointer(tmp_path, monkeypatch):
    monkeypatch.setattr(conftest, "LARGE_FIXTURES", tmp_path)
    (tmp_path / "x.perfetto-trace").write_bytes(POINTER)
    return "x.perfetto-trace"


def test_an_lfs_pointer_skips_with_how_to_fetch(pointer, monkeypatch):
    monkeypatch.delenv(conftest.REQUIRE_ENV, raising=False)
    with pytest.raises(pytest.skip.Exception, match="git lfs pull"):
        conftest.large_fixture(pointer)


def test_an_lfs_pointer_fails_where_fixtures_are_required(pointer, monkeypatch):
    monkeypatch.setenv(conftest.REQUIRE_ENV, "1")
    with pytest.raises(pytest.fail.Exception, match="Git LFS pointer"):
        conftest.large_fixture(pointer)


def test_a_real_trace_is_returned(tmp_path, monkeypatch):
    # The control: anything that is not a pointer is handed back as it is.
    monkeypatch.setattr(conftest, "LARGE_FIXTURES", tmp_path)
    (tmp_path / "y.perfetto-trace").write_bytes(b"\x0a\x00not a pointer")
    assert conftest.large_fixture("y.perfetto-trace") == tmp_path / "y.perfetto-trace"
