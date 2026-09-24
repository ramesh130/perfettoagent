# JetNews plants and captures live in a private repo, sized from JetNews's own noise

Issue #34 applies the five plants to the second app, JetNews (ADR-0017), and captures each against clean runs on the API 36 emulator. This records where that work lives, the noise it was sized from, each plant's size, the leak question ADR-0017 left open, and what every capture shows. Affects `docs/roadmap.md` (item 8) and issue #35, which turns these captures into cases. Nothing in this repo reads them: there is no runtime or test-time dependency on JetNews, the new repo or devicelab, and no trace is added here.

## Where it lives: `ramesh130/jetnews-perf`, private

A new private repo, at the user's direction. It holds:

| Path | What |
|---|---|
| `JetNews/` | `android/compose-samples` at `0bbd72d`, only `JetNews/`, with `ASSETS_LICENSE` kept |
| `LICENSE`, `NOTICE.md` | the samples repo's root Apache-2.0 licence, and a notice that `JetNews/` is a modified copy |
| `harness/` | `harness/lab run <scenario> [--plant <name>]`, adapted from superPlayer's `devicelab/` |
| `plants/` | the five patches, and a README with the sizing tables below |
| `runs/<run_id>/` | one capture each: `run.json`, `trace.perfetto-trace.gz`, the Perfetto config, screenshots before and after the measured part, and `plant.patch` for a planted run |

