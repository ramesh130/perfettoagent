"""Build the eval cases from devicelab captures and superPlayer's source (ADR-0015).

    uv run python evals/build_cases.py --superplayer ../superPlayer          # write
    uv run python evals/build_cases.py --superplayer ../superPlayer --check  # compare

This is the only code that reads superPlayer, and it runs by hand, never from a test
(tech-stack: no test-time dependency on superPlayer). What it writes is committed:

- `evals/repos/superplayer.bundle`: the fixture repo, one branch per case, named by case
  id.
- `evals/cases/<id>/`: what the model sees. The two traces and `inputs.json` (the
  range).
- `evals/answers/<id>.json` and `evals/answers/patches/`: what the model must not see.

Each case's history starts at a snapshot of the exact superPlayer commit its baseline
trace was built from, minus everything that describes the plants (EXCLUDED). Then come
neutral commits: comment, KDoc, private-name, equivalent-rewrite and build-setting changes
that do not change what the app does, some of them in the plant's own files, and none
that either trace could contradict (`unseen_edits`). A planted case adds the plant as one commit
among them, at a position drawn per case. So the range's first commit is the baseline's
build and its last is the current trace's build plus changes that cannot move a trace:
the traces stay honest about the range, and attribution is still a search over diffs.

Commit dates, authors and order come from fixed data and a per-case seed, so a rebuild
from the same superPlayer commits gives the same shas; `--check` proves it.
"""

import argparse
import functools
import gzip
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from perfettoagent.query import query_trace

EVALS = Path(__file__).resolve().parent
ROOT = EVALS.parent
BUNDLE = EVALS / "repos" / "superplayer.bundle"
CASES = EVALS / "cases"
ANSWERS = EVALS / "answers"
TEST_FIXTURES = ROOT / "tests" / "fixtures" / "large"

# Left out of every snapshot. devicelab/ holds the plant patches and their README, and
# the docs, plans and changelog describe them or the captures; .github and benchmark
# name devicelab's scenarios, and third-party is 16 MB of prebuilt binaries nobody
# greps.
EXCLUDED = (
    "devicelab",
    "docs",
    "PRD.md",
    "CLAUDE.md",
    "CONTEXT.md",
    "CHANGELOG.md",
    ".github",
    "benchmark",
    "third-party",
)

# The superPlayer commits the captures were built from (each run's run.json).
STARTUP_BASE = "7b43b5fa05df6a1dd6e1497bf25b8078ade3977d"
JANK_BASE = "57e3144bca8c591023be8c764bf961c1892cd84d"
LEAK_BASE = "abc232cb33fb06bf5f9de62856012cd77c434c32"

# Where the plant patches are read from: superPlayer's main when the captures were made.
PLANTS_AT = "9fdd93c"

OUT = "devicelab/out"

# Fictional, so no real person is named as a culprit.
AUTHORS = (
    ("Priya Raman", "priya.raman@superplayer.invalid"),
    ("Tom Okafor", "tom.okafor@superplayer.invalid"),
    ("Lena Fischer", "lena.fischer@superplayer.invalid"),
)

# Neutral commits per range, besides the plant: the issue asks for at least 8.
NEUTRAL_PER_CASE = 9


@dataclass(frozen=True)
class Edit:
    """A commit that changes nothing the app does at run time: a comment, a private
    name, an equivalent rewrite or a build setting. An edit that stops matching its
    file fails the build instead of drifting: each literal `old` must occur exactly
    once, and each renamed identifier must occur and its new name must not."""

    message: str
    # (path, old text, new text)
    changes: tuple[tuple[str, str, str], ...] = ()
    # (path, old identifier, new identifier): every whole-word occurrence, comments
    # included
    renames: tuple[tuple[str, str, str], ...] = ()


