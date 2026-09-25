# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 1 dropped; 8 of 9 citations passed
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

### c2. The increase is isolated to com.superplayer.demo: it went from 7 collections totaling 258.575876 ms to 149 collections totaling 10356.094546 ms; the current run reclaimed 5422.02 MB.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur) / 1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name, gc_type ORDER BY gc_count DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur) / 1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name, gc_type ORDER BY gc_count DESC
```

### c3. The affected trace area is the app's UI drawing path: current AndroidOwner:draw totaled 6800.699007 ms across 427 slices and Record View#draw() totaled 7167.757708 ms, versus 249.954786 ms across 676 slices and 815.651371 ms across 701 slices in the baseline.

The `baseline` trace: 4 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.name IN ('drainAndFeed', 'draw-VRI[MainActivity]', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY s.name ORDER BY total_ms DESC
```

The `current` trace: 4 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.name IN ('drainAndFeed', 'draw-VRI[MainActivity]', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY s.name ORDER BY total_ms DESC
```

### c4. 60be8b69bd6967b234ecb466b5cd1312df2c9854 is the likely culprit: it changed FeedScreen.kt to add a scrolling grain overlay that allocates List(GRAIN_SPECKS) inside the drawing callback. That allocation pattern matches the current trace's large increase in app GC and UI-draw work.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur) / 1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name, gc_type ORDER BY gc_count DESC
```

The `current` trace: 4 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.name IN ('drainAndFeed', 'draw-VRI[MainActivity]', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY s.name ORDER BY total_ms DESC
```

## Caveats

- Only one capture was available per side, so smaller frame-level differences may contain run-to-run noise; this GC increase is large relative to that risk.
- The current capture is from a non-debuggable benchmark build on the sdk_gphone64_arm64 emulator.
- GC time measures collector work, not direct main-thread pause time; the source attribution is correlated because the trace exposes framework draw/GC slices rather than an app source stack for the allocation.

## Dropped claims

### c1. App garbage-collection time increased from 258.575876 ms in the baseline to 10356.094546 ms in the current trace, a 10097.51867 ms increase.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
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

## Run

`gpt-5.6-luna` on openai, effort xhigh: 63 tool calls, $0.0354, 276 s.
Tokens: 51 input, 339,476 cache read, 41,121 cache write, 15,295 output.
