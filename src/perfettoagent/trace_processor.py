"""Perfetto's trace processor, pinned: the one binary perfettoagent reads a trace with.

Downloaded rather than vendored, because it is a 13 MB native binary per host platform.
Pinned twice over: the version is PERFETTO_VERSION, and the release archive must match
the sha256 in `trace-processor.sha256` next to this file. An archive that does not is
refused rather than run, so a version bump that forgets its hashes fails, loudly, on
first use.

Cached under ~/.cache/perfettoagent, so a machine downloads it once per version.
TRACE_PROCESSOR=/path/to/trace_processor_shell skips all of this for a machine with no
network. Whoever sets it vouches for the binary: nothing checks it.

Ported from devicelab's lib/trace_processor.sh (same author, Apache-2.0).

ref: https://perfetto.dev/docs/analysis/trace-processor
ref: https://github.com/google/perfetto/releases
"""

import hashlib
import os
import platform as host_platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from collections.abc import Callable, Mapping
from pathlib import Path

# The version devicelab also pins (docs/tech-stack.md): both tools read traces alike.
PERFETTO_VERSION = "58.2"

PIN_FILE = Path(__file__).with_name("trace-processor.sha256")

# ref: https://github.com/google/perfetto/releases/tag/v58.2 (one zip per platform)
RELEASE_URL = (
    "https://github.com/google/perfetto/releases/download/v{version}/{platform}.zip"
)

# Long enough for a 13 MB archive on a slow link; short enough that a stall fails.
DOWNLOAD_TIMEOUT_S = 300

# A query running longer than this is a runaway (a cross join, say), not an analysis.
QUERY_TIMEOUT_S = 300

BINARY_NAME = "trace_processor_shell"

# Perfetto's release asset names, by `platform.system()` and `platform.machine()`.
_PLATFORMS = {
    ("Darwin", "arm64"): "mac-arm64",
    ("Darwin", "x86_64"): "mac-amd64",
    ("Linux", "x86_64"): "linux-amd64",
    ("Linux", "aarch64"): "linux-arm64",
    ("Linux", "arm64"): "linux-arm64",
}

# Writes the body at a URL to a local file. Injectable so tests never need a network.
Fetch = Callable[[str, Path], None]


class TraceProcessorError(RuntimeError):
    """The trace processor could not be found, verified or run."""


def default_cache_dir() -> Path:
    return Path.home() / ".cache" / "perfettoagent"


def download(url: str, dest: Path) -> None:
    """The default `Fetch`: writes the body at `url` to `dest`."""
    try:
        with (
            urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_S) as response,
            dest.open("wb") as out,
        ):
            shutil.copyfileobj(response, out)
    except OSError as e:
        raise TraceProcessorError(f"could not download {url}: {e}") from e


