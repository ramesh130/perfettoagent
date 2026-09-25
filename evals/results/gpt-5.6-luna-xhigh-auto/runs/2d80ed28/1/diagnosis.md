# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 13 of 13 citations passed
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

### c1. The app UI-thread p95 time increased from 26.206625 ms in baseline to 54.169584 ms in current, a 27.962959 ms regression.

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

### c2. The frame-owning process is com.example.jetnews in both captures, with the UI thread named example.jetnews. Its current trace has 1,378 traversal slices totaling 64,394.183702 ms, versus 2,198 traversal slices totaling 15,637.029552 ms in baseline.

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
SELECT p.upid, p.pid, p.name, t.utid, t.tid, t.name AS thread_name, count(*) AS window_frame_count
FROM window_frames AS f
JOIN app ON app.upid = f.upid
JOIN process AS p ON p.upid = f.upid
JOIN thread AS t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.pid, p.name, t.utid, t.tid, t.name
```

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
SELECT p.upid, p.pid, p.name, t.utid, t.tid, t.name AS thread_name, count(*) AS window_frame_count
FROM window_frames AS f
JOIN app ON app.upid = f.upid
JOIN process AS p ON p.upid = f.upid
JOIN thread AS t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.pid, p.name, t.utid, t.tid, t.name
```

The `baseline` trace: 100 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 365 AND s.name NOT GLOB 'Choreographer#doFrame*' AND s.dur > 0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

The `current` trace: 100 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 1 AND s.name NOT GLOB 'Choreographer#doFrame*' AND s.dur > 0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

### c3. Garbage collection is also concentrated in the app: baseline has 2 app GC events totaling 32.61125 ms, while current has 575 totaling 5854.487717 ms. The current GC slices run on the app's HeapTaskDaemon, with 430 young concurrent collections and 145 concurrent collections.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
),
app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT g.upid, p.pid, p.name AS process_name, count(*) AS gc_count,
       sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
WHERE g.upid = (SELECT upid FROM app)
GROUP BY g.upid, p.pid, p.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
),
app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT g.upid, p.pid, p.name AS process_name, count(*) AS gc_count,
       sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
WHERE g.upid = (SELECT upid FROM app)
GROUP BY g.upid, p.pid, p.name
```

The `current` trace: 9 rows.

```sql
SELECT s.name, t.utid, t.tid, t.name AS thread_name, p.name AS process_name,
       count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
LEFT JOIN process AS p ON p.upid = t.upid
WHERE s.name GLOB '*GC*' OR s.name GLOB '*Garbage*'
GROUP BY s.name, t.utid, t.tid, t.name, p.name
ORDER BY total_ms DESC
```

### c4. The likely culprit is bcd3ba1e926293a8681b6246ecdd271b5beb1592: it changes PostCards.kt to launch a withFrameNanos loop and execute drawWithContent with a new 6,000-element random list on every frame. The change is consistent with the current trace's much heavier traversal/draw work and app GC, but the trace does not contain an app CPU stack pointing directly to that source line.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

The `current` trace: 100 rows.

```sql
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 1 AND s.name NOT GLOB 'Choreographer#doFrame*' AND s.dur > 0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
),
app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT g.upid, p.pid, p.name AS process_name, count(*) AS gc_count,
       sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
WHERE g.upid = (SELECT upid FROM app)
GROUP BY g.upid, p.pid, p.name
```

### c5. The bcd3ba1e926293a8681b6246ecdd271b5beb1592 lines in PostCards.kt are attributed to that commit at the range head, confirming it introduced the per-frame grain code.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available, so run-to-run noise cannot be estimated; the observed change is large relative to that limitation.
- The current run is a debuggable debug build on an emulator, and the culprit attribution is correlated rather than a direct stack-level proof.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 51 tool calls, $0.0346, 197 s.
Tokens: 39 input, 234,181 cache read, 36,973 cache write, 17,228 output.
