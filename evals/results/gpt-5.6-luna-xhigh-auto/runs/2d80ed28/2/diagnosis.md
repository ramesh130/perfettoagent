# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 6 claims kept, 0 dropped; 13 of 13 citations passed
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

### c1. The selected UI-frame metric regressed from 26.206625 ms to 54.169584 ms at p95, a 27.962959 ms increase.

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

### c2. The slowdown is localized to com.example.jetnews's UI rendering: the current trace has 1,376 UI frames and all exceed 16.67 ms, while the baseline has 2,120 frames, of which 1,327 exceed that threshold.

The `current` trace: 1 row.

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
SELECT p.name AS process_name, t.name AS ui_thread_name, count(*) AS frame_count,
       sum(fr.dur)/1e6 AS frame_ms, sum(fr.dur > 16666667) AS frames_over_16_67ms
FROM window_frames AS fr
JOIN app ON app.upid = fr.upid
JOIN process AS p ON p.upid = fr.upid
JOIN thread AS t ON t.utid = fr.ui_thread_utid
GROUP BY p.name, t.name
```

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
SELECT p.name AS process_name, t.name AS ui_thread_name, count(*) AS frame_count,
       sum(fr.dur)/1e6 AS frame_ms, sum(fr.dur > 16666667) AS frames_over_16_67ms
FROM window_frames AS fr
JOIN app ON app.upid = fr.upid
JOIN process AS p ON p.upid = fr.upid
JOIN thread AS t ON t.utid = fr.ui_thread_utid
GROUP BY p.name, t.name
```

### c3. The app's garbage-collection load rose from 2 young collections totaling 32.61125 ms in the baseline to 575 collections totaling 5854.487717 ms in the current trace: 430 young and 145 full collections.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, avg(max_heap_mb) AS avg_max_heap_mb
FROM android_garbage_collection_events
WHERE upid = 365
GROUP BY process_name, gc_type
ORDER BY gc_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, avg(max_heap_mb) AS avg_max_heap_mb
FROM android_garbage_collection_events
WHERE upid = 1
GROUP BY process_name, gc_type
ORDER BY gc_ms DESC
```

### c4. The current trace also shows 1,378 AndroidOwner:draw slices totaling 63894.081421 ms, compared with 2,060 such slices totaling 180.432279 ms in the baseline.

The `current` trace: 7 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE t.upid = 1
  AND (s.name IN ('AndroidOwner:draw', 'traversal') OR s.name GLOB '*GC*')
  AND s.dur > 0
GROUP BY s.name
ORDER BY total_ms DESC
```

The `baseline` trace: 3 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE t.upid = 365
  AND (s.name IN ('AndroidOwner:draw', 'traversal') OR s.name GLOB '*GC*')
  AND s.dur > 0
GROUP BY s.name
ORDER BY total_ms DESC
```

### c5. bcd3ba1e926293a8681b6246ecdd271b5beb1592 is the likely culprit: blame at the range head assigns the new card-rendering code to this commit, which adds a frame-driven loop and allocates a fresh List(GRAIN_SPECKS) of 6,000 random values inside drawWithContent. That allocation pattern matches the new repeated GC and draw activity.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, avg(max_heap_mb) AS avg_max_heap_mb
FROM android_garbage_collection_events
WHERE upid = 1
GROUP BY process_name, gc_type
ORDER BY gc_ms DESC
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, avg(max_heap_mb) AS avg_max_heap_mb
FROM android_garbage_collection_events
WHERE upid = 365
GROUP BY process_name, gc_type
ORDER BY gc_ms DESC
```

### c6. Neither trace contains stack-profile frames, so the source-level attribution cannot be direct from a sampled callstack.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS frame_rows FROM stack_profile_frame
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS frame_rows FROM stack_profile_frame
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so run-to-run noise cannot be ruled out; the observed UI and GC changes are nevertheless large.
- The captures are emulator/debug-build measurements, so absolute timings may not represent release hardware.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 58 tool calls, $0.0316, 190 s.
Tokens: 39 input, 240,519 cache read, 32,525 cache write, 15,547 output.
