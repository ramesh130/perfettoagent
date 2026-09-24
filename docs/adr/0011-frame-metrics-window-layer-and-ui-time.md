# Frame metrics count the app's window layer, and a UI-time metric detects the per-frame plants

Issue #8 builds `jank_frames_pct`, `frame_p95_ms` and `frame_p99_ms` on the `android.frames.timeline` stdlib module. ADR-0008 left open whether the library also needs a metric for layout thrash, which `frame_p95_ms` barely separates from clean runs. This records how the frames are chosen, what "jank" means, and the answer: a fourth metric, `frame_ui_time_p95_ms`. It detects both per-frame plants (allocation storm and layout thrash), while the three timeline metrics detect at most one. Affects `docs/roadmap.md` (the item 3 table, and the item 5 "Expected metric" column) and `src/perfettoagent/metrics/`.

## Which frames

Each metric reads the stdlib's `android_frames_layers`: one row per app frame (a `Choreographer#doFrame` and its `DrawFrame`) and per SurfaceFlinger layer that has an actual-timeline row for that vsync. The full argument is in the header of `jank_frames_pct.sql`. In short:

- **The app's window layer only.** The layers named `*SurfaceView*` are dropped. A video `SurfaceView` gets timeline rows for the same vsync ids as the window, so it would count decoder buffers as UI frames. The stdlib's one-row-per-vsync `android_frames` points at a `SurfaceView` row for 563 of 701 frames on B1, and app jank read through it is 12.7%, against 54.7% on the window's own rows (superPlayer PR #392).
- **The app is the process with the most window frames.** SystemUI draws 2–3 frames during each capture.
- **Left out:** frames with no window timeline row (3–27 per fixture), and frames not yet presented when the trace stopped. `DISTINCT` on the timeline row, because the layers table can repeat a frame.
- **Percentiles by nearest rank,** as for the startup metrics (ADR-0009), so each reported number is one real frame's value.

Checked independently: all four metrics, on all four fixtures, round to the same 0.1 as superPlayer devicelab's own `frames.sql` and `frame_work.sql`. Those queries read the raw timeline table and doFrame slices, not these stdlib tables.

## Jank is `App Deadline Missed`

On the API 36 emulator, 94–100% of window frames carry some `jank_type`, mostly `Buffer Stuffing` and `Prediction Error`: that is the emulator's display pipeline, the same for every build. So `jank_frames_pct` counts a frame when its `jank_type` includes `App Deadline Missed`, meaning the app itself was late.

## Measured on all 15 jank captures

The runs are superPlayer PR #392's: six clean runs (B, C), and three each of the tap-sleep (S), allocation-storm (G) and layout-thrash (R) plants. All values come from the metrics themselves, on the pinned trace processor (58.2). `p50` is the same query at rank ⌈n/2⌉ and is not shipped.

| Run | `jank_frames_pct` | `frame_p95_ms` | `frame_p99_ms` | `frame_ui_time_p95_ms` | p50 |
|---|---:|---:|---:|---:|---:|
| B1 (clean) | 54.73 | 81.50 | 154.50 | 37.95 | 40.37 |
| C1 (clean) | 42.19 | 72.30 | 123.53 | 36.63 | 35.46 |
| B2 (clean) | 45.31 | 76.54 | 148.09 | 39.43 | 37.13 |
| C2 (clean) | 44.48 | 73.26 | 136.01 | 36.99 | 39.31 |
| B3 (clean) | 37.14 | 67.81 | 115.78 | 32.53 | 33.52 |
| C3 (clean) | 43.03 | 73.25 | 139.92 | 35.18 | 38.67 |
| G1 | 66.51 | 87.73 | 138.03 | 60.26 | 40.67 |
| G2 | 65.32 | 89.10 | 129.88 | 67.05 | 40.66 |
| G3 | 64.29 | 86.02 | 120.41 | 61.22 | 40.06 |
| R1 | 80.30 | 92.74 | 124.06 | 69.29 | 62.81 |
| R2 | 73.49 | 88.47 | 124.21 | 65.48 | 62.54 |
| R3 | 72.95 | 84.00 | 115.53 | 62.61 | 62.10 |
| S1 | 45.57 | 72.56 | 127.33 | 36.29 | 34.44 |
| S2 | 37.46 | 65.20 | 122.37 | 31.91 | 33.70 |
| S3 | 41.95 | 71.78 | 130.27 | 34.31 | 33.04 |

