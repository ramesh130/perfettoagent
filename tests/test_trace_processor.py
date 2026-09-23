"""Download, verification and caching of the pinned trace processor, all offline.

Every test builds a fake release archive and serves it through an injected fetch
function, so nothing here touches the network or needs the real binary.
"""

import hashlib
import os
import stat
import zipfile
from pathlib import Path

import pytest

from perfettoagent.trace_processor import (
    PERFETTO_VERSION,
    TraceProcessorError,
    download,
    resolve_trace_processor,
)

PLATFORM = "mac-arm64"
FAKE_BINARY = b"#!/bin/sh\necho fake trace processor\n"


def make_archive(
    tmp_path: Path, platform: str = PLATFORM, binary: bytes = FAKE_BINARY
) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    archive = tmp_path / f"{platform}.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{platform}/trace_processor_shell", binary)
        zf.writestr(f"{platform}/other_tool", b"not wanted")
    return archive


def pin_file_for(tmp_path: Path, digest: str, platform: str = PLATFORM) -> Path:
    pins = tmp_path / "pins.sha256"
    pins.write_text(f"# comment\n{PERFETTO_VERSION} {platform} {digest}\n")
    return pins


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeFetch:
    """Stands in for the GitHub download: copies a local archive, counts the calls."""

    def __init__(self, archive: Path):
        self.archive = archive
        self.urls: list[str] = []

    def __call__(self, url: str, dest: Path) -> None:
        self.urls.append(url)
        dest.write_bytes(self.archive.read_bytes())


@pytest.fixture
def archive(tmp_path):
    return make_archive(tmp_path)


def resolve(tmp_path, fetch, pins, **kwargs):
    kwargs.setdefault("env", {})
    return resolve_trace_processor(
        cache_dir=tmp_path / "cache",
        fetch=fetch,
        pin_file=pins,
        platform=PLATFORM,
        **kwargs,
    )


def test_matching_archive_is_downloaded_verified_and_installed(tmp_path, archive):
    fetch = FakeFetch(archive)
    binary = resolve(tmp_path, fetch, pin_file_for(tmp_path, sha256(archive)))

    assert fetch.urls == [
        f"https://github.com/google/perfetto/releases/download/v{PERFETTO_VERSION}/{PLATFORM}.zip"
    ]
    install_dir = tmp_path / "cache" / f"trace-processor-{PERFETTO_VERSION}-{PLATFORM}"
    assert binary == install_dir / "trace_processor_shell"
    assert binary.read_bytes() == FAKE_BINARY
    assert os.stat(binary).st_mode & stat.S_IXUSR
    # Only the binary is kept: no archive or partial download is left in the cache.
    assert sorted(p.name for p in binary.parent.iterdir()) == [
        "trace_processor_shell",
        "trace_processor_shell.sha256",
    ]


def test_second_use_runs_from_cache_without_downloading(tmp_path, archive):
    fetch = FakeFetch(archive)
    pins = pin_file_for(tmp_path, sha256(archive))
    first = resolve(tmp_path, fetch, pins)
    second = resolve(tmp_path, fetch, pins)
    assert first == second
    assert len(fetch.urls) == 1


def test_mismatched_archive_is_refused_and_never_installed(tmp_path, archive):
    fetch = FakeFetch(archive)
    pins = pin_file_for(tmp_path, "0" * 64)
    with pytest.raises(TraceProcessorError, match="does not match its pinned sha256"):
        resolve(tmp_path, fetch, pins)
    cache = tmp_path / "cache"
    assert [p for p in cache.rglob("*") if p.is_file()] == []


def test_tampered_archive_is_refused(tmp_path, archive):
    pins = pin_file_for(tmp_path, sha256(archive))
    tampered = make_archive(tmp_path / "evil", binary=b"#!/bin/sh\necho pwned\n")
    with pytest.raises(TraceProcessorError, match="refusing to run it"):
        resolve(tmp_path, FakeFetch(tampered), pins)


