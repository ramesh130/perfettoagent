# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. App garbage-collection time increased from 258.575876 ms in the baseline to 10356.094546 ms in the current trace, a delta of 10097.51867 ms.

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

### c2. The regression is concentrated in com.superplayer.demo: it had 7 GC events totaling 258.575876 ms in the baseline and 149 events totaling 10356.094546 ms in the current trace.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, g.upid, COUNT(*) AS gc_count, SUM(g.gc_dur) / 1e6 AS gc_ms, MAX(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
GROUP BY g.upid, p.name
ORDER BY gc_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, g.upid, COUNT(*) AS gc_count, SUM(g.gc_dur) / 1e6 AS gc_ms, MAX(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
GROUP BY g.upid, p.name
ORDER BY gc_ms DESC
```

### c3. The current trace also shows com.superplayer.demo spending 6800.699007 ms in AndroidOwner:draw and 10356.094546 ms in the two background GC categories, versus 249.954786 ms and 258.575876 ms respectively in the baseline.

The `baseline` trace: 4 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name, COUNT(*) AS slice_count, SUM(s.dur) / 1e6 AS total_ms, MAX(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.name IN ('AndroidOwner:draw', 'Record View#draw()', 'Background concurrent mark compact GC', 'Background young concurrent mark compact GC')
GROUP BY p.name, t.name, s.name
ORDER BY total_ms DESC
```

The `current` trace: 4 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name, COUNT(*) AS slice_count, SUM(s.dur) / 1e6 AS total_ms, MAX(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.name IN ('AndroidOwner:draw', 'Record View#draw()', 'Background concurrent mark compact GC', 'Background young concurrent mark compact GC')
GROUP BY p.name, t.name, s.name
ORDER BY total_ms DESC
```

### c4. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 adds a scrolling feed grain overlay in FeedScreen.kt that allocates a List using GRAIN_SPECKS set to 1,000,000 during drawWithContent; this is the strongest correlation with the new UI-draw and GC activity.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

## Caveats

- Each side is a single capture, so ordinary run-to-run variation cannot be ruled out; the size and concentration of this change make noise an unlikely explanation.
- The captures are benchmark runs on an Android emulator, and no allocation-profiler data was available to directly connect individual allocations to the FeedScreen method.

## Run

`gpt-5.6-luna` on openai, effort high: 52 tool calls, $0.0297, 184 s.
Tokens: 33 input, 285,021 cache read, 52,819 cache write, 8,984 output.
