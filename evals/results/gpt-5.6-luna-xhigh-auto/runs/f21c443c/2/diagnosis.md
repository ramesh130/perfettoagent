# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 6 claims kept, 0 dropped; 14 of 14 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 258.58 | 10,356.09 | +10,097.52 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_garbage_collection_events) THEN NULL
    ELSE coalesce((
      SELECT sum(gc_dur) FROM android_garbage_collection_events
      WHERE upid = (SELECT upid FROM app)
    ), 0) / 1e6
  END AS value
```

## Claims

### c1. App GC time increased from 258.575876 ms in the baseline to 10356.094546 ms in the current trace, a delta of 10097.51867 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_garbage_collection_events) THEN NULL
    ELSE coalesce((
      SELECT sum(gc_dur) FROM android_garbage_collection_events
      WHERE upid = (SELECT upid FROM app)
    ), 0) / 1e6
  END AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_garbage_collection_events) THEN NULL
    ELSE coalesce((
      SELECT sum(gc_dur) FROM android_garbage_collection_events
      WHERE upid = (SELECT upid FROM app)
    ), 0) / 1e6
  END AS value
```

### c2. The increase is concentrated in com.superplayer.demo: the app had 7 GC events in the baseline and 149 in the current trace. The captures were approximately the same length, while the current trace actually had fewer window frames.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.upid, p.name AS process_name, count(*) AS gc_events,
       sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
WHERE g.upid = (SELECT upid FROM app)
GROUP BY p.upid, p.name
ORDER BY gc_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.upid, p.name AS process_name, count(*) AS gc_events,
       sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
WHERE g.upid = (SELECT upid FROM app)
GROUP BY p.upid, p.name
ORDER BY gc_ms DESC
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid, count(*) AS frames FROM window_frames GROUP BY upid ORDER BY frames DESC, upid LIMIT 1)
SELECT (SELECT frames FROM app) AS window_frame_count,
       (SELECT (max(ts+dur)-min(ts))/1e9 FROM sched) AS sched_span_s,
       (SELECT upid FROM app) AS upid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid, count(*) AS frames FROM window_frames GROUP BY upid ORDER BY frames DESC, upid LIMIT 1)
SELECT (SELECT frames FROM app) AS window_frame_count,
       (SELECT (max(ts+dur)-min(ts))/1e9 FROM sched) AS sched_span_s,
       (SELECT upid FROM app) AS upid
```

### c3. The user-visible frame outcome also worsened: App Deadline Missed jank rose from 54.7337278106509% to 66.5105386416862%.

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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
```

### c4. The current trace contains one JIT-compilation slice for the FeedScreen coroutine FeedScreenKt$FeedScreen$3$1$2.invokeSuspend; the baseline contains none.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS slices, min(name) AS example_name, sum(dur)/1e6 AS total_ms
FROM slice
WHERE name LIKE 'JIT compiling %com.superplayer.demo.FeedScreenKt$FeedScreen$3$1$2.invokeSuspend%'
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS slices, min(name) AS example_name, sum(dur)/1e6 AS total_ms
FROM slice
WHERE name LIKE 'JIT compiling %com.superplayer.demo.FeedScreenKt$FeedScreen$3$1$2.invokeSuspend%'
```

### c5. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 introduced the scroll-driven FeedScreen grain path, including the per-frame coroutine and the one-million-element random grain list; blame at the range head assigns those lines to this commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c6. The current-only FeedScreen trace row points into the file changed by commit 60be8b69bd6967b234ecb466b5cd1312df2c9854, while the large increase in app GC activity and jank occurs in the same capture; this directly attributes the regression to that commit.

The `current` trace: 1 row.

```sql
SELECT count(*) AS slices, min(name) AS example_name, sum(dur)/1e6 AS total_ms
FROM slice
WHERE name LIKE 'JIT compiling %com.superplayer.demo.FeedScreenKt$FeedScreen$3$1$2.invokeSuspend%'
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_garbage_collection_events) THEN NULL
    ELSE coalesce((
      SELECT sum(gc_dur) FROM android_garbage_collection_events
      WHERE upid = (SELECT upid FROM app)
    ), 0) / 1e6
  END AS value
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

## Caveats

- Only one capture per side is available, so smaller changes could be noisy; this regression is large but should still be confirmed with repetitions.
- The current run metadata identifies a non-debuggable benchmark build on the sdk_gphone64_arm64 Android emulator (SDK 36).
- No allocation/heapprofd profile was available; gc_time_ms measures total garbage-collector work, not directly the application pause time.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 59 tool calls, $0.0456, 275 s.
Tokens: 48 input, 380,623 cache read, 69,997 cache write, 17,093 output.
