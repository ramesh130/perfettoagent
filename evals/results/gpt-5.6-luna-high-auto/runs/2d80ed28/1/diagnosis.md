# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. The app UI-thread p95 time increased from 26.206625 ms in the baseline to 54.169584 ms in the current trace, a 27.962959 ms regression.

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

### c2. The affected workload is com.example.jetnews: its UI thread is example.jetnews, and the current trace has substantially more frame work than the baseline.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, COUNT(*) AS frame_count, SUM(a.dur) / 1e6 AS frame_ms FROM actual_frame_timeline_slice AS a JOIN android_frames_layers AS f ON f.actual_frame_timeline_id = a.id JOIN process AS p ON p.upid = f.upid JOIN thread AS t ON t.utid = f.ui_thread_utid WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0 GROUP BY p.name, t.name ORDER BY frame_count DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, COUNT(*) AS frame_count, SUM(a.dur) / 1e6 AS frame_ms FROM actual_frame_timeline_slice AS a JOIN android_frames_layers AS f ON f.actual_frame_timeline_id = a.id JOIN process AS p ON p.upid = f.upid JOIN thread AS t ON t.utid = f.ui_thread_utid WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0 GROUP BY p.name, t.name ORDER BY frame_count DESC
```

### c3. Garbage collection is the strongest trace-localized change: com.example.jetnews HeapTaskDaemon GC rose from 2 collections totaling 32.61125 ms to 575 collections totaling 5854.487717 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, COUNT(*) AS gc_count, SUM(gc_dur)/1e6 AS gc_ms, MAX(gc_dur)/1e6 AS max_gc_ms FROM android_garbage_collection_events WHERE process_name = 'com.example.jetnews' GROUP BY process_name, thread_name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, COUNT(*) AS gc_count, SUM(gc_dur)/1e6 AS gc_ms, MAX(gc_dur)/1e6 AS max_gc_ms FROM android_garbage_collection_events WHERE process_name = 'com.example.jetnews' GROUP BY process_name, thread_name
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 adds a continuously running per-card frame effect and constructs a 6,000-element random List inside drawWithContent.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

### c5. The per-frame allocation introduced by bcd3ba1e926293a8681b6246ecdd271b5beb1592 is likely responsible for the regression: it matches the current trace's large increase in HeapTaskDaemon GC activity and the elevated UI-frame p95.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, thread_name, COUNT(*) AS gc_count, SUM(gc_dur)/1e6 AS gc_ms, MAX(gc_dur)/1e6 AS max_gc_ms FROM android_garbage_collection_events WHERE process_name = 'com.example.jetnews' GROUP BY process_name, thread_name
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

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so smaller changes could be affected by run-to-run noise; the observed GC and frame-time changes are large.
- The attribution is correlated rather than direct because the trace records the affected process and thread but not a stack sample pointing to the changed source line.

## Run

`gpt-5.6-luna` on openai, effort high: 52 tool calls, $0.0282, 155 s.
Tokens: 45 input, 250,673 cache read, 51,213 cache write, 8,681 output.
