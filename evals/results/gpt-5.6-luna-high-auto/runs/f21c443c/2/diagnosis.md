# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 1 dropped; 6 of 7 citations passed
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

### c2. The GC work is localized to com.superplayer.demo's HeapTaskDaemon: the baseline has 7 collections totaling 258.575876 ms, while the current trace has 149 collections totaling 10356.094546 ms.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, gc_type, count(*) AS gc_count,
       sum(gc_dur)/1e6 AS gc_ms,
       sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name='com.superplayer.demo'
GROUP BY process_name, thread_name, gc_type
ORDER BY gc_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, gc_type, count(*) AS gc_count,
       sum(gc_dur)/1e6 AS gc_ms,
       sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name='com.superplayer.demo'
GROUP BY process_name, thread_name, gc_type
ORDER BY gc_ms DESC
```

### c3. The current trace contains FeedScreenKt activity, including a FeedScreen coroutine JIT slice, linking the observed app work to the FeedScreen code changed in the range.

The `current` trace: 4 rows.

```sql
SELECT name, ts/1e9 AS ts_s, dur/1e6 AS dur_ms
FROM slice
WHERE name LIKE '%FeedScreenKt%' OR name LIKE '%DownloadsScreenKt%' OR name LIKE '%GRAIN%' OR name LIKE '%drawWithContent%'
ORDER BY ts
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c4. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 adds a per-frame scrolling grain effect in FeedScreen, allocating List(GRAIN_SPECKS) with GRAIN_SPECKS set to 1,000,000; blame at the range head assigns these lines to that commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

## Caveats

- Each side is a single capture, so smaller changes could be run-to-run noise; this GC increase is large relative to that limitation.
- The captures ran on an Android emulator (sdk_gphone64_arm64, API 36), and GC time measures collector duration rather than a direct allocation byte count.

## Dropped claims

### c1. App garbage-collection time increased from 258.575876 ms in the baseline to 10356.094546 ms in the current trace.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 28 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 28 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

## Run

`gpt-5.6-luna` on openai, effort high: 53 tool calls, $0.0279, 187 s.
Tokens: 33 input, 244,456 cache read, 47,545 cache write, 9,240 output.
