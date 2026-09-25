"""Build the JetNews eval cases from jetnews-perf's captures (ADR-0021, ADR-0028).

    uv run python evals/build_jetnews_cases.py --jetnews-perf ../jetnews-perf          # write
    uv run python evals/build_jetnews_cases.py --jetnews-perf ../jetnews-perf --check  # compare

The second app's cases, built as `build_cases.py` builds superPlayer's (ADR-0015), and
with its history code (`lay_out_history`, `unseen_edits`, `Repo`, `Edit`). This is the
only code that reads jetnews-perf (github.com/ramesh130/jetnews-perf), and it runs by hand, never from a
test. What it writes is committed:

- `evals/repos/jetnews.bundle`: the fixture repo, one branch per case.
- `evals/cases/<id>/`: the two traces, `inputs.json` and `run.json`.
- `evals/answers/<id>.json` and `evals/answers/patches/`.

Every capture was built from the same app source: jetnews-perf's `JetNews/` directory,
tree `SOURCE_TREE`, which every run.json records as `app.source_tree`. That tree, less
upstream's README images (EXCLUDED), is each case's root commit: `harness/`, `plants/`,
`runs/` and `NOTICE.md`, which name the plants, are outside it. A planted case's culprit applies the patch its current run
recorded, `runs/<id>/plant.patch`, whose sha256 the run.json also records; its paths
lose their `JetNews/` prefix, as the fixture repo's root is that directory.
"""

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from build_cases import (
    ANSWERS,
    CASES,
    Edit,
    Repo,
    lay_out_history,
    unseen_edits,
)

EVALS = Path(__file__).resolve().parent
BUNDLE = EVALS / "repos" / "jetnews.bundle"

# The fixture repo's name in each case's inputs.json.
REPO_NAME = "jetnews"

# jetnews-perf's `JetNews/` at every capture: the one app source all 37 runs record.
SOURCE_TREE = "f756bb2642f4f83574280e5f42ee5838e02ea81f"

# Left out of the root: upstream's README images (8.3 MB of GIF and PNG), which the app
# does not build and a plain-git bundle would carry for every case.
EXCLUDED = ("screenshots",)

# The prefix a jetnews-perf patch's paths carry, which the fixture repo's paths do not.
PATCH_STRIP = 2  # a/JetNews/app/... -> app/...

# Fictional, so no real person is named as a culprit.
AUTHORS = (
    ("Maya Chen", "maya.chen@jetnews.invalid"),
    ("Daniel Osei", "daniel.osei@jetnews.invalid"),
    ("Sofia Marquez", "sofia.marquez@jetnews.invalid"),
)

APP = "app/src/main/java/com/example/jetnews"
CARDS = f"{APP}/ui/home/PostCards.kt"
CONTAINER = f"{APP}/data/AppContainerImpl.kt"
HOME_VM = f"{APP}/ui/home/HomeViewModel.kt"
HOME = f"{APP}/ui/home/HomeScreens.kt"
JETNEWS_APP = f"{APP}/ui/JetnewsApp.kt"
MAIN = f"{APP}/ui/MainActivity.kt"
INTERESTS = f"{APP}/ui/interests/InterestsScreen.kt"
INTERESTS_VM = f"{APP}/ui/interests/InterestsViewModel.kt"
TOPIC_BUTTON = f"{APP}/ui/interests/SelectTopicButton.kt"
WIDGET = f"{APP}/glance/ui/JetnewsGlanceAppWidget.kt"
INTEGERS = "app/src/main/res/values/integers.xml"

