# Regression

- **Metric:** `gc_time_ms` +5,821.88 ms (32.61 → 5,854.49 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 3 claims kept, 1 dropped; 6 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 32.61 | 5,854.49 | +5,821.88 |

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

### c1. The app's aggregate garbage-collection time increased from 32.61125 ms in the baseline to 5854.487717 ms in the current trace.

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

### c2. The GC increase is in com.example.jetnews: the baseline has 2 collections totaling 32.61125 ms, while the current trace has 575 collections totaling 5854.487717 ms.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process, p.pid, e.upid, count(*) AS gc_count, sum(e.gc_dur) / 1e6 AS gc_ms, max(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
GROUP BY e.upid, p.name, p.pid
ORDER BY gc_ms DESC;
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process, p.pid, e.upid, count(*) AS gc_count, sum(e.gc_dur) / 1e6 AS gc_ms, max(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
GROUP BY e.upid, p.name, p.pid
ORDER BY gc_ms DESC;
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 added continuously refreshed grain rendering to PostCardSimple, including a 6,000-element random list inside drawWithContent; this is the strongest correlated explanation for the increased allocation and frame work.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side, so ordinary run-to-run variation cannot be independently estimated.
- The captures were made on an Android emulator using a debuggable build.
- The GC metric measures collector work and does not by itself identify every allocation site; the attribution is therefore correlated rather than direct.

## Dropped claims

### c3. UI work also worsened: the 95th-percentile doFrame time increased from 26.206625 ms to 54.169584 ms.

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort medium: 25 tool calls, $0.0156, 78 s.
Tokens: 15 input, 60,086 cache read, 37,806 cache write, 4,109 output.
