# Regression

- **Metric:** `frame_ui_time_p95_ms` +2.65 ms (32.53 → 35.18 ms)
- **Culprit:** `7fd362610713` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 32.53 | 35.18 | +2.65 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c1. The selected app UI-frame p95 time increased from 32.532333 ms in the baseline to 35.181834 ms in the current trace, a delta of 2.649501 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

### c2. The trace localizes the change to com.superplayer.demo's UI thread: the current run has 327 app-deadline-missed frames versus 306 in the baseline, although it also contains fewer total frames.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
  ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT
  (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name,
  (SELECT t.name FROM thread t WHERE t.utid=(SELECT utid FROM ui)) AS ui_thread_name,
  (SELECT count(*) FROM frames) AS frame_count,
  (SELECT sum(jank_type GLOB '*App Deadline Missed*') FROM frames) AS app_deadline_missed,
  (SELECT count(*) FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_ms,
  (SELECT count(*) FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_ms
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
  ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT
  (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name,
  (SELECT t.name FROM thread t WHERE t.utid=(SELECT utid FROM ui)) AS ui_thread_name,
  (SELECT count(*) FROM frames) AS frame_count,
  (SELECT sum(jank_type GLOB '*App Deadline Missed*') FROM frames) AS app_deadline_missed,
  (SELECT count(*) FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_ms,
  (SELECT count(*) FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_ms
```

### c3. On that UI thread, Compose lazy-prefetch composition grew from 358.572502 ms across 68 slices to 397.255297 ms across 71 slices; binder work nested in frames also increased from 3.022458 ms to 20.467292 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
  ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT
  (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name,
  (SELECT t.name FROM thread t WHERE t.utid=(SELECT utid FROM ui)) AS ui_thread_name,
  (SELECT count(*) FROM frames) AS frame_count,
  (SELECT sum(jank_type GLOB '*App Deadline Missed*') FROM frames) AS app_deadline_missed,
  (SELECT count(*) FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_ms,
  (SELECT count(*) FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_ms
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
  ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT
  (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name,
  (SELECT t.name FROM thread t WHERE t.utid=(SELECT utid FROM ui)) AS ui_thread_name,
  (SELECT count(*) FROM frames) AS frame_count,
  (SELECT sum(jank_type GLOB '*App Deadline Missed*') FROM frames) AS app_deadline_missed,
  (SELECT count(*) FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_ms,
  (SELECT count(*) FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_ms
```

### c4. The correlated in-range candidate is 7fd3626107135436b97973da12915e1e13f76255, which changes the watched-row player-acquisition expression in FeedScreen; the trace evidence localizes the effect to the app UI workload but does not directly name that source method.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
  ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT
  (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name,
  (SELECT t.name FROM thread t WHERE t.utid=(SELECT utid FROM ui)) AS ui_thread_name,
  (SELECT count(*) FROM frames) AS frame_count,
  (SELECT sum(jank_type GLOB '*App Deadline Missed*') FROM frames) AS app_deadline_missed,
  (SELECT count(*) FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN thread_track tt ON tt.id=s.track_id
    WHERE tt.utid IN (SELECT utid FROM ui) AND s.name='compose:lazy:prefetch:compose') AS prefetch_compose_ms,
  (SELECT count(*) FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_count,
  (SELECT sum(s.dur)/1e6 FROM slice s JOIN android_frames_choreographer_do_frame d ON d.id=s.parent_id
    WHERE d.ui_thread_utid IN (SELECT utid FROM ui) AND s.name='binder transaction') AS frame_binder_ms
```

## Caveats

- Only one capture per side is available, so the p95 and jank differences may include run-to-run noise.
- The current capture is a non-debuggable benchmark on the sdk_gphone64_arm64 Android 36 emulator.
- No sampled app callstack directly linked the Compose/binder slices to FeedScreen; the commit attribution is therefore correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 76 tool calls, $0.0647, 296 s.
Tokens: 57 input, 735,958 cache read, 88,690 cache write, 23,147 output.