FEED = "demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt"
MAIN = "demo/src/main/kotlin/com/superplayer/demo/MainActivity.kt"
CORE = "superplayer-core/src/main/kotlin/com/superplayer/core"
POOL = f"{CORE}/PlayerPool.kt"
PLAYER = f"{CORE}/SuperPlayer.kt"

# Edits every snapshot can take: the library and the build are the same in all three
# where these touch them.
SHARED_EDITS = (
    Edit(
        "Give the Gradle daemon 6 GB",
        changes=(
            (
                "gradle.properties",
                "org.gradle.jvmargs=-Xmx4g ",
                "org.gradle.jvmargs=-Xmx6g ",
            ),
        ),
    ),
    Edit(
        "Rename PlayerPool's newPlayer to buildPlayer",
        renames=((POOL, "newPlayer", "buildPlayer"),),
    ),
    Edit(
        "Rename PlayerPool.isReleased to hasBeenReleased",
        renames=((POOL, "isReleased", "hasBeenReleased"),),
    ),
    Edit(
        "Say when PlayerPool's sample releases the pool",
        changes=(
            (
                POOL,
                " * // When the screen goes away.",
                " * // When the screen goes away, after every player is back.",
            ),
        ),
    ),
    Edit(
        "Reword why PlayerPool.acquire can return null",
        changes=(
            (
                POOL,
                " * Because the bound is real. A pool that blocked would block the main thread;",
                " * Because the bound is real. A pool that blocked would stall the main thread;",
            ),
        ),
    ),
    Edit(
        "Rename isObjectMethod to isDeclaredByObject",
        renames=((PLAYER, "isObjectMethod", "isDeclaredByObject"),),
    ),
)

# The demo-side pool, for the startup and jank snapshots (the two differ only in the
# feed's tap handling, which none of these touch). The feed edits stay clear of every
# hunk the feed plants change, and rename nothing a plant's lines use, so each plant
# applies at any position among them.
DEMO_EDITS = SHARED_EDITS + (
    Edit(
        "Point the feed's KDoc at the refresh constant",
        changes=(
            (
                FEED,
                " * The header is sampled twice a second rather than observed.",
                " * The header is sampled every [SUMMARY_REFRESH_MS] rather than observed.",
            ),
        ),
    ),
    Edit(
        "Rename the feed's main-thread handler",
        renames=((FEED, "mainThread", "mainHandler"),),
    ),
    Edit(
        "Say why the feed builds one collector per player",
        changes=(
            (
                FEED,
                "        // A collector per player, because a collector measures one.",
                "        // A collector per player: each collector measures exactly one player.",
            ),
        ),
    ),
    Edit(
        "Rename FeedRow's hasFirstFrame to firstFrameShown",
        renames=((FEED, "hasFirstFrame", "firstFrameShown"),),
    ),
    Edit(
        "Acquire the watched row's player with takeIf",
        changes=(
            (
                FEED,
                "        val acquired = if (isCurrent) {\n"
                "            // Where the feed is, first: the pool then prefers the player holding this row warm.\n"
                "            feed.preload.setScrollPosition(index)\n"
                "            feed.pool.acquire()\n"
                "        } else {\n"
                "            null\n"
                "        }\n",
                "        // Where the feed is, first: the pool then prefers the player holding this row warm.\n"
                "        val acquired = isCurrent.takeIf { it }?.let {\n"
                "            feed.preload.setScrollPosition(index)\n"
                "            feed.pool.acquire()\n"
                "        }\n",
            ),
        ),
    ),
    Edit(
        "Say what FeedPlayback's first-frame callback receives",
        changes=(
            (
                FEED,
                " * [onFirstFrame] is called on the main thread with the row's content id.",
                " * [onFirstFrame] is called on the main thread with the row's content id and its first\n"
                " * frame.",
            ),
        ),
    ),
    Edit(
        "Name the Android release that made edge-to-edge the default",
        changes=(
            (
                MAIN,
                "        // From API 35 an app targeting 35+ is laid out edge to edge",
                "        // From API 35 (Android 15) an app targeting 35+ is laid out edge to edge",
            ),
        ),
    ),
    Edit(
        "Rename DemoApp's launchContentSent to launchContentHandedOver",
        renames=((MAIN, "launchContentSent", "launchContentHandedOver"),),
    ),
    Edit(
        "Say who ignores a second reportFullyDrawn",
        changes=(
            (
                MAIN,
                "An Activity reports once and\n    // ignores every later call,",
                "An Activity reports once and\n    // the platform ignores every later call,",
            ),
        ),
    ),
)

