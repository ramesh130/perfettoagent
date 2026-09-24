# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The selected app's garbage-collection time increased from 258.575876 ms in the baseline to 10356.094546 ms in the current trace, a 10097.51867 ms increase.

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

### c2. The GC increase is localized to com.superplayer.demo: it went from 7 GC events totaling 258.575876 ms to 149 events totaling 10356.094546 ms.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT g.upid, p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms
FROM android_garbage_collection_events AS g
LEFT JOIN process AS p USING (upid)
GROUP BY g.upid, p.name
ORDER BY gc_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT g.upid, p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms
FROM android_garbage_collection_events AS g
LEFT JOIN process AS p USING (upid)
GROUP BY g.upid, p.name
ORDER BY gc_ms DESC
```

### c3. The app's HeapTaskDaemon also grew from 1481 traced slices totaling 960.583157 ms to 23300 slices totaling 38257.91202 ms, identifying the collector thread as the main trace-side locus of the change.

The `baseline` trace: 1 row.

```sql
SELECT t.utid, t.name AS thread_name, count(*) AS slice_count, sum(s.dur) / 1e6 AS slice_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo' AND t.name = 'HeapTaskDaemon' AND s.dur > 0
GROUP BY t.utid, t.name
```

The `current` trace: 1 row.

```sql
SELECT t.utid, t.name AS thread_name, count(*) AS slice_count, sum(s.dur) / 1e6 AS slice_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo' AND t.name = 'HeapTaskDaemon' AND s.dur > 0
GROUP BY t.utid, t.name
```

### c4. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 adds a scrolling drawWithContent path that constructs List(GRAIN_SPECKS) and sets GRAIN_SPECKS to 1000000; together with the sharp increase in app GC activity, this is the likely cause.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT g.upid, p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms
FROM android_garbage_collection_events AS g
LEFT JOIN process AS p USING (upid)
GROUP BY g.upid, p.name
ORDER BY gc_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT g.upid, p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms
FROM android_garbage_collection_events AS g
LEFT JOIN process AS p USING (upid)
GROUP BY g.upid, p.name
ORDER BY gc_ms DESC
```

## Caveats

- Only one capture is available for each build, so run-to-run variability cannot be completely excluded.
- gc_time_ms measures total collector work, not directly the application's paused time.
- The source attribution is correlated rather than direct because the trace localizes the increase to the app's collector activity, while the matching source change is identified from the git range.

## Run

`gpt-5.6-luna` on openai, effort high: 34 tool calls, $0.0160, 163 s.
Tokens: 24 input, 74,204 cache read, 18,274 cache write, 8,308 output.
