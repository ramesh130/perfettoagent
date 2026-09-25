# Inconclusive

- **Metric:** `frame_p95_ms` +0.5 ms (58.63 → 59.13 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 1 dropped; 12 of 13 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 58.63 | 59.13 | +0.5 |

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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c2. The frame-bearing process is com.example.jetnews, and its UI thread is example.jetnews (utid 365); the traces contain 2,120 baseline frames and 2,107 current frames.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, f.ui_thread_utid, p.name AS process_name, t.name AS ui_thread_name, count(*) AS frame_count
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid,f.ui_thread_utid,p.name,t.name
ORDER BY frame_count DESC LIMIT 10
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, f.ui_thread_utid, p.name AS process_name, t.name AS ui_thread_name, count(*) AS frame_count
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid,f.ui_thread_utid,p.name,t.name
ORDER BY frame_count DESC LIMIT 10
```

### c3. The localized UI work is generic Compose lazy-list prefetch on the app UI thread. Its compose-prefetch totals were 312.383833 ms in baseline and 299.495334 ms in current, so the trace does not show a corresponding increase in this work.

The `baseline` trace: 4 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name AS slice_name,
       count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND s.depth = 0 AND s.dur > 0
  AND s.name GLOB 'compose:lazy:prefetch*'
GROUP BY p.name,t.name,s.name
ORDER BY total_ms DESC
```

The `current` trace: 4 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name AS slice_name,
       count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND s.depth = 0 AND s.dur > 0
  AND s.name GLOB 'compose:lazy:prefetch*'
GROUP BY p.name,t.name,s.name
ORDER BY total_ms DESC
```

### c4. The app-only UI-time p95 changed by only 0.344041 ms, from 26.206625 ms to 26.550666 ms.

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

### c5. Garbage collection differs more noticeably: the app's HeapTaskDaemon spent 32.61125 ms across two young collections in baseline versus 50.839 ms across a young and a full collection in current.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, gc_type, gc_ts, gc_dur / 1e6 AS gc_ms, reclaimed_mb, gc_running_dur / 1e6 AS running_ms, gc_runnable_dur / 1e6 AS runnable_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
ORDER BY gc_ts
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, gc_type, gc_ts, gc_dur / 1e6 AS gc_ms, reclaimed_mb, gc_running_dur / 1e6 AS running_ms, gc_runnable_dur / 1e6 AS runnable_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
ORDER BY gc_ts
```

### c6. Commit 77a061c0c715ba071167b2104fcebb2c2be12c8d changes the app's InterestsScreen.kt UI to use smaller thumbnails. The trace only localizes the activity to generic Compose slices and HeapTaskDaemon collections, so it does not provide a direct source-level attribution to this commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

The `baseline` trace: 4 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name AS slice_name,
       count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND s.depth = 0 AND s.dur > 0
  AND s.name GLOB 'compose:lazy:prefetch*'
GROUP BY p.name,t.name,s.name
ORDER BY total_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, gc_type, gc_ts, gc_dur / 1e6 AS gc_ms, reclaimed_mb, gc_running_dur / 1e6 AS running_ms, gc_runnable_dur / 1e6 AS runnable_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
ORDER BY gc_ts
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so there is no run-to-run variance estimate; the 0.500583 ms p95 movement may be capture noise.
- The current run is a debuggable debug build on an emulator, where scheduler, JIT, rendering, and GC timing can vary.
- No source-level stack attribution connects the generic Compose or GC rows to a changed line in the range.

## Dropped claims

### c1. The selected end-to-end frame p95 increased from 58.626583 ms to 59.127166 ms, a delta of 0.500583 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 63 tool calls, $0.0437, 254 s.
Tokens: 45 input, 284,867 cache read, 49,362 cache write, 21,364 output.