# The library-side pool, for the leak snapshot, which predates the demo's feed as the
# other snapshots have it. Most are in SuperPlayer.kt, the plant's own file, and none
# touches the lines the plant removes.
LIBRARY_EDITS = SHARED_EDITS + (
    Edit(
        "Say why onLowMemory is still forwarded",
        changes=(
            (
                PLAYER,
                "Forwarded anyway: on an API 24 device it",
                "Still forwarded: on an API 24 device it",
            ),
        ),
    ),
    Edit(
        "Reword where a measurement session begins",
        changes=(
            (
                PLAYER,
                "        // The one place a measurement session can begin,",
                "        // The only place a measurement session can begin,",
            ),
        ),
    ),
    Edit(
        "Say why restored memory goes in ahead of the media item",
        changes=(
            (
                PLAYER,
                "        // Ahead of the media item, so that the restored memory is in place before anything can read",
                "        // Before the media item, so that the restored memory is in place before anything can read",
            ),
        ),
    ),
    Edit(
        "Say which trim level means the app went to the background",
        changes=(
            (
                PLAYER,
                "                    // TRIM_MEMORY_UI_HIDDEN says the app went to the background and says nothing",
                "                    // TRIM_MEMORY_UI_HIDDEN only says the app went to the background, and nothing",
            ),
        ),
    ),
    Edit(
        "Rename lastKnownPositions to positionMemory",
        renames=((PLAYER, "lastKnownPositions", "positionMemory"),),
    ),
    Edit(
        "Spell out msd in the start-up reference",
        changes=(
            (
                PLAYER,
                "CMCD v2's `msd`\n        // (media start delay)",
                "CMCD v2's `msd` key\n        // (media start delay)",
            ),
        ),
    ),
    Edit(
        "Rename rememberPositionOfCurrentContent to rememberCurrentPosition",
        renames=(
            (PLAYER, "rememberPositionOfCurrentContent", "rememberCurrentPosition"),
        ),
    ),
    Edit(
        "Say why the session ends before the engine is released",
        changes=(
            (
                PLAYER,
                "        // Before the engine goes, so the session's terminal event is emitted while there is still",
                "        // Before the engine is released, so the session's terminal event is emitted while there is still",
            ),
        ),
    ),
    Edit(
        "Rename PlayerPool.inUse to lent",
        renames=((POOL, "inUse", "lent"),),
    ),
)
# The leak plant, as it was measured: the four lines of resetForReuse that remove every
# listener registered on a pooled player. The run commented them out; the culprit commit
# deletes them, which compiles to the same code and reads like a commit someone made.
LEAK_PLANT = Edit(
    "Trim resetForReuse",
    changes=(
        (
            PLAYER,
            "        delegate.clearMediaItems()\n"
            "\n"
            "        synchronized(wrappedListeners) {\n"
            "            wrappedListeners.values.forEach(delegate::removeListener)\n"
            "            wrappedListeners.clear()\n"
            "        }\n"
            "\n",
            "        delegate.clearMediaItems()\n\n",
        ),
    ),
)


@dataclass(frozen=True)
class Plant:
    name: str
    message: str
    patch: str | None = None  # a devicelab/plants patch, read at PLANTS_AT
    edit: Edit | None = None  # or an edit, for the plant that was never a patch file