# The pool every case draws from. None touches the lines a plant's hunks use, or a
# file the listener plant changes (the repository and both fakes, ADR-0021), and none
# renames an identifier a plant's lines or context use: `openDialog`, say, is in the
# bookmark plant's context. So each plant applies at any position among them.
EDITS = (
    # Changes in behaviour, in code none of the four scenarios runs: the home-screen
    # widget, the Interests screen and the history row's dialog are never opened.
    Edit(
        "Refresh the home-screen widget every half hour",
        decoy=True,
        changes=(
            (
                INTEGERS,
                "  <!-- Refresh widget every 1 hour -->\n"
                '  <integer name="widget_update_period_millis">3600000</integer>',
                "  <!-- Refresh widget every 30 minutes -->\n"
                '  <integer name="widget_update_period_millis">1800000</integer>',
            ),
        ),
    ),
    Edit(
        "Use smaller thumbnails on the Interests rows",
        decoy=True,
        changes=(
            (
                INTERESTS,
                "                    .size(56.dp)",
                "                    .size(48.dp)",
            ),
            (
                INTERESTS,
                "modifier.padding(start = 72.dp, top = 8.dp, bottom = 8.dp)",
                "modifier.padding(start = 64.dp, top = 8.dp, bottom = 8.dp)",
            ),
        ),
    ),
    Edit(
        "Make the topic selection button 40 dp",
        decoy=True,
        changes=(
            (
                TOPIC_BUTTON,
                "modifier.size(36.dp, 36.dp)",
                "modifier.size(40.dp, 40.dp)",
            ),
        ),
    ),
    Edit(
        "Pad the fewer-stories dialog's agree button to 16 dp",
        decoy=True,
        changes=(
            (
                CARDS,
                "                        .padding(15.dp)",
                "                        .padding(16.dp)",
            ),
        ),
    ),
    # Neutral: comments, private names, a build setting.
    Edit(
        "Give the Gradle daemon 3 GB",
        changes=(
            (
                "gradle.properties",
                "org.gradle.jvmargs=-Xmx2048m",
                "org.gradle.jvmargs=-Xmx3072m",
            ),
        ),
    ),
    Edit(
        "Reword AppContainer's KDoc",
        changes=(
            (
                CONTAINER,
                " * Dependency Injection container at the application level.\n */\ninterface",
                " * Holds the dependencies the whole application shares.\n */\ninterface",
            ),
        ),
    ),
    Edit(
        "Say when AppContainerImpl creates each repository",
        changes=(
            (
                CONTAINER,
                " * Variables are initialized lazily and the same instance is shared across the whole app.",
                " * Each repository is created on first use, and that one instance is shared across the whole app.",
            ),
        ),
    ),
    Edit(
        "Reword the home view model's comments",
        changes=(
            (
                HOME_VM,
                "    // UI state exposed to the UI",
                "    // The UI state, as the screen observes it",
            ),
            (
                HOME_VM,
                "        // Observe for favorite changes in the repo layer",
                "        // Observe favorite changes in the repository",
            ),
        ),
    ),
    Edit(
        "Say what refreshPosts shows first",
        changes=(
            (
                HOME_VM,
                "        // Ui state is refreshing",
                "        // Show that the feed is refreshing",
            ),
        ),
    ),
    Edit(
        "Reword toggleFavorite's KDoc",
        changes=(
            (
                HOME_VM,
                "     * Toggle favorite of a post",
                "     * Toggle whether a post is a favorite",
            ),
        ),
    ),
    Edit(
        "Reword HomeViewModel's KDoc",
        changes=(
            (
                HOME_VM,
                " * ViewModel that handles the business logic of the Home screen",
                " * The ViewModel holding the Home screen's business logic",
            ),
        ),
    ),
    Edit(
        "Say when the home screen offers a manual refresh",
        changes=(
            (
                HOME,
                "// if there are no posts, and no error, let the user refresh manually",
                "// with no posts and no error, let the user refresh by hand",
            ),
        ),
    ),
    Edit(
        "Say how the home screen shows its errors",
        changes=(
            (
                HOME,
                "    // Process one error message at a time and show them as Snackbars in the UI",
                "    // Show the error messages one at a time, each as a Snackbar",
            ),
        ),
    ),
    Edit(
        "Reword when the drawer opens by gesture",
        changes=(
            (
                JETNEWS_APP,
                "            // Only enable opening the drawer via gestures if the screen is not expanded",
                "            // The drawer opens by gesture only when the screen is not expanded",
            ),
        ),
    ),
    Edit(
        "Rename rememberSizeAwareDrawerState to rememberDrawerStateForSize",
        renames=(
            (JETNEWS_APP, "rememberSizeAwareDrawerState", "rememberDrawerStateForSize"),
        ),
    ),
    Edit(
        "Rename MainActivity's isOpenedByDeepLink to openedByDeepLink",
        renames=((MAIN, "isOpenedByDeepLink", "openedByDeepLink"),),
    ),
    Edit(
        "Rename HistoryPostPreview to PostCardHistoryPreview",
        renames=((CARDS, "HistoryPostPreview", "PostCardHistoryPreview"),),
    ),
    Edit(
        "Say which requests the Interests view model makes together",
        changes=(
            (
                INTERESTS_VM,
                "            // Trigger repository requests in parallel",
                "            // Request the topics, people and publications in parallel",
            ),
        ),
    ),
    Edit(
        "Reword the widget's loading comment",
        changes=(
            (
                WIDGET,
                "        // Load data needed to render the composable.",
                "        // Load what the composable needs to render.",
            ),
        ),
    ),
)


