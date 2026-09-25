# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 2 dropped; 9 of 12 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.21 | 54.17 | +27.96 |

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

### c1. The app UI-time p95 increased from 26.206625 ms in baseline to 54.169584 ms in current, a 27.962959 ms regression.

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

### c4. The app's GC activity increased from 2 young collections totaling 32.61125 ms to 430 young and 145 full collections totaling 5,854.487717 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, max(gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY gc_type ORDER BY gc_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, max(gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY gc_type ORDER BY gc_ms DESC
```

### c5. The likely culprit is bcd3ba1e926293a8681b6246ecdd271b5beb1592: it changes PostCards.kt to run a withFrameNanos loop and drawWithContent grain generation, including a 6,000-element random List during drawing; blame at the range head assigns these added lines to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, max(gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY gc_type ORDER BY gc_ms DESC
```

### c6. Both traces have zero stack-profile callsites and frames, so the source attribution is correlated rather than a direct symbolized-stack hit.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS callsites, (SELECT count(*) FROM __intrinsic_stack_profile_frame) AS frames FROM __intrinsic_stack_profile_callsite
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS callsites, (SELECT count(*) FROM __intrinsic_stack_profile_frame) AS frames FROM __intrinsic_stack_profile_callsite
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so ordinary run-to-run noise cannot be quantified.
- The attribution is based on a strong code/trace correlation; the traces do not contain sampled app callstacks for direct source-level confirmation.

## Dropped claims

### c2. The affected process is com.example.jetnews, and the frame-producing UI thread is example.jetnews in both captures.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.upid, p.pid, p.name AS process_name, t.utid, t.tid, t.name AS thread_name, count(*) AS frame_rows
FROM window_frames f
JOIN app ON app.upid = f.upid
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.pid, p.name, t.utid, t.tid, t.name
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
)
SELECT p.upid, p.pid, p.name AS process_name, t.utid, t.tid, t.name AS thread_name, count(*) AS frame_rows
FROM window_frames f
JOIN app ON app.upid = f.upid
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.pid, p.name, t.utid, t.tid, t.name
```

### c3. Normalized top-level Choreographer#doFrame work rose from 18,919.493771 ms across 2,286 slices in baseline to 65,201.813686 ms across 1,378 slices in current.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT CASE
  WHEN s.name LIKE 'Choreographer#doFrame%' THEN 'Choreographer#doFrame'
  ELSE s.name END AS slice_group,
  count(*) AS slices, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id = s.track_id
WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth = 0 AND s.dur > 0
GROUP BY slice_group ORDER BY total_ms DESC LIMIT 20
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT CASE
  WHEN s.name LIKE 'Choreographer#doFrame%' THEN 'Choreographer#doFrame'
  ELSE s.name END AS slice_group,
  count(*) AS slices, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id = s.track_id
WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth = 0 AND s.dur > 0
GROUP BY slice_group ORDER BY total_ms DESC LIMIT 20
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 50 tool calls, $0.0308, 179 s.
Tokens: 30 input, 212,162 cache read, 41,577 cache write, 13,468 output.
