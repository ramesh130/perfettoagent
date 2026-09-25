# No regression

- **Metric:** `gc_time_ms` +18.23 ms (32.61 → 50.84 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 1 dropped; 9 of 10 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 32.61 | 50.84 | +18.23 |

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

### c2. The extra GC time is localized to com.example.jetnews. The baseline has two young collections lasting 12.322333 ms and 20.288917 ms; the current trace has a 31.45225 ms young collection and a 19.38675 ms full collection. Reclaimed memory is similar across the two captures.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT gc_type, gc_dur/1e6 AS gc_ms, reclaimed_mb, min_heap_mb, max_heap_mb, gc_ts/1e9 AS ts_s
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
ORDER BY gc_ts
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT gc_type, gc_dur/1e6 AS gc_ms, reclaimed_mb, min_heap_mb, max_heap_mb, gc_ts/1e9 AS ts_s
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
ORDER BY gc_ts
```

### c3. The main-thread slice workload does not show a broad slowdown: the top-level traversal slices total 15637.029552 ms across 2198 slices in the baseline and 14908.30484 ms across 2187 slices in the current trace.

The `baseline` trace: 10 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id=s.track_id
WHERE tt.utid=365 AND s.dur > 0
GROUP BY s.name
ORDER BY total_ms DESC
LIMIT 10
```

The `current` trace: 10 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id=s.track_id
WHERE tt.utid=365 AND s.dur > 0
GROUP BY s.name
ORDER BY total_ms DESC
LIMIT 10
```

### c4. The range contains a UI-size change that reduces Interests row thumbnails from 56 dp to 48 dp and changes the corresponding padding, but the trace evidence does not localize the GC increase to that code.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT gc_type, gc_dur/1e6 AS gc_ms, reclaimed_mb, min_heap_mb, max_heap_mb, gc_ts/1e9 AS ts_s
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
ORDER BY gc_ts
```

### c5. The other runtime-affecting range change adjusts the home-screen widget update period from one hour to 30 minutes; it is a resource change and is not connected by the traces to the app's HeapTaskDaemon collections.

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
GROUP BY process_name
ORDER BY gc_ms DESC
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- There is only one capture per side, so GC scheduling and collection type are noisy; the extra full collection is insufficient to attribute a regression to a commit.
- The current trace metadata identifies a debuggable build running on an Android emulator; baseline build metadata was not recorded.

## Dropped claims

### c1. The selected metric increased from 32.61125 ms in the baseline to 50.839 ms in the current trace, a delta of 18.22775 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 28 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 28 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT upid FROM window_frames GROUP BY count(*) ORDER BY count(*) DESC, upid LIMIT 1
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

## Run

`gpt-5.6-luna` on openai, effort high: 42 tool calls, $0.0167, 111 s.
Tokens: 27 input, 100,605 cache read, 20,489 cache write, 7,992 output.