PLANTS = {
    "startup-main-thread-io": Plant(
        "startup-main-thread-io",
        "Check the catalog cache at launch",
        patch="devicelab/plants/startup-main-thread-io.patch",
    ),
    "feed-tap-sleep": Plant(
        "feed-tap-sleep",
        "Let a quick second tap land on the paused row",
        patch="devicelab/plants/feed-tap-sleep.patch",
    ),
    "feed-grain-allocations": Plant(
        "feed-grain-allocations",
        "Veil the feed's stand-ins with a grain while it scrolls",
        patch="devicelab/plants/feed-grain-allocations.patch",
    ),
    "feed-row-remeasure": Plant(
        "feed-row-remeasure",
        "Fit each row's title to its width, and let the rows breathe",
        patch="devicelab/plants/feed-row-remeasure.patch",
    ),
    "listener-leak": Plant("listener-leak", LEAK_PLANT.message, edit=LEAK_PLANT),
}


@dataclass(frozen=True)
class Case:
    id: str
    base: str
    edits: tuple[Edit, ...]
    baseline: str  # a trace under superPlayer's devicelab/out
    current: str
    plant: str | None
    metrics: tuple[str, ...]
    # The roadmap's name for the regression, for people reading the answers.
    regression: str | None = None


def _run(stamp: str, scenario: str) -> str:
    return f"{OUT}/20260924T{stamp}-{scenario}/trace.perfetto-trace"


def _heap(stamp: str) -> str:
    return f"{OUT}/20260911T{stamp}-leak-hunt/heap-feed-final.perfetto-trace"


# Opaque ids (secrets.token_hex(4)), assigned in no order that says anything.
CASE_LIST = (
    Case(
        "275adbfb",
        STARTUP_BASE,
        DEMO_EDITS,
        _run("011856Z", "startup"),
        _run("012233Z", "startup"),
        "startup-main-thread-io",
        ("startup_ttid_ms",),
        "Main-thread I/O on startup",
    ),
    Case(
        "f21c443c",
        JANK_BASE,
        DEMO_EDITS,
        _run("033342Z", "jank"),
        _run("033945Z", "jank"),
        "feed-grain-allocations",
        ("frame_ui_time_p95_ms", "gc_time_ms"),
        "Allocation storm",
    ),
    Case(
        "69dc18c7",
        JANK_BASE,
        DEMO_EDITS,
        _run("033342Z", "jank"),
        _run("033648Z", "jank"),
        "feed-tap-sleep",
        ("main_thread_blocked_ms",),
        "Synchronous sleep",
    ),
    Case(
        "c89d5055",
        JANK_BASE,
        DEMO_EDITS,
        _run("033342Z", "jank"),
        _run("034233Z", "jank"),
        "feed-row-remeasure",
        ("frame_ui_time_p95_ms", "jank_frames_pct"),
        "Layout thrash",
    ),
    Case(
        "462439ff",
        LEAK_BASE,
        LIBRARY_EDITS,
        # A clean run's final feed dump against the planted run's, both after six
        # passes.
        _heap("151106Z"),
        _heap("144545Z"),
        "listener-leak",
        ("heap_growth_objects_by_class",),
        "Listener leak",
    ),
    # Clean pairs: a baseline against a second clean capture of the same build.
    Case(
        "571fe43e",
        STARTUP_BASE,
        DEMO_EDITS,
        _run("011856Z", "startup"),
        _run("012633Z", "startup"),
        None,
        (),
    ),
    Case(
        "c69ee38f",
        STARTUP_BASE,
        DEMO_EDITS,
        _run("013010Z", "startup"),
        _run("013758Z", "startup"),
        None,
        (),
    ),
    Case(
        "b021c1fb",
        JANK_BASE,
        DEMO_EDITS,
        _run("033342Z", "jank"),
        _run("034924Z", "jank"),
        None,
        (),
    ),
    Case(
        "f37266c8",
        JANK_BASE,
        DEMO_EDITS,
        _run("035208Z", "jank"),
        _run("040632Z", "jank"),
        None,
        (),
    ),
    Case(
        "65f39dfe",
        JANK_BASE,
        DEMO_EDITS,
        _run("040915Z", "jank"),
        _run("042341Z", "jank"),
        None,
        (),
    ),
)