The **clean spread** is the largest minus the smallest value over the six clean runs. The gap is from the largest clean value to the smallest planted value; a negative gap means the plant overlaps the clean runs. ADR-0008 gave layout thrash's p95 gap as 2.7 ms, from devicelab's `frames.sql`. That query counts every window timeline row, including the few with no doFrame and DrawFrame that the stdlib does not match (3 in R1), so R3's p95 reads 84.2 there and 84.00 here.

| Metric | Clean spread | G gap | R gap |
|---|---:|---:|---:|
| `jank_frames_pct` | 17.60 points | 9.55 (0.5×) | 18.22 (1.04×) |
| `frame_p95_ms` | 13.69 ms | 4.52 (0.3×) | 2.50 (0.2×) |
| `frame_p99_ms` | 38.73 ms | −34.09 | −38.97 |
| p50 | 6.85 ms | −0.31 | 21.73 (3.2×) |
| `frame_ui_time_p95_ms` | 6.90 ms | 20.83 (3.0×) | 23.18 (3.4×) |

On the fixtures (B1 as baseline), the deltas are:

| Metric | G1 − B1 | R1 − B1 | C1 − B1 (the clean pair) |
|---|---:|---:|---:|
| `jank_frames_pct` | +11.78 | +25.57 | −12.54 |
| `frame_p95_ms` | +6.23 | +11.24 | −9.20 |
| `frame_p99_ms` | −16.47 | −30.44 | −30.97 |
| `frame_ui_time_p95_ms` | +22.31 | +31.34 | −1.32 |

## Decision: add `frame_ui_time_p95_ms`, and keep the three

`frame_ui_time_p95_ms` is the p95, by nearest rank, of the stdlib's UI time (`android_frames_ui_time`: a `Choreographer#doFrame`'s duration). It covers every doFrame of the thread that draws the app's window.

- **Why it separates.** A frame's timeline duration runs to its present, so on the emulator most of it is SurfaceFlinger queueing, which varies from capture to capture. Both plants add work to every frame on the app's UI thread, and UI time measures only that work.
- **Why this, not p50.** The frame p50 separates layout thrash well (3.2×) but not the allocation storm, which sits inside the clean range. One metric that detects both plants is a smaller library than two metrics that detect one each.
- **Why every doFrame of the UI thread.** Not only the doFrames matched to a window frame: counted over window frames only, the same p95 clears the clean runs by just 1.5× (G 1.8×, R 1.5×; clean spread 11.52 ms). A doFrame that drew nothing new still ran on the UI thread. The player pool's thread also runs a Choreographer, with 115–122 doFrames of under 3 ms per capture, so it is left out.
- **The three issue #8 metrics ship as specified.** An alert may well be on jank or p95, and on a real device the display pipeline is less noisy than on this emulator. What they detect here is recorded, not assumed:
  - `jank_frames_pct` detects layout thrash only just (1.45× the spread on the fixtures, and a 1.04× gap over all runs).
  - `jank_frames_pct` does not detect the allocation storm: its 11.8-point delta is smaller than the clean pair's own 12.5.
  - `frame_p95_ms` and `frame_p99_ms` detect neither plant.
  - The tap-sleep plant (S) moves no frame metric. It is `main_thread_blocked_ms`'s (#9).

## Consequences

- Roadmap item 5's "Expected metric":
  - allocation storm: becomes `frame_ui_time_p95_ms`, `gc_time_ms` (was `jank_frames_pct`, `gc_time_ms`);
  - layout thrash: becomes `frame_ui_time_p95_ms`, `jank_frames_pct` (was `frame_p95_ms`).
- The fixture tests treat "meaningful" as larger than the clean spread above.
  - Each plant's `frame_ui_time_p95_ms` delta must be more than twice the spread.
  - Layout thrash's `jank_frames_pct` delta must be more than the spread.
  - The clean pair's delta must be less than the spread on all four metrics.
  - What does not separate is asserted as such, so no later claim can rest on it.
- These numbers come from one emulator, one app and one hour. A second app (roadmap item 8) should re-measure the spreads, especially `jank_frames_pct`'s, before reusing them.
- `frame_ui_time_p95_ms` needs no `gfx` category, only `frametimeline` and `view` (atrace). Without `frametimeline` it reads NULL, because the app and UI thread are found from the window's timeline rows.
