# The second app is JetNews (Q1), after the user's expense tracker proved too simple

Open question Q1 asked which open-source app builds fastest on Apple silicon with the API 36 emulator, and it blocks roadmap item 8. The roadmap named three candidates: Now in Android, Tivi and Signal-Android. This diverges from that list at the user's direction.
- The user's first choice was their own app, `ramesh130/vibe-android-expense-tracker`.
- After its trial, they asked for an app that fits the evals better and still builds on this 16 GB host while other work runs. That request named Tivi and Signal-Android as too heavy for this host and Now in Android as borderline. None of the three was tried, because the first alternative tried fit.

The second app is **JetNews**, from Google's `android/compose-samples` (Apache-2.0), at commit `0bbd72d` (2026-09-18). Affects `docs/roadmap.md` (Q1, item 8) and issue #34.

## How each candidate was tried

The host was Apple silicon with 16 GB, JDK 17 (`openjdk@17` 17.0.18) and the `superplayer_verify_36` AVD (API 36, 1080×2400, headless).
- **Builds:** each ran `./gradlew assembleDebug --max-workers=2 --no-daemon --no-build-cache` in a fresh clone outside this repo.
  - The **cold** build came first, when the app's Gradle version was not yet downloaded. The **re-run** came after it, with dependencies cached, using `--rerun-tasks`.
  - Peak memory is the summed RSS of the Java processes each build started, sampled every second. That means the Gradle daemon, the Kotlin daemon and the wrapper.
- **Startups:** each was `am start -W -S -n <package>/<activity>`, run six times after a force-stop.
- **Traces:** one scratch trace per app, captured with `linux.ftrace` (atrace `am`, `wm`, `view`, `gfx`, `dalvik`) and `android.surfaceflinger.frametimeline`. Each was read with the pinned trace processor (58.2). No trace is committed.

| | Expense tracker | JetNews |
|---|---|---|
| Source | `ramesh130/vibe-android-expense-tracker`, 2 commits | `android/compose-samples` `0bbd72d`, `JetNews/` |
| Licence | none | Apache-2.0; fonts under SIL OFL 1.1 (`ASSETS_LICENSE`) |
| App Kotlin files (main) | 4, of which `MainActivity.kt` is 503 lines, all the app's UI and state | 55, across data, UI, navigation, deep links and a widget |
| Gradle / AGP / Kotlin | 8.13 / 8.11.1 / 2.0.21 | 9.5.0 / 9.3.1 / 2.4.20 |
| compileSdk / targetSdk | 35 / 35 | 37 / 33 |
| Built unchanged on JDK 17 | yes | yes |
| Cold build, wall time | 117 s | 156 s |
| Cached re-run, wall time | 15–16 s | 21 s |
| Peak Java RSS | 1993 MB (re-run) | 2433 MB (cold), 2283 MB (re-run) |
| Cold starts, `am start -W` TotalTime (ms) | 1025, 925, 876, 900, 904, 949 | 1124, 902, 890, 889, 911, 892 |
| `android_startups` in the trace | 2 of 2 cold starts, 1350.5 and 1414.7 ms against TotalTime 1350 and 1414 | 2 of 2 cold starts, 1081.4 and 1080.5 ms against TotalTime 1081 and 1080 |
| Scrolling list | empty at launch; 25 expenses typed in through `adb shell input` took about 205 s, and a cold start empties it again | the home feed loads offline fake data 800 ms after launch; no seeding |
| Frames in the trace | 242 app frames in `actual_frame_timeline_slice`, 393 `Choreographer#doFrame` | 458 app frames, 668 `Choreographer#doFrame` |

In every run, WaitTime was 1–3 ms above TotalTime. The cold build pulled that app's Gradle distribution. In the expense tracker's case it also triggered the next item.

**Side effect on the shared SDK.** The expense tracker's first build made AGP auto-install Build-Tools 35.0.0 into `~/Library/Android/sdk`. The SDK had only 36.0.0 before. It is still there.

Measured memory stayed well under a 6 GB budget. During the JetNews cold build, swap use stayed at 3630.75 MB before and after, and memory was 41% free once the build finished.

**Inspected only, not built:** two other Compose samples in the same repo, at the same commit.
- **Reply:** 27 Kotlin files, no `INTERNET` permission, no `Application` subclass.
- **Jetsnack:** it declares `INTERNET` and loads its images over the network.
JetNews fit on the first try, so neither was needed.

## Why the expense tracker was too simple