# Captures already committed as test fixtures. A case reuses those bytes rather than
# compressing the capture again, so Git LFS stores each trace once.
REUSED_FIXTURES = {
    _run("011856Z", "startup"): "startup-a-baseline.perfetto-trace.gz",
    _run("012233Z", "startup"): "startup-a-current.perfetto-trace.gz",
    _run("012633Z", "startup"): "startup-a-rerun.perfetto-trace.gz",
    _run("033342Z", "jank"): "jank-a-baseline.perfetto-trace.gz",
    _run("034924Z", "jank"): "jank-a-rerun.perfetto-trace.gz",
    _run("033945Z", "jank"): "jank-b-current.perfetto-trace.gz",
    _run("034233Z", "jank"): "jank-c-current.perfetto-trace.gz",
    _run("033648Z", "jank"): "jank-d-current.perfetto-trace.gz",
}

# The fixed clock every history is laid out on.
EPOCH = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)


class Repo:
    """A scratch repo whose objects come from superPlayer's through alternates, so
    building a snapshot copies nothing and the bundle carries only what the cases reach.
    """

    def __init__(self, path: Path, superplayer: Path):
        self.path = path
        self.superplayer = superplayer
        self.git("init", "-q")
        objects = superplayer / ".git" / "objects"
        (path / ".git" / "objects" / "info" / "alternates").write_text(f"{objects}\n")
        self.index = path / "scratch-index"

    def git(self, *args: str, input: str | None = None, env: dict | None = None) -> str:
        return subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=self.path,
            input=input,
            env={**os.environ, "GIT_INDEX_FILE": str(self.index), **(env or {})}
            if hasattr(self, "index")
            else None,
            capture_output=True,
            text=True,
            check=True,
        ).stdout

    def snapshot(self, base: str) -> str:
        self.git("read-tree", base)
        self.git("rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *EXCLUDED)
        return self.git("write-tree").strip()

    def edit(self, tree: str, edit: Edit) -> str:
        self.git("read-tree", tree)
        # Changes to one file apply in order, each to the text the one before left.
        texts: dict[str, str] = {}

        def text_of(path: str) -> str:
            if path not in texts:
                texts[path] = self.git("cat-file", "blob", f"{tree}:{path}")
            return texts[path]

        for path, old, new in edit.changes:
            found = text_of(path).count(old)
            if found != 1:
                raise SystemExit(
                    f"{edit.message!r}: {old!r} is in {path} {found} times, not once"
                )
            texts[path] = texts[path].replace(old, new)
        for path, old, new in edit.renames:
            if _word(new).search(text_of(path)):
                raise SystemExit(f"{edit.message!r}: {new} is already a name in {path}")
            texts[path], found = _word(old).subn(new, texts[path])
            if not found:
                raise SystemExit(f"{edit.message!r}: no {old} in {path}")
        for path, text in texts.items():
            mode = self.git("ls-tree", tree, "--", path).split()[0]
            blob = self.git("hash-object", "-w", "--stdin", input=text).strip()
            self.git("update-index", "--cacheinfo", f"{mode},{blob},{path}")
        return self.git("write-tree").strip()

    def patch(self, tree: str, patch: str) -> str:
        self.git("read-tree", tree)
        self.git("apply", "--cached", "-", input=patch)
        return self.git("write-tree").strip()

    def commit(self, tree: str, parent: str | None, message: str, author, when) -> str:
        name, email = author
        stamp = when.strftime("%Y-%m-%dT%H:%M:%S+0000")
        env = {
            "GIT_AUTHOR_NAME": name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_AUTHOR_DATE": stamp,
            "GIT_COMMITTER_NAME": name,
            "GIT_COMMITTER_EMAIL": email,
            "GIT_COMMITTER_DATE": stamp,
        }
        parents = ["-p", parent] if parent else []
        return self.git("commit-tree", tree, *parents, "-m", message, env=env).strip()


def _word(identifier: str) -> re.Pattern:
    """An identifier as a whole word, so renaming `inUse` leaves `inUseCount` alone."""
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])")