def test_corrupted_cached_binary_is_found_and_replaced_not_run(tmp_path, archive):
    fetch = FakeFetch(archive)
    pins = pin_file_for(tmp_path, sha256(archive))
    binary = resolve(tmp_path, fetch, pins)
    binary.write_bytes(FAKE_BINARY[:10])  # as an interrupted write would leave it

    again = resolve(tmp_path, fetch, pins)
    assert len(fetch.urls) == 2
    assert again.read_bytes() == FAKE_BINARY


def test_corrupted_cache_is_refused_when_downloading_is_off(tmp_path, archive):
    fetch = FakeFetch(archive)
    pins = pin_file_for(tmp_path, sha256(archive))
    binary = resolve(tmp_path, fetch, pins)
    binary.write_bytes(b"half")
    with pytest.raises(TraceProcessorError, match="not cached"):
        resolve(tmp_path, fetch, pins, allow_download=False)


def test_empty_cache_without_download_is_an_error_not_a_fetch(tmp_path, archive):
    fetch = FakeFetch(archive)
    with pytest.raises(TraceProcessorError, match="not cached"):
        resolve(
            tmp_path,
            fetch,
            pin_file_for(tmp_path, sha256(archive)),
            allow_download=False,
        )
    assert fetch.urls == []


def test_archive_without_the_binary_is_refused(tmp_path):
    archive = tmp_path / "empty.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr(f"{PLATFORM}/something_else", b"x")
    with pytest.raises(TraceProcessorError, match="has no"):
        resolve(tmp_path, FakeFetch(archive), pin_file_for(tmp_path, sha256(archive)))


def test_platform_without_a_pin_is_refused_before_downloading(tmp_path, archive):
    fetch = FakeFetch(archive)
    pins = pin_file_for(tmp_path, sha256(archive), platform="linux-amd64")
    with pytest.raises(TraceProcessorError, match="no pinned sha256"):
        resolve(tmp_path, fetch, pins)
    assert fetch.urls == []


def test_unsupported_host_is_refused(tmp_path, archive):
    with pytest.raises(TraceProcessorError, match="TRACE_PROCESSOR"):
        resolve_trace_processor(
            cache_dir=tmp_path,
            fetch=FakeFetch(archive),
            env={},
            host=("Windows", "AMD64"),
        )


def test_trace_processor_env_overrides_the_download(tmp_path, archive):
    own = tmp_path / "my_tp"
    own.write_bytes(FAKE_BINARY)
    own.chmod(0o755)
    fetch = FakeFetch(archive)
    binary = resolve(
        tmp_path,
        fetch,
        pin_file_for(tmp_path, "0" * 64),
        env={"TRACE_PROCESSOR": str(own)},
    )
    assert binary == own
    assert fetch.urls == []


def test_trace_processor_env_must_be_executable(tmp_path, archive):
    own = tmp_path / "not_executable"
    own.write_bytes(FAKE_BINARY)
    with pytest.raises(TraceProcessorError, match="not executable"):
        resolve(tmp_path, FakeFetch(archive), None, env={"TRACE_PROCESSOR": str(own)})


def test_default_download_reads_a_url_to_a_file(tmp_path, archive):
    # file:// goes through the same urllib path as https://, with no socket.
    dest = tmp_path / "got.zip"
    download(archive.as_uri(), dest)
    assert dest.read_bytes() == archive.read_bytes()


def test_repo_pin_file_covers_every_supported_host(tmp_path, archive):
    # With the repo's own pins, a fake archive is refused on every platform: the pins
    # are real digests, not placeholders that happen to match anything.
    for platform in ("mac-arm64", "mac-amd64", "linux-amd64", "linux-arm64"):
        fake = make_archive(tmp_path / platform, platform=platform)
        with pytest.raises(
            TraceProcessorError, match="does not match its pinned sha256"
        ):
            resolve_trace_processor(
                cache_dir=tmp_path / "cache",
                fetch=FakeFetch(fake),
                env={},
                platform=platform,
            )