- **The base snapshot.** The first commit is upstream `JetNews/` unchanged. The second is the only change to the app: the home feed's "recommended" and "history" sections repeat their posts ten times, each copy with its own id. ADR-0017 allowed this. The sample's 11 posts scroll past in one swipe, so a scroll would mostly measure the list's end.
- **The harness is copied, not imported** (ADR-0015's lesson). It keeps devicelab's detached Perfetto sessions, its plant apply-build-revert procedure and its `run.json` shape. The Perfetto fragments (`base`, `startup`, `jank`, `frametimeline`, `java_hprof`) are devicelab's, copied byte for byte. It drops what JetNews does not need: booting emulators, Maven local and the stale-artifact check, and playback probes.
- **What a run records.** Every `run.json` has:
  - `base_commit`, the jetnews-perf commit it was built from;
  - `app.source_tree`, the git tree id of `JetNews/` at that commit;
  - for a planted run, `plant.patch_sha256` and `plant.base_commit`, with `plant.patch` copied in.

  All 37 runs record the same `source_tree`, `f756bb2`, across five `base_commit`s. Only the harness and the plants changed between those commits. A check run before the push found each planted run's `plant.patch`, its recorded sha256 and the patch in `plants/` identical. The `apk_sha256` is not an identity: debug builds of the same tree gave different APKs across sessions.
- **Size.** 37 runs, 537.8 MB, all plain git. The largest run is 47.5 MB, a layout-thrash trace with its screenshots, and every file is under GitHub's 100 MB limit. So the repo needs no Git LFS, and this repo's LFS quota is untouched.

## Scenarios

The emulator was `superplayer_verify_36`, booted with devicelab's flags (`-no-window -no-audio -gpu swiftshader_indirect -no-snapshot-load`). It is userdebug, so `su` works. The build is `./gradlew assembleDebug --max-workers=2` on JDK 17.

| Scenario | What it drives | Data sources |
|---|---|---|
| `startup` | 20 cold starts, page cache dropped before each, after one untraced warm-up launch | `startup`, `frametimeline` |
| `scroll` | 3 rounds of 6 flings down the feed and 6 back, after the same plan once untraced | `jank`, `frametimeline` |
| `bookmarks` | 6 taps on the first recommended row's bookmark, 2 s apart, at the feed's top | `jank`, `frametimeline` |
| `leak` | 10 passes of home → top story → Back, two forced GCs, then one Java heap dump | `java_hprof` |

ADR-0017's tap scenario gets a scenario of its own. superPlayer's feed takes a tap anywhere, so its taps could end each scroll round. JetNews's bookmark is a 48 dp button, and it sits still only when the feed does.

## Noise, measured first

Every value in this ADR comes from this repo's metric library, run on the capture with the pinned trace processor 58.2. The spread is the largest clean value minus the smallest.

| Scenario | Clean runs | Metric | Range | Spread |
|---|---:|---|---|---:|
| startup | 7 | `startup_ttid_ms` | 837.51–987.67 | 150.16 |
| scroll | 7 | `frame_ui_time_p95_ms` | 25.72–29.82 | 4.10 |
| scroll | 7 | `jank_frames_pct` | 12.23–30.82 | 18.59 |
| scroll | 7 | `gc_time_ms` | 32.61–70.07 | 37.46 |
| bookmarks | 5 | `main_thread_blocked_ms` | 0.00–0.02 | 0.02 |
| leak | 3 | `heap_growth_objects_by_class`, headline delta between clean runs | −183 to +146 | |

Against superPlayer's numbers (ADR-0009, ADR-0011, ADR-0013):
- **TTID's spread is larger (150 against 105 ms), and it is drift.** Three clean runs at 11:13–11:21 UTC read 944–988 ms. Four from 12:17 on read 838–859 ms. The build and the scenario were the same, and the host was running other work, so a threshold taken from one session would understate it.
- **UI time and blocked time are quieter** than superPlayer's (4.10 against 6.90 ms, and 0.02 against 29.7 ms), with no video player behind the feed.
- **Jank is as noisy.** `jank_frames_pct` has a spread of 18.59 points here against 17.60 on superPlayer.
- `startup_ttfd_ms` reads NULL on every run, as ADR-0017 predicted: JetNews never calls `reportFullyDrawn`.

## Each plant's size

The rule is ADR-0008's: size each plant so its smallest planted value clears the largest clean value by more than the clean spread. The pilots that sized a plant were made from earlier sizes of its patch. Their traces are not kept, and their rows are in jetnews-perf's `plants/README.md`.

| Plant (jetnews-perf name) | Where | Size | Why that size |
|---|---|---|---|
| Startup I/O (`startup-article-cache`) | `JetnewsApplication.onCreate`, before `AppContainerImpl` | reads and CRC-checks a 768 MiB file | 192 MiB gave 1083 ms (a 0.6× gap). 384 MiB gave 1145–1196 ms (1.0×, lost in the drift). 768 MiB gives 3.6×. |
| Allocation storm (`feed-card-grain`) | a `drawWithContent` on `PostCardSimple`, invalidated every frame by `withFrameNanos` | 6,000 boxed floats per row per draw; the recommended section composes 30 rows, so 180,000 a frame | Redrawn only when the row moved (`onGloballyPositioned`), it never ran (GC time 27.73 ms): a scrolled `LazyColumn` does not redraw its items, as superPlayer's pilots found. 2,000 and 4,000 a row gave UI time gaps of 0.9× and 2.1×. |
| Sleep (`bookmark-hold`) | `PostCardSimple`'s `BookmarkButton` click, after `onToggleFavorite` | `Thread.sleep(120)` | The roadmap's size. The first run cleared the clean runs by 36,000×. |
| Layout thrash (`feed-row-fit`) | every `PostCardSimple` and `PostCardHistory` row | padding breathes by 4 dp; `PostTitle` is fitted to the row in three lines, 14 to 24 sp in 0.25 sp steps | ADR-0008's 0.05 sp steps drew a frame every 120 ms. Driven by hand, that build took a fling as a tap and opened a post, and the pilot's traced pass held just 24 text layouts: it did not measure the feed. 0.25 sp does a fifth of the layouts. |
| Listener leak (`bookmark-listener`) | `PostsRepository.addFavoritesListener`, and a `remember` in `PostCardSimple` that registers one | no removal; 30 rows register per visit to home | 10 passes, where superPlayer's leak hunt makes 6. Each pass adds 30 listeners, so the plant adds 300 over the passes plus 60 more from the launch and the warm-up. A clean pair moves no class by more than 107. |

After that pilot, every run saves a screenshot before and after its measured part, because the harness reads nothing off the screen. Every scroll run's `after.png` shows the home feed. Every one also shows the fake network's "Can't update latest news" snackbar. The flings back to the top pull to refresh, and ADR-0017's every-fifth-load failure then fires. The snackbar appears in clean and planted runs alike.

## The leak: the culprit adds a registration with no removal

ADR-0017 left two shapes open:
- the base carries a registration and its removal, and the culprit deletes the removal, as in superPlayer's leak case (ADR-0015);
- or the culprit adds a registration with no removal.

This takes the second.

- **The base stays upstream's code.** JetNews has no listener API. Its favourites are a `StateFlow` that the view model collects, and that cannot leak this way. For the first shape, the base would need a listener API, a registration and a removal. That code would exist only so that a plant could delete one line: a hook for the eval, which ADR-0007 and ADR-0017 rule out. The feed repeat changes only data.
- **It is a real bug's shape.** Someone adds a callback API, registers from a composable in `remember`, and forgets the `DisposableEffect` that would remove it. The diff is the evidence. To attribute it, the agent has to see what the diff leaves out: `addFavoritesListener` with no `remove`, and a registration with no disposal. That is the same reading superPlayer's deleted lines ask for.
- **The cost.**
  - The culprit is larger: four files, 26 added lines and 2 changed, against four deleted lines on superPlayer.
  - Its lambda is D8's synthetic `PostCardsKt$$ExternalSyntheticLambda2`, so the heap names the file but not the listener. A clean build has 30 objects of a different lambda under that same name.
  - For #35's builder, no neutral commit may touch `PostsRepository.kt`, `FakePostsRepository.kt`, `BlockingFakePostsRepository.kt` or the lines of `PostCards.kt` this patch uses. Nor may one rename `PostCardsKt`'s composables, which the heap records.

## What each capture shows

Each pair's baseline is a clean run from the same session, captured just before the current run. The delta is current − baseline, from the metric itself.

| Pair | Metric | Baseline | Current | Delta | Runs (baseline → current) |
|---|---|---:|---:|---:|---|
| startup I/O | `startup_ttid_ms` | 839.50 | 1596.43 | +756.93 | `20260924T123421Z` → `20260924T125501Z` |
| startup I/O | `startup_ttid_ms` | 854.85 | 1529.76 | +674.91 | `20260924T125758Z` → `20260924T130037Z` |
| startup I/O | `startup_ttid_ms` | 858.88 | 1544.55 | +685.67 | `20260924T130331Z` → `20260924T130610Z` |
| startup clean | `startup_ttid_ms` | 839.50 | 854.85 | +15.35 | `20260924T123421Z` → `20260924T125758Z` |
| startup clean | `startup_ttid_ms` | 854.85 | 858.88 | +4.03 | `20260924T125758Z` → `20260924T130331Z` |
| storm | `frame_ui_time_p95_ms` | 26.21 | 54.17 | +27.96 | `20260924T115742Z` → `20260924T120949Z` |
| storm | `frame_ui_time_p95_ms` | 26.55 | 54.88 | +28.33 | `20260924T121218Z` → `20260924T122254Z` |
| storm | `frame_ui_time_p95_ms` | 25.72 | 54.62 | +28.90 | `20260924T122522Z` → `20260924T123945Z` |
| storm | `gc_time_ms` | 32.61 | 5854.49 | +5821.88 | `20260924T115742Z` → `20260924T120949Z` |
| storm | `gc_time_ms` | 50.84 | 6821.92 | +6771.08 | `20260924T121218Z` → `20260924T122254Z` |
| storm | `gc_time_ms` | 45.02 | 6289.39 | +6244.37 | `20260924T122522Z` → `20260924T123945Z` |
| thrash | `frame_ui_time_p95_ms` | 26.30 | 103.76 | +77.46 | `20260924T112635Z` → `20260924T115456Z` |
| thrash | `frame_ui_time_p95_ms` | 26.55 | 103.14 | +76.59 | `20260924T121218Z` → `20260924T121441Z` |
| thrash | `frame_ui_time_p95_ms` | 25.72 | 100.52 | +74.80 | `20260924T122522Z` → `20260924T123136Z` |
| thrash | `jank_frames_pct` | 12.68 | 41.80 | +29.12 | `20260924T112635Z` → `20260924T115456Z` |
| thrash | `jank_frames_pct` | 12.72 | 40.55 | +27.83 | `20260924T121218Z` → `20260924T121441Z` |
| thrash | `jank_frames_pct` | 12.23 | 38.01 | +25.78 | `20260924T122522Z` → `20260924T123136Z` |
| scroll clean | `frame_ui_time_p95_ms` | 26.21 | 26.55 | +0.34 | `20260924T115742Z` → `20260924T121218Z` |
| scroll clean | `frame_ui_time_p95_ms` | 26.55 | 25.72 | −0.83 | `20260924T121218Z` → `20260924T122522Z` |
| scroll clean | `frame_ui_time_p95_ms` | 25.72 | 27.49 | +1.77 | `20260924T122522Z` → `20260924T124214Z` |
| scroll clean | `jank_frames_pct` | 12.23 | 13.81 | +1.58 | `20260924T122522Z` → `20260924T124214Z` |
| scroll clean | `gc_time_ms` | 45.02 | 52.62 | +7.60 | `20260924T122522Z` → `20260924T124214Z` |
| sleep | `main_thread_blocked_ms` | 0.00 | 729.71 | +729.71 | `20260924T112957Z` → `20260924T114105Z` |
| sleep | `main_thread_blocked_ms` | 0.01 | 727.70 | +727.69 | `20260924T122745Z` → `20260924T122815Z` |
| sleep | `main_thread_blocked_ms` | 0.00 | 729.42 | +729.42 | `20260924T124436Z` → `20260924T124507Z` |
| bookmarks clean | `main_thread_blocked_ms` | 0.01 | 0.00 | −0.01 | `20260924T122745Z` → `20260924T124436Z` |
| leak | `heap_growth_objects_by_class` | 399535 | 401322 | +1787 | `20260924T113026Z` → `20260924T114136Z` |
| leak | `heap_growth_objects_by_class` | 399498 | 401352 | +1854 | `20260924T122846Z` → `20260924T123011Z` |
| leak | `heap_growth_objects_by_class` | 399498 | 401221 | +1723 | `20260924T122846Z` → `20260924T124538Z` |
| leak clean | `heap_growth_objects_by_class` | 399535 | 399352 | −183 | `20260924T113026Z` → `20260924T113151Z` |
| leak clean | `heap_growth_objects_by_class` | 399352 | 399498 | +146 | `20260924T113151Z` → `20260924T122846Z` |

- **Every plant shows on its expected metric.**
  - Startup I/O: each delta is more than four times the clean spread.
  - Storm: each UI-time delta is more than six times the spread, and each GC delta more than 150 times.
  - Thrash: each UI-time delta is more than 18 times the spread.
  - Sleep: 727.69–729.71 ms against a spread of 0.02 ms, six sleeps of about 120 ms each.
  - Leak: the breakdown's top rows are the plant's own. The listener lambda grows +330 (30 → 360: twelve visits to home of 30 rows each, less the 30 a clean build has under the same name). Its `SnapshotMutableStateImpl$StateStateRecord` grows +720, and `ParcelableSnapshotMutableState` and `AtomicInt` +360 each. On the clean pairs no class moves by more than 107 (`float[]`).
- **No clean pair shows such a delta.** Each scalar clean pair is under its metric's spread, and under a tenth of the plant's delta, the test ADR-0013 applies. The leak's clean headline deltas (−183, +146) are about a tenth of the planted ones (+1723 to +1854). There, as on superPlayer (ADR-0015), the breakdown carries the finding: the listener grows +330, and no class grows by more than 107 between two clean runs.
- **What does not separate is recorded, as ADR-0011 does.** `jank_frames_pct`, layout thrash's second metric, does not clear the clean runs. The smallest thrash run (38.01) is 7.19 points above the largest clean run (30.82), which is less than the 18.59-point spread. Its pair deltas above (+25.78 to +29.12) look clear only because their baselines are low-jank runs. A clean pair from the first session reads +18.14 (`20260924T112635Z` → `20260924T112412Z`). A diagnosis of the thrash case should rest on UI time.
- **The storm also moves jank**, to 100.00 on all three runs, because every frame is late.

## Toolchain notes

- **JDK 17 by path.** The first pilot inherited JDK 25 from the shell's `JAVA_HOME`. The harness now always takes `/usr/libexec/java_home -v 17`. That run was discarded.
- **Debug builds.** As the issue asked, the captured APK is the debug build, so every `run.json` says `debuggable: true`. That differs from superPlayer, whose `benchmark` build type is not debuggable. The release build type here is minified, and a heap dump from it would need the R8 mapping. Every capture, clean or planted, is the same kind of build. Roadmap item 7 turns `debuggable: true` into a caveat, which #35's sanitised run metadata should carry.
- **Toolchain as ADR-0017 found it:** Gradle 9.5.0, AGP 9.3.1, Kotlin 2.4.20, compileSdk 37, targetSdk 33 (below the AVD's 36). There was no compatibility prompt. A cached build took a few seconds.
- **Captures were sequential**, one run at a time. Two kept runs were captured while earlier traces were being analysed on the host: `20260924T114105Z` (sleep) and `20260924T114136Z` (leak). Their values match the later runs of the same plant (729.71 ms against 727.70–729.42, and +1787 objects against +1723 to +1854).
- The emulator was shut down after the last capture.

## Consequences

- **#35 can build the JetNews cases from this repo alone:**
  - the base from `app.source_tree`;
  - the culprits from `plants/` and their recorded sha256;
  - the traces from `runs/`.

  Its builder must leave out `harness/`, `plants/`, `runs/`, `NOTICE.md`'s list of changes and this repo's commit messages, as ADR-0015 leaves out devicelab's. Those name the plants.
- **Enough clean runs for the pairs.** There are three planted runs per plant and at least three clean pairs per scenario, so #35 can meet roadmap item 5's rule of at least as many clean pairs as planted cases.
- **The thresholds here are this app's.** ADR-0009's, ADR-0011's and ADR-0013's were superPlayer's, and like theirs these come from one emulator and one afternoon.