@dataclass(frozen=True)
class Plant:
    """A plant as its run recorded it: the patch in the run's directory."""

    name: str
    message: str
    patch: str

    def apply(self, repo: Repo, tree: str, source: Path) -> str:
        return repo.patch(tree, self.patch, strip=PATCH_STRIP)


# How the author of each plant would describe it, never as a regression.
PLANT_MESSAGES = {
    "startup-article-cache": "Check the offline article cache at launch",
    "feed-card-grain": "Lay a faint grain over the feed's cards",
    "bookmark-hold": "Let a quick second bookmark tap land after the first",
    "feed-row-fit": "Fit each post title to its row, and let the rows breathe",
    "bookmark-listener": "Follow the bookmark from the repository directly",
}


@dataclass(frozen=True)
class Case:
    id: str
    baseline: str  # a run id under jetnews-perf's runs/
    current: str
    plant: str | None
    metrics: tuple[str, ...]
    regression: str | None = None


def _run(stamp: str) -> str:
    return f"20260924T{stamp}"


# Opaque ids (secrets.token_hex(4)), assigned in no order that says anything. Each
# pair's baseline is a clean run of the same session, captured before its current run
# (ADR-0021's table).
CASE_LIST = (
    Case(
        "ba4d10bb",
        _run("123421Z"),
        _run("125501Z"),
        "startup-article-cache",
        ("startup_ttid_ms",),
        "Main-thread I/O on startup",
    ),
    Case(
        "2d80ed28",
        _run("115742Z"),
        _run("120949Z"),
        "feed-card-grain",
        ("frame_ui_time_p95_ms", "gc_time_ms"),
        "Allocation storm",
    ),
    Case(
        "68629563",
        _run("112957Z"),
        _run("114105Z"),
        "bookmark-hold",
        ("main_thread_blocked_ms",),
        "Synchronous sleep",
    ),
    # UI time only: on JetNews, jank does not clear the clean runs' spread (ADR-0021).
    Case(
        "3f05432d",
        _run("112635Z"),
        _run("115456Z"),
        "feed-row-fit",
        ("frame_ui_time_p95_ms",),
        "Layout thrash",
    ),
    Case(
        "e3a281bb",
        _run("113026Z"),
        _run("114136Z"),
        "bookmark-listener",
        ("heap_growth_objects_by_class",),
        "Listener leak",
    ),
    # Clean pairs: a baseline against a later clean capture of the same build.
    Case("33677800", _run("123421Z"), _run("125758Z"), None, ()),
    Case("9a0b7cd0", _run("115742Z"), _run("121218Z"), None, ()),
    Case("e04aeae9", _run("121218Z"), _run("122522Z"), None, ()),
    Case("d18a09bc", _run("122745Z"), _run("124436Z"), None, ()),
    Case("538c24e3", _run("113026Z"), _run("113151Z"), None, ()),
)


def run_json(source: Path, run: str) -> dict:
    return json.loads((source / "runs" / run / "run.json").read_text())


def trace(source: Path, run: str) -> Path:
    return source / "runs" / run / "trace.perfetto-trace.gz"


def plant_of(source: Path, case: Case) -> Plant | None:
    if case.plant is None:
        return None
    text = (source / "runs" / case.current / "plant.patch").read_text()
    return Plant(case.plant, PLANT_MESSAGES[case.plant], text)


def check_provenance(source: Path, case: Case) -> None:
    """Both runs built from SOURCE_TREE; the baseline clean; the current run carrying
    exactly the case's plant, as the patch whose sha256 it recorded, or none."""
    for side, run in (("baseline", case.baseline), ("current", case.current)):
        meta = run_json(source, run)
        if meta["app"]["source_tree"] != SOURCE_TREE:
            raise SystemExit(f"{case.id} {side}: not built from {SOURCE_TREE}")
        planted = meta.get("plant")
        expected = case.plant if side == "current" else None
        if (planted["name"] if planted else None) != expected:
            raise SystemExit(f"{case.id} {side}: run carries {planted}, not {expected}")
        if planted:
            patch = (source / "runs" / run / "plant.patch").read_bytes()
            if hashlib.sha256(patch).hexdigest() != planted["patch_sha256"]:
                raise SystemExit(f"{case.id} {side}: plant.patch is not what it ran")


