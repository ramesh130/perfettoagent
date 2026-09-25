# No regression

- **Metric:** `frame_p95_ms` +0.5 ms (58.63 → 59.13 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 1 dropped; 12 of 13 citations passed
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

### c2. The measured app is com.example.jetnews in both traces, and its frame rows are for the MainActivity window on UI thread 365.

The `baseline` trace: 1 row.

```sql
SELECT upid, pid, name FROM process WHERE upid = 365
```

The `current` trace: 1 row.

```sql
SELECT upid, pid, name FROM process WHERE upid = 365
```

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, f.ui_thread_utid, f.layer_name, a.id, a.ts, a.dur, a.jank_type
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
ORDER BY a.dur DESC LIMIT 20
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, f.ui_thread_utid, f.layer_name, a.id, a.ts, a.dur, a.jank_type
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
ORDER BY a.dur DESC LIMIT 20
```

### c3. The UI-thread-only p95 also moved only slightly, from 26.206625 ms to 26.550666 ms, providing no stronger evidence of a code-level frame regression.

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

### c4. An auxiliary difference is higher app GC time: com.example.jetnews has two young collections totaling 32.61125 ms in the baseline, versus one young and one full collection totaling 50.839 ms in the current trace. This is not enough to attribute a frame regression to a commit from a single pair of captures.

The `baseline` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS total_gc_ms, max(gc_dur)/1e6 AS max_gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
GROUP BY process_name, gc_type
ORDER BY total_gc_ms DESC
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS gc_count, sum(gc_dur)/1e6 AS total_gc_ms, max(gc_dur)/1e6 AS max_gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
GROUP BY process_name, gc_type
ORDER BY total_gc_ms DESC
```

### c5. Commit 77a061c0c715ba071167b2104fcebb2c2be12c8d changes the InterestsScreen TopicItem thumbnail from 56 dp to 48 dp and adjusts its divider inset; the trace evidence does not directly identify that changed composable as the source of the small frame delta, so no culprit is assigned.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, f.ui_thread_utid, f.layer_name, a.id, a.ts, a.dur, a.jank_type
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
ORDER BY a.dur DESC LIMIT 20
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, f.ui_thread_utid, f.layer_name, a.id, a.ts, a.dur, a.jank_type
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
ORDER BY a.dur DESC LIMIT 20
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one baseline and one current capture are available, so percentile and GC differences are vulnerable to run-to-run noise.
- The current run metadata identifies a debuggable build on an sdk_gphone64_arm64 emulator; baseline build metadata was not available.

## Dropped claims

### c1. The selected frame_p95_ms metric increased from 58.626583 ms in the baseline to 59.127166 ms in the current trace, an approximately 0.5 ms change. With one capture per side, this small shift is insufficient to establish a meaningful regression.

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

`gpt-5.6-luna` on openai, effort xhigh: 72 tool calls, $0.0445, 204 s.
Tokens: 45 input, 391,831 cache read, 65,160 cache write, 16,934 output.
