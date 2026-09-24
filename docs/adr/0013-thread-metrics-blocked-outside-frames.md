# Thread metrics: blocked means blocked outside a frame, and one more jank fixture

Issue #9 adds `main_thread_blocked_ms`, `gc_time_ms` and `binder_wait_ms` to the metric library. The issue names each metric's source but leaves open which app, which thread and which time each one counts. This records those choices, the measurements behind them, and the fixture the sleep plant needs. `native_unfreed_bytes` has no data on any capture; that is ADR-0014. Affects `src/perfettoagent/metrics/`, `tests/fixtures/large/` and `tests/conftest.py`.

## The app is the frame metrics' app

All three use the frame metrics' own query to find the app (ADR-0011): the process with the most window frames. They take its main thread from the same query, as the thread that draws those frames. The query is copied verbatim down to the `frames` CTE, and a test checks that the copies match. One choice of app across the library means a diagnosis can't compare two numbers taken from two different processes. The cost is that without the `frametimeline` data source these three read NULL, as the frame metrics already do.

## `main_thread_blocked_ms`: blocked inside work, outside `Choreographer#doFrame`

Blocked means any `thread_state` other than Running or runnable (`R`, `R+`). Mostly that is `S` (sleep, a lock, a binder reply) and `D` (usually I/O). Runnable time is left out, because it means the CPU was busy, not that the thread was waiting. Only blocked time inside the main thread's top-level slices counts. An idle main thread sleeps in its Looper, and that is most of any trace: 41.7 s of the 49.5 s the main thread slept on the clean baseline fixture.