def captured_on(case: Case) -> datetime:
    """Noon UTC on the day the current trace was captured, from its run id."""
    return datetime.strptime(case.current[:8], "%Y%m%d").replace(hour=12, tzinfo=UTC)


def build_history(repo: Repo, source: Path, case: Case) -> tuple[str, str, str | None]:
    traces = [trace(source, case.baseline), trace(source, case.current)]
    return lay_out_history(
        repo,
        source,
        case.id,
        root_tree=repo.without(SOURCE_TREE, EXCLUDED),
        unseen=unseen_edits(case.id, EDITS, traces),
        plant=plant_of(source, case),
        captured=captured_on(case),
        authors=AUTHORS,
    )


def run_metadata(source: Path, case: Case, head: str) -> dict:
    """The current run's metadata as the model may see it (ADR-0025): the range's
    head, built clean, and the build and device facts that do not name the plant.
    jetnews-perf's device record has no model or emulator field; the build
    fingerprint's device name and the emulator serial give them."""
    meta = run_json(source, case.current)
    device = meta["device"]
    return {
        "schema": 1,
        "commit": head,
        "tree_dirty": False,
        "debuggable": meta["app"]["debuggable"],
        "build_type": meta["app"]["build_type"],
        "device": {
            "model": device["build_fingerprint"].split("/")[1],
            "sdk": device["sdk"],
            "emulator": device["serial"].startswith("emulator-"),
        },
    }


def stripped(patch: str) -> str:
    """A jetnews-perf patch with the fixture repo's paths, as the culprit applies it."""
    return (
        patch.replace(" a/JetNews/", " a/")
        .replace(" b/JetNews/", " b/")
        .replace("--- a/JetNews/", "--- a/")
        .replace("+++ b/JetNews/", "+++ b/")
    )


def write_case(source: Path, case: Case, base: str, head: str, culprit) -> None:
    directory = CASES / case.id
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for side, run in (("baseline", case.baseline), ("current", case.current)):
        shutil.copyfile(trace(source, run), directory / f"{side}.perfetto-trace.gz")
    inputs = {"schema": 1, "repo": REPO_NAME, "range": {"base": base, "head": head}}
    _write_json(directory / "inputs.json", inputs)
    _write_json(directory / "run.json", run_metadata(source, case, head))

    patch = None
    plant = plant_of(source, case)
    if plant is not None:
        patch = f"patches/{plant.name}.patch"
        (ANSWERS / "patches").mkdir(parents=True, exist_ok=True)
        (ANSWERS / patch).write_text(stripped(plant.patch))
    answer = {
        "schema": 1,
        "verdict": "regression" if case.plant else "no_regression",
        "metrics": list(case.metrics),
        "culprit": culprit,
        "regression": case.regression,
        "plant": case.plant,
        "patch": patch,
        "provenance": {
            "source_tree": SOURCE_TREE,
            "baseline_trace": f"jetnews-perf runs/{case.baseline}",
            "current_trace": f"jetnews-perf runs/{case.current}",
        },
    }
    _write_json(ANSWERS / f"{case.id}.json", answer)


def check(source: Path, built: dict) -> int:
    """Every case's range, culprit and run.json as committed, from a rebuild."""
    stale = []
    for case in CASE_LIST:
        base, head, culprit = built[case.id]
        inputs = json.loads((CASES / case.id / "inputs.json").read_text())
        answer = json.loads((ANSWERS / f"{case.id}.json").read_text())
        metadata = json.loads((CASES / case.id / "run.json").read_text())
        if (
            inputs["range"] != {"base": base, "head": head}
            or answer["culprit"] != culprit
            or metadata != run_metadata(source, case, head)
        ):
            stale.append(case.id)
    for case_id in stale:
        print(
            f"{case_id}: rebuilt case differs from the committed one", file=sys.stderr
        )
    return 1 if stale else 0


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jetnews-perf", type=Path, required=True, dest="source")
    parser.add_argument("--check", action="store_true", help="compare, write nothing")
    args = parser.parse_args()
    source = args.source.resolve()

    with tempfile.TemporaryDirectory() as scratch:
        repo = Repo(Path(scratch), source)
        built = {}
        for case in CASE_LIST:
            check_provenance(source, case)
            built[case.id] = build_history(repo, source, case)
        if args.check:
            return check(source, built)
        BUNDLE.parent.mkdir(parents=True, exist_ok=True)
        repo.git("bundle", "create", "-q", str(BUNDLE), "--branches")
        for case in CASE_LIST:
            write_case(source, case, *built[case.id])
    return 0


if __name__ == "__main__":
    sys.exit(main())
