# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The selected GC-time metric rose from 258.575876 ms in baseline to 10356.094546 ms in current, a 10097.51867 ms increase.

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

### c2. The increase is app-local: com.superplayer.demo had 7 collections totaling 258.575876 ms in baseline and 149 collections totaling 10356.094546 ms in current.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, count(*) AS gc_count, sum(gc_dur) / 1e6 AS total_gc_ms, max(gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, count(*) AS gc_count, sum(gc_dur) / 1e6 AS total_gc_ms, max(gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name
```

### c3. The app's traced draw work also expanded: Record View#draw() rose from 815.651371 ms to 7167.757708 ms, while AndroidOwner:draw rose from 249.954786 ms to 6800.699007 ms.

The `baseline` trace: 8 rows.

```sql
SELECT t.name AS thread_name,
  CASE WHEN s.name GLOB 'Choreographer#doFrame*' THEN 'Choreographer#doFrame*' ELSE s.name END AS slice_group,
  count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND (s.name GLOB 'Choreographer#doFrame*'
       OR s.name IN ('Background concurrent mark compact GC', 'Background young concurrent mark compact GC', 'Record View#draw()', 'AndroidOwner:draw', 'Compose:recompose', 'Compose:onForgotten'))
GROUP BY t.name, slice_group
ORDER BY total_ms DESC
```

The `current` trace: 8 rows.

```sql
SELECT t.name AS thread_name,
  CASE WHEN s.name GLOB 'Choreographer#doFrame*' THEN 'Choreographer#doFrame*' ELSE s.name END AS slice_group,
  count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND (s.name GLOB 'Choreographer#doFrame*'
       OR s.name IN ('Background concurrent mark compact GC', 'Background young concurrent mark compact GC', 'Record View#draw()', 'AndroidOwner:draw', 'Compose:recompose', 'Compose:onForgotten'))
GROUP BY t.name, slice_group
ORDER BY total_ms DESC
```

### c4. The relevant range change is 60be8b69bd6967b234ecb466b5cd1312df2c9854 in FeedScreen.kt: it adds a scroll-driven grain overlay that constructs List(GRAIN_SPECKS) inside drawWithContent, with GRAIN_SPECKS set to 1,000,000.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c5. The source lines for the grain loop and million-speck constant are attributed by blame to commit 60be8b69bd6967b234ecb466b5cd1312df2c9854, which correlates with the current trace's increased GC and draw work.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, count(*) AS gc_count, sum(gc_dur) / 1e6 AS total_gc_ms, max(gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name
```

## Caveats

- Only one capture per side is available, so small performance deltas could be run-to-run noise; this delta is unusually large and is accompanied by matching UI draw-work growth.
- The current metadata identifies an emulator benchmark build (sdk_gphone64_arm64, SDK 36, non-debuggable); baseline build metadata was not available.
- gc_time_ms is total ART collector wall time, not a direct measure of main-thread pause time. Attribution is marked correlated because the trace localizes the effect to app GC and draw work rather than exposing a source-level FeedScreen stack.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 47 tool calls, $0.0342, 216 s.
Tokens: 33 input, 212,535 cache read, 56,406 cache write, 13,234 output.