def plant_patch(superplayer: Path, plant: Plant) -> str:
    return subprocess.run(
        ["git", "show", f"{PLANTS_AT}:{plant.patch}"],
        cwd=superplayer,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def check_provenance(superplayer: Path, case: Case) -> None:
    """Each trace was built from the case's base commit, and a planted one with exactly
    the patch this builds the culprit from: run.json records both."""
    for side, trace in (("baseline", case.baseline), ("current", case.current)):
        run = json.loads((superplayer / trace).parent.joinpath("run.json").read_text())
        commit = run["superplayer"]["commit"]
        if commit != case.base:
            raise SystemExit(f"{case.id} {side}: built from {commit}, not {case.base}")
        planted = run.get("plant")
        if case.plant is None or side == "baseline":
            if planted is not None:
                raise SystemExit(
                    f"{case.id} {side}: run carries plant {planted['name']}"
                )
        elif PLANTS[case.plant].patch:
            patch = plant_patch(superplayer, PLANTS[case.plant]).encode()
            if (
                planted is None
                or planted["patch_sha256"] != hashlib.sha256(patch).hexdigest()
            ):
                raise SystemExit(
                    f"{case.id} current: run's plant is not {case.plant} as read"
                )


def build_history(
    repo: Repo, superplayer: Path, case: Case
) -> tuple[str, str, str | None]:
    """The case's range (base, head) and its culprit, if it has one."""
    rng = random.Random(case.id)
    edits = rng.sample(unseen_edits(superplayer, case), NEUTRAL_PER_CASE)
    steps: list[Edit | Plant] = list(edits)
    if case.plant is not None:
        steps.insert(rng.randrange(len(steps) + 1), PLANTS[case.plant])

    tree = repo.snapshot(case.base)
    when = EPOCH
    base = head = repo.commit(tree, None, "Initial import", AUTHORS[0], when)
    culprit = None
    when += timedelta(days=1)
    for step in steps:
        if isinstance(step, Plant):
            tree = (
                repo.edit(tree, step.edit)
                if step.edit
                else repo.patch(tree, plant_patch(superplayer, step))
            )
        else:
            tree = repo.edit(tree, step)
        head = repo.commit(tree, head, step.message, rng.choice(AUTHORS), when)
        if isinstance(step, Plant):
            culprit = head
        when += timedelta(minutes=rng.randrange(40, 600))
    repo.git("update-ref", f"refs/heads/{case.id}", head)
    return base, head, culprit


def unseen_edits(superplayer: Path, case: Case) -> list[Edit]:
    """The case's edits that neither of its traces could contradict.

    A trace records some of the source it was built from: a heap dump names classes and
    fields (`PlayerPool.inUse`, `SuperPlayer$lastKnownPositions$1`), and a monitor
    contention slice names a method with its file and line. Both traces come from the
    range's base (plus the plant), so a range that renamed a name a trace records, or
    moved lines in a file a trace cites by line, would end at code the trace does not
    match. An edit is left out of a case when either trace records the old name of
    anything it renames, or cites a file it changes by line number."""
    seen = "\n".join(
        _recorded(superplayer / trace) for trace in (case.baseline, case.current)
    )
    unseen = [
        e
        for e in case.edits
        if not any(_word(old).search(seen) for _, old, _ in e.renames)
        and not any(f"{Path(path).name}:" in seen for path, _, _ in e.changes)
    ]
    if len(unseen) < NEUTRAL_PER_CASE:
        raise SystemExit(
            f"{case.id}: only {len(unseen)} edits its traces cannot contradict"
        )
    return unseen


@functools.cache
def _recorded(trace: Path) -> str:
    """Every slice name, heap class name and heap field name in the trace, one a line."""
    sql = (
        "SELECT DISTINCT name FROM slice"
        " UNION SELECT DISTINCT name FROM heap_graph_class"
        " UNION SELECT DISTINCT field_name FROM heap_graph_reference"
    )
    rows = query_trace(sql, trace, max_rows=None)["rows"]
    return "\n".join(str(name) for (name,) in rows if name)


def gzipped(superplayer: Path, trace: str) -> bytes:
    """The capture, gzipped: the committed test fixture's bytes when it is one, checked
    to hold exactly this capture; otherwise compressed with no name or time in the
    header, so the same capture always gives the same bytes."""
    raw = (superplayer / trace).read_bytes()
    if trace in REUSED_FIXTURES:
        data = (TEST_FIXTURES / REUSED_FIXTURES[trace]).read_bytes()
        if gzip.decompress(data) != raw:
            raise SystemExit(f"{REUSED_FIXTURES[trace]} is not {trace}")
        return data
    return gzip.compress(raw, compresslevel=9, mtime=0)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--superplayer", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="compare, write nothing")
    args = parser.parse_args()
    superplayer = args.superplayer.resolve()

    with tempfile.TemporaryDirectory() as scratch:
        repo = Repo(Path(scratch), superplayer)
        built = {}
        for case in CASE_LIST:
            check_provenance(superplayer, case)
            built[case.id] = build_history(repo, superplayer, case)

        if args.check:
            return check(built)

        BUNDLE.parent.mkdir(parents=True, exist_ok=True)
        repo.git("bundle", "create", "-q", str(BUNDLE), "--branches")
        for case in CASE_LIST:
            write_case(repo, superplayer, case, *built[case.id])
    return 0


def write_case(repo: Repo, superplayer: Path, case: Case, base, head, culprit) -> None:
    directory = CASES / case.id
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for side, trace in (("baseline", case.baseline), ("current", case.current)):
        (directory / f"{side}.perfetto-trace.gz").write_bytes(
            gzipped(superplayer, trace)
        )
    inputs = {"schema": 1, "repo": "superplayer", "range": {"base": base, "head": head}}
    _write_json(directory / "inputs.json", inputs)

    patch = None
    if case.plant is not None:
        plant = PLANTS[case.plant]
        patch = f"patches/{plant.name}.patch"
        text = (
            plant_patch(superplayer, plant)
            if plant.patch
            else repo.git("diff-tree", "-p", "--no-commit-id", culprit)
        )
        (ANSWERS / "patches").mkdir(parents=True, exist_ok=True)
        (ANSWERS / patch).write_text(text)
    answer = {
        "schema": 1,
        "verdict": "regression" if case.plant else "no_regression",
        "metrics": list(case.metrics),
        "culprit": culprit,
        "regression": case.regression,
        "plant": case.plant,
        "patch": patch,
        "provenance": {
            "source_commit": case.base,
            "baseline_trace": case.baseline,
            "current_trace": case.current,
        },
    }
    _write_json(ANSWERS / f"{case.id}.json", answer)


def check(built: dict) -> int:
    """Every case's range and culprit as committed, from a rebuild: 0 when they
    match."""
    stale = []
    for case in CASE_LIST:
        base, head, culprit = built[case.id]
        inputs = json.loads((CASES / case.id / "inputs.json").read_text())
        answer = json.loads((ANSWERS / f"{case.id}.json").read_text())
        if (
            inputs["range"] != {"base": base, "head": head}
            or answer["culprit"] != culprit
        ):
            stale.append(case.id)
    for case_id in stale:
        print(
            f"{case_id}: rebuilt range differs from the committed one", file=sys.stderr
        )
    return 1 if stale else 0


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


if __name__ == "__main__":
    sys.exit(main())