It builds fast and starts cold on API 36, and `android_startups` sees its startups. Three things rule it out as an eval app:
- **Attribution would be a lookup.** All of its UI and state are in one 503-line `MainActivity.kt`. A range of 10–12 commits under ADR-0015 would have nearly every commit touch that file. `git log -- <file>` would then no longer narrow anything, and the diffs could only be told apart by reading one file.
- **No place for the listener leak.** The app has no pool, no listener, no repository and no second screen. The leak plant would bring its whole mechanism with it, which is the screen-for-the-eval problem ADR-0007 rejected.
- **The scroll scenario needs heavy seeding.** The list is in memory and starts empty. Typing entries in costs about 8 s each, and every cold start loses them. A repeatable scroll would need a seed hook added to the app for the eval.

It also has no licence. ADR-0015's approach snapshots the app's source into this Apache-2.0 repo's eval bundle, so it would first need one.

## Where the five plants go in JetNews

These mirror superPlayer's five plants from roadmap item 5, each against the same metric. All paths are under `JetNews/app/src/main/java/com/example/jetnews/`.

| Plant | Where it goes | Scenario | Expected metric |
|---|---|---|---|
| Main-thread I/O on startup | `JetnewsApplication.onCreate`, before `AppContainerImpl` is built. The app already has its own `Application`, so ADR-0007's adaptation (the patch brings the subclass) is not needed. | cold starts | `startup_ttid_ms` |
| Allocation storm | A draw modifier on `PostCardSimple` (`ui/home/PostCards.kt`), the row of the feed's "recommended" section, sized as in ADR-0008. | scroll the home feed | `frame_ui_time_p95_ms`, `gc_time_ms` |
| Synchronous sleep | `Thread.sleep(120)` in the bookmark click path, where `PostCardSimple`'s `BookmarkButton` calls `onToggleFavorite`. | tap bookmarks on the feed | `main_thread_blocked_ms` |
| Layout thrash | A forced re-measure of each `PostCardSimple` and `PostCardHistory` row every frame, with `PostTitle` fitted to the row's width, as in ADR-0008. | scroll the home feed | `frame_ui_time_p95_ms`, `jank_frames_pct` |
| Listener leak | A favourites listener that each feed row registers with `FakePostsRepository` (`data/posts/impl/`) and never removes. #34 settles one question here. In ADR-0015's leak case the culprit deletes existing removal lines, which would need the registration and its removal in the base snapshot. The alternative is a culprit that adds a registration with no removal. | navigate home → post → back, repeatedly, with heap dumps | `heap_growth_objects_by_class` |

The plants are spread over `JetnewsApplication.kt`, `ui/home/PostCards.kt` and `data/posts/impl/FakePostsRepository.kt`. ADR-0015's neutral commits and decoys can then land across the app's 55 files. The decoys can go in screens no scenario opens: the interests screen, the post screen's share and "not available" actions, the Glance widget and deep links.

## Risks to carry into #34 and #35

- **Licence and attribution.** Apache-2.0 allows the snapshot. Only `JetNews/` goes in, not the whole samples repo. The snapshot must add the samples repo's root `LICENSE`, which is not inside `JetNews/`, keep `JetNews/ASSETS_LICENSE`, since the fonts are under SIL OFL 1.1, and say it is a modified copy.
- **A short feed.** The home feed has 11 posts in four `LazyColumn` items: top, recommended, popular (a horizontal row) and history. A fifth item, search, appears only on expanded screens. Rows inside a section are a `Column`, so they are not lazily composed. The scratch trace's 12 swipes gave 458 frames. That is enough for frame metrics, but a single swipe reaches the end. If #34's captures need a longer scroll, the base snapshot can repeat the fake posts in `PostsData.kt`. That is a data change in the base, not a hook added for the eval, and it applies to every case alike.
- **A fake network.** `FakePostsRepository.getPostsFeed` waits 800 ms and fails every fifth call in a process. A cold start is a new process, so its first load succeeds. A scenario that pulls to refresh four times would hit the failure.
- **No TTFD.** JetNews never calls `reportFullyDrawn`, so `startup_ttfd_ms` reads `no_data` (ADR-0014). `startup_ttid_ms` is the startup plant's metric, as it was on superPlayer.
- **A different toolchain from superPlayer.** JetNews uses AGP 9.3.1, Gradle 9.5.0 and compileSdk 37, and the host has platform `android-37.0` installed. Its targetSdk is 33, below the AVD's 36. It ran without a compatibility prompt, but the captures should record it.
- **Noise must be measured again.** ADR-0009, ADR-0011 and ADR-0013 sized their thresholds on superPlayer alone. The first of six JetNews starts, straight after install, was 1124 ms against 889–911 ms for the other five. #34 should measure clean spreads before sizing plants, as ADR-0008 did.
