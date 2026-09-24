# Regression

- **Metric:** `gc_time_ms` +13,373.93 ms (258.58 → 13,632.5 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 1 dropped; 8 of 9 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 258.58 | 13,632.5 | +13,373.93 |

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

### c2. The app frame spans were similar—55.083096984 seconds in the baseline and 57.414479277 seconds in the current trace—so the much larger GC total is not explained by a substantially longer capture.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT upid, count(*) AS frame_count, min(ts) / 1e9 AS first_frame_s,
       max(ts + dur) / 1e9 AS last_frame_s,
       (max(ts + dur) - min(ts)) / 1e9 AS frame_span_s
FROM window_frames
WHERE upid = (SELECT upid FROM app)
GROUP BY upid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT upid, count(*) AS frame_count, min(ts) / 1e9 AS first_frame_s,
       max(ts + dur) / 1e9 AS last_frame_s,
       (max(ts + dur) - min(ts)) / 1e9 AS frame_span_s
FROM window_frames
WHERE upid = (SELECT upid FROM app)
GROUP BY upid
```

### c3. The current GC is concentrated in com.superplayer.demo's HeapTaskDaemon, while the app's UI thread also shows substantially more Compose lazy-prefetch idle work: 34 slices totaling 1114.795252 ms versus 10 slices totaling 67.200875 ms in the baseline.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS gc_count,
       sum(e.gc_dur) / 1e6 AS gc_ms,
       min(e.gc_dur) / 1e6 AS min_gc_ms,
       max(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
LEFT JOIN thread AS t USING (utid)
WHERE e.upid = (SELECT upid FROM app)
GROUP BY p.name, t.name
ORDER BY gc_ms DESC
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms,
       max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE s.depth = 0 AND tt.utid IN (SELECT utid FROM main_thread)
  AND s.name = 'compose:lazy:prefetch:idle_frame' AND s.dur > 0
GROUP BY s.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms,
       max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE s.depth = 0 AND tt.utid IN (SELECT utid FROM main_thread)
  AND s.name = 'compose:lazy:prefetch:idle_frame' AND s.dur > 0
GROUP BY s.name
```

### c4. The likely culprit is commit 18fab3f92d84e00498a5a6891125dd23bd063820: it adds an infinite per-row Compose breathing animation and a RowTitle implementation that repeatedly measures text while composing FeedScreen.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms,
       max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE s.depth = 0 AND tt.utid IN (SELECT utid FROM main_thread)
  AND s.name = 'compose:lazy:prefetch:idle_frame' AND s.dur > 0
GROUP BY s.name
```

## Caveats

- Only one capture is available for each side, so small performance changes could be run-to-run noise; this change is large enough to stand out but the attribution remains correlated rather than a direct sampled-code attribution.
- The GC metric is whole-trace GC wall time, and the captures were made on an emulator.

## Dropped claims

### c1. App GC time increased from 258.575876 ms across 7 collections in the baseline to 13632.500926 ms across 203 collections in the current trace.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 18 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 18 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY count(*) ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT count(*) AS gc_count, sum(gc_dur) / 1e6 AS gc_ms,
       min(gc_ts) / 1e9 AS first_gc_s, max(gc_ts + gc_dur) / 1e9 AS last_gc_s,
       (max(gc_ts + gc_dur) - min(gc_ts)) / 1e9 AS gc_span_s
FROM android_garbage_collection_events
WHERE upid = (SELECT upid FROM app)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT count(*) AS gc_count, sum(gc_dur) / 1e6 AS gc_ms,
       min(gc_ts) / 1e9 AS first_gc_s, max(gc_ts + gc_dur) / 1e9 AS last_gc_s,
       (max(gc_ts + gc_dur) - min(gc_ts)) / 1e9 AS gc_span_s
FROM android_garbage_collection_events
WHERE upid = (SELECT upid FROM app)
```

## Run

`gpt-5.6-luna` on openai, effort high: 53 tool calls, $0.0291, 340 s.
Tokens: 39 input, 241,278 cache read, 30,547 cache write, 13,873 output.