def resolve_trace_processor(
    *,
    env: Mapping[str, str] | None = None,
    cache_dir: Path | None = None,
    allow_download: bool = True,
    fetch: Fetch = download,
    pin_file: Path | None = None,
    platform: str | None = None,
    host: tuple[str, str] | None = None,
) -> Path:
    """Returns the pinned trace_processor_shell's path, downloading it on first use.

    `TRACE_PROCESSOR` in `env` (default: the process environment) wins over everything.
    With `allow_download=False`, a missing or corrupt cache is an error, not a download.
    `platform` or `host` (`uname -s`, `uname -m`) default to this machine's.
    """
    env = os.environ if env is None else env
    override = env.get("TRACE_PROCESSOR")
    if override:
        path = Path(override)
        if not (path.is_file() and os.access(path, os.X_OK)):
            raise TraceProcessorError(f"TRACE_PROCESSOR={override} is not executable")
        return path

    if platform is None:
        platform = _platform_for(
            *(host or (host_platform.system(), host_platform.machine()))
        )
    pinned = _pinned_sha256(PERFETTO_VERSION, platform, pin_file or PIN_FILE)
    cache_dir = cache_dir or default_cache_dir()
    install_dir = cache_dir / f"trace-processor-{PERFETTO_VERSION}-{platform}"
    binary = install_dir / BINARY_NAME
    record = install_dir / f"{BINARY_NAME}.sha256"

    # The binary's own hash is recorded when it is extracted from a checked archive and
    # compared on every use after that, so a cache left half-written by an interrupted
    # run is found, not run.
    if (
        binary.is_file()
        and record.is_file()
        and _sha256_of(binary) == record.read_text().strip()
    ):
        return binary
    if not allow_download:
        raise TraceProcessorError(
            f"trace_processor_shell {PERFETTO_VERSION} for {platform} is not cached "
            f"in {install_dir}"
        )

    install_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"perfettoagent: downloading Perfetto {PERFETTO_VERSION}'s trace processor "
        f"for {platform} into {install_dir}",
        file=sys.stderr,
    )
    with tempfile.TemporaryDirectory(dir=install_dir, prefix=".download-") as work:
        archive = Path(work) / f"{platform}.zip"
        fetch(RELEASE_URL.format(version=PERFETTO_VERSION, platform=platform), archive)
        if _sha256_of(archive) != pinned:
            raise TraceProcessorError(
                f"the downloaded Perfetto {PERFETTO_VERSION} archive for {platform} "
                "does not match its pinned sha256; refusing to run it"
            )
        member = f"{platform}/{BINARY_NAME}"
        extracted = Path(work) / BINARY_NAME
        try:
            with (
                zipfile.ZipFile(archive) as zf,
                zf.open(member) as src,
                extracted.open("wb") as out,
            ):
                shutil.copyfileobj(src, out)
        except (KeyError, zipfile.BadZipFile) as e:
            raise TraceProcessorError(
                f"the Perfetto {PERFETTO_VERSION} archive has no {member}"
            ) from e
        extracted.chmod(0o755)
        # A rename within one directory is atomic, so a concurrent run sees the old
        # binary or the new one. The record goes last: a binary without one is
        # downloaded again.
        os.replace(extracted, binary)
        record.write_text(_sha256_of(binary) + "\n")
    return binary


def run_sql_script(binary: Path, trace: Path, script: str) -> str:
    """Runs `script` on `trace` and returns stdout.

    Every statement that returns rows prints them as CSV, one result set after another,
    separated by a blank line. The script goes in on stdin, so no SQL is ever read as a
    command-line flag. SQL file access stays off (trace processor's default), and the
    trace is loaded into memory, never written.

    ref: https://perfetto.dev/docs/analysis/trace-processor#shell
    """
    if not trace.is_file():
        # trace processor also accepts URLs; a local file is the only input we read.
        raise TraceProcessorError(f"no trace file at {trace}")
    try:
        result = subprocess.run(
            [str(binary), "query", "-f", "-", str(trace)],
            input=script,
            capture_output=True,
            # Trace strings are UTF-8 whatever the locale; a stray invalid byte in one
            # must not lose the whole result.
            encoding="utf-8",
            errors="replace",
            timeout=QUERY_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise TraceProcessorError(
            f"trace processor query timed out after {QUERY_TIMEOUT_S}s"
        ) from e
    if result.returncode != 0:
        raise TraceProcessorError(_error_from(result.stderr))
    return result.stdout


def _error_from(stderr: str) -> str:
    # A SQL error follows the trace-loading log as a Python-style traceback: keep that.
    start = stderr.find("Traceback")
    if start >= 0:
        detail = stderr[start:]
    else:
        detail = "\n".join(stderr.strip().splitlines()[-20:])
    return f"trace processor failed:\n{detail.strip()}"


def _platform_for(system: str, machine: str) -> str:
    try:
        return _PLATFORMS[(system, machine)]
    except KeyError:
        raise TraceProcessorError(
            f"Perfetto publishes no trace processor for a {system} {machine} host; "
            "set TRACE_PROCESSOR to one you built"
        ) from None


def _pinned_sha256(version: str, platform: str, pin_file: Path) -> str:
    for line in pin_file.read_text().splitlines():
        fields = line.split()
        if len(fields) == 3 and fields[0] == version and fields[1] == platform:
            return fields[2]
    raise TraceProcessorError(
        f"no pinned sha256 for Perfetto {version} on {platform}; "
        f"add the release's digest to {pin_file}"
    )


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
