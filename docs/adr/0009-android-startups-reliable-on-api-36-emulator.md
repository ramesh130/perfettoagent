# `android_startups` is reliable on API 36 emulator traces (Q4), and a startup metric is the median cold start

Open question Q4 asked whether Perfetto's `android.startup.startups` stdlib module can be trusted on API 36 emulator traces, and it blocked the startup metrics (roadmap item 3, issue #7). It can. The metrics `startup_ttid_ms` and `startup_ttfd_ms` use it, with `android.startup.time_to_display` for TTID and TTFD, and both `INCLUDE` lines are the first lines of their `sql_used`. No fallback SQL is needed. Affects `docs/roadmap.md` (item 3, Q4) and `src/perfettoagent/metrics/`.

## The evidence

All eight startup captures from issue #5 (superPlayer PR #391) were checked on the pinned trace processor (58.2). They are three baselines, three regressed runs and two clean re-runs, each of 20 cold launches of `com.superplayer.demo` on the `superplayer_verify_36` emulator, all captured with `frametimeline`. Each startup was compared with two records the trace processor does not read: devicelab's `am start -W` output and the run's logcat.

| Check | Result over 8 runs |
|---|---|
| Startups found | 160 of 160. Every run gives 20, all `package = com.superplayer.demo`, `startup_type = cold`. |
| `android_startups.dur` against `am start -W` TotalTime | Within 1.09 ms on every launch. The mean absolute difference is 0.44–0.58 ms per run. |
| TTID against logcat's `Displayed … +N ms` | TTID is 0.1–25.5 ms shorter on every launch, 2.9–5.5 ms on average per run. TTID ends when the app's RenderThread finishes its first frame, and `Displayed` ends later, when the window is shown. Nothing is off by a frame or more, except for single launches of up to 25.5 ms. |
| TTID and TTFD present | 160 of 160 each. |
| TTFD against logcat's `Fully drawn … +N ms` | TTFD is 67–85 ms longer on average per run, ranging from −0.6 to +203 ms on a single launch. `Fully drawn` stops at the `reportFullyDrawn` call, and TTFD runs on to the end of the next frame, so it should be longer by about a frame or more. |

Logcat is missing the first one or two launches of some runs, because it was cleared after they happened. Those launches were compared with `am start -W` only.

**Caveat:** TTID is NULL unless the trace also records `frametimeline`. PR #391's first pilot, without it, found every startup and no TTID at all. The TTID metric's description says so, so a NULL reads as a capture problem and not as a fast start.

## One number from 20 starts: the median cold start

Each trace holds 20 cold starts, and a metric reports one number per trace. It reports the **median, by nearest rank**: the value at rank ⌈n/2⌉, which is the 10th of 20.

Per-run values from the metric itself, in ms:

| Run | TTID p50 | TTFD p50 |
|---|---:|---:|
| B1 (clean) | 349.68 | 2077.31 |
| C1 (clean) | 345.47 | 2282.74 |
| B2 (clean) | 425.90 | 2432.04 |
| C2 (clean) | 386.76 | 2422.63 |
| B3 (clean) | 450.71 | 2687.14 |
| R1 (regressed) | 664.88 | 2723.99 |
| R2 (regressed) | 702.78 | 2675.63 |
| R3 (regressed) | 738.24 | 2896.38 |

- **p50, not p95.** Over the hour of captures, the clean runs' p95 drifted from 456 to 813 ms, a spread of 357 ms. Their p50 stayed within 105.24 ms. On p95, the gap between the smallest regressed value and the largest clean one is 67 ms (880 against 813). On p50 it is 214 ms (664.88 against 450.71), twice the clean spread. With 20 samples, p95 by nearest rank is the 19th start, so two slow launches set it. The mission's own example says "p95", so this is a choice to argue in a diagnosis, not a default to assume. A p95 metric can be added as its own file if a case needs one.
- **Nearest rank, not interpolated.** The reported number is one real start's value. A claim can then cite that start, and there is no average of two starts that no launch actually had.
- **Cold starts only.** A warm or hot start skips process creation and `Application.onCreate`, so if they were mixed in, the median would depend on the mix of start types rather than on the code.
- **One app.** The app is the package with the most cold starts, with ties broken by name. So a launcher or system app that starts during the capture is not mixed into its distribution. Starts with no TTID or TTFD are left out of the median rather than counted as 0. A trace with no such start reads NULL.

## TTFD does not separate this plant from clean runs

The superPlayer demo calls `reportFullyDrawn` at its first video frame, so TTFD includes a network fetch. Its clean p50s span 609.83 ms, and the regressed runs fall inside that span: R2 (2675.63) is below B3 (2687.14). `startup_ttid_ms` is the metric that detects the main-thread I/O plant, as the roadmap's plant table expects. `startup_ttfd_ms` is shipped because a real alert may be on TTFD, but on this app a TTFD delta smaller than about 610 ms is within the noise of clean runs.

## Consequences

- The fixture tests treat "meaningful" as larger than the clean spread measured here: 105.24 ms for TTID and 609.83 ms for TTFD. The regressed pair's TTID delta must be more than twice that spread, and the clean pair's delta must be less than it.
- These numbers come from one emulator, one app and one hour of captures. A second app (roadmap item 8) should re-check the spread before a threshold is reused.