The hard part is `Choreographer#doFrame`. Measured on all 15 jank captures (superPlayer PR #392, with the pinned trace processor 58.2):

| Run | Blocked in any top-level slice | of which inside doFrame | Outside doFrame (**the metric**) |
|---|---:|---:|---:|
| B1 (clean) | 7780.2 | 7754.9 | **25.3** |
| C1 (clean) | 7845.8 | 7836.6 | **9.3** |
| B2 (clean) | 9110.2 | 9091.0 | **19.2** |
| C2 (clean) | 9901.2 | 9873.0 | **28.2** |
| B3 (clean) | 7698.2 | 7685.2 | **13.0** |
| C3 (clean) | 8594.8 | 8555.9 | **38.9** |
| S1 (sleep) | 8049.5 | 7317.9 | **731.5** |
| S2 (sleep) | 7634.1 | 6900.3 | **733.9** |
| S3 (sleep) | 8431.6 | 7683.4 | **748.2** |
| G1 (storm) | 2495.8 | 2449.4 | **46.4** |
| G2 (storm) | 2639.8 | 2544.6 | **95.3** |
| G3 (storm) | 1949.7 | 1865.2 | **84.6** |
| R1 (thrash) | 14923.3 | 14849.5 | **73.8** |
| R2 (thrash) | 18115.5 | 18034.4 | **81.0** |
| R3 (thrash) | 18154.2 | 18094.5 | **59.7** |

All values are in ms. The last two columns are the same query with the doFrame filter inverted, and they add up to the first.

- **Inside doFrame, the clean runs block for 7.7–9.9 s,** most of it in `postAndWait` (handing the frame to the RenderThread) and in `Compose:onForgotten` as rows leave the composition while the feed scrolls. That noise has a 2.2 s spread, three times the 725 ms the sleep plant adds, so it hides the plant. superPlayer's own pilots found the same thing (its `plants/README.md`).
- **Outside doFrame, the clean spread is 29.7 ms** (9.3–38.9). The sleep runs sit at 731.5–748.2 ms: the gap from the largest clean run to the smallest sleep run is 692.6 ms, 23× the spread. All of it is six sleeps of about 120 ms inside the taps' `deliverInputEvent` slices. Android batches only move events into the next frame, so a tap's click handler runs outside doFrame.
- **What it leaves to other metrics.** Blocking inside a frame is part of that frame's duration, which `frame_ui_time_p95_ms` measures at the 95th percentile, and `binder_wait_ms` counts the main thread's binder waits wherever they happen.
- **What else it moves.** The storm and thrash runs read 46–95 ms. Against the baseline fixture, current_c (R1) is +48.6 ms, 1.6× the clean spread, and current_b (G1) is +21.1 ms. Both are more than ten times smaller than the sleep plant's +706.2 ms. The tests assert that ratio. They do not assert that the other plants leave this metric flat.
- **Limits.** It can't tell a sleep from a lock or a binder reply: all of them are `S`. Blocking in untraced code looks like an idle Looper, so it is missed.

## `gc_time_ms`: the app's collections, from the stdlib

`gc_time_ms` sums `gc_dur` over `android_garbage_collection_events` for the app's process. Those are ART's top-level `*concurrent*GC` slices, plus their `CompactionPhase` when it runs outside them.

- **Only the app's process.** On the clean baseline fixture, 17 of the trace's 24 collections belong to other processes.
- **Not the `GC: Wait For Completion …` slices.** Those are other threads waiting for these same collections, so the time would be counted twice. A main-thread wait outside a frame is already in `main_thread_blocked_ms`.
- **Measured:** 6–8 collections taking 172.0–428.5 ms on the clean runs, a spread of 256.5 ms. The storm runs had 134–149 collections taking 9484.5–11044.5 ms, a gap 35× the spread. The thrash runs are high too (11801.6–13632.5 ms), because re-measuring text allocates. The sleep runs are inside the clean range. On the fixtures, the numbers match superPlayer devicelab's `gc.sql` to within 1 ms.

## `binder_wait_ms`: the main thread's synchronous calls

`binder_wait_ms` sums `client_dur` over `android_binder_txns` for synchronous calls from the main thread. On the fixtures that equals the sum of the main thread's `binder transaction` slices exactly.

- **Main thread only.** The app's other threads wait 9–20 s per capture, against 0.1–1.1 s on the main thread, and none of it is on the thread that handles input and draws.
- **Synchronous only.** A oneway call does not wait.
- **Measured:** 214.3–348.3 ms on the clean runs, a spread of 134.0 ms. No plant targets it. The thrash runs read 888.5–1080.0 ms. That is recorded here, not asserted in a test, because nothing yet explains it.

## NULL when the data source was off

Each metric reads NULL, never 0, when its data source was off:

- all three, when there is no window frame;
- `main_thread_blocked_ms`, when the main thread has no `thread_state` (sched);
- `gc_time_ms`, when no process collected (the `dalvik` category was off);
- `binder_wait_ms`, when no process made a binder call (`binder_driver` was off).

A trace that has the data source but no matching event in the app reads 0. ADR-0014 covers how a NULL reaches the model.

## The sleep capture joins the fixtures, and LFS now holds about 210 MB

The sleep plant needs its capture. S1 is committed as `jank-d-current.perfetto-trace.gz`: 31.0 MB raw, 11.8 MB after `gzip -9 -n` (ADR-0010, ADR-0012). The name says only that it is a third changed capture. `conftest.jank_traces` now returns it as `current_d`. The heap dumps were not re-compressed. That would save about 37 MB per fetch but add about 10 MB of storage, and it would change #3's fixtures in a change about other metrics. It remains the next step if bandwidth runs short (ADR-0012).

## Consequences

- **The LFS total is 209.8 MB** (209,750,882 bytes over ten files): 46.7 MB of heap dumps, 82.5 MB of startup traces and 80.5 MB of jank traces. The 1 GB monthly bandwidth quota now allows about 4 full fetches. CI is still manual-only. The storage quota is 21% used.
- The tests treat a change as meaningful when it is larger than the clean spread above. Each plant's delta must be more than twice its metric's spread. The clean pair must stay under the spread, and under a tenth of the plant's delta.
- These spreads come from one emulator, one app and one hour. A second app (roadmap item 8) should measure them again.
