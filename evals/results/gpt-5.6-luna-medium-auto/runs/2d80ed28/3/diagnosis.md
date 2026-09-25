# Regression

- **Metric:** `gc_time_ms` +5,821.88 ms (32.61 → 5,854.49 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. Garbage-collection time increased substantially: the app's GC events totaled 32.61125 ms in the baseline and 5854.487717 ms in the current trace.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH
  window_frames AS (
   SELECT DISTINCT f.upid, f.ui_thread_utid, a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.name AS process, t.name AS thread, count(*) AS gc_events, sum(g.gc_dur)/1e6 AS gc_ms, max(g.gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid JOIN thread t ON t.utid=g.utid
WHERE g.upid=(SELECT upid FROM app)
GROUP BY p.name,t.name ORDER BY gc_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH
  window_frames AS (
   SELECT DISTINCT f.upid, f.ui_thread_utid, a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.name AS process, t.name AS thread, count(*) AS gc_events, sum(g.gc_dur)/1e6 AS gc_ms, max(g.gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid JOIN thread t ON t.utid=g.utid
WHERE g.upid=(SELECT upid FROM app)
GROUP BY p.name,t.name ORDER BY gc_ms DESC
```

### c2. The GC increase is localized to com.example.jetnews's HeapTaskDaemon: 2 collections occurred in the baseline versus 575 in the current trace.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH
  window_frames AS (
   SELECT DISTINCT f.upid, f.ui_thread_utid, a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.name AS process, t.name AS thread, count(*) AS gc_events, sum(g.gc_dur)/1e6 AS gc_ms, max(g.gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid JOIN thread t ON t.utid=g.utid
WHERE g.upid=(SELECT upid FROM app)
GROUP BY p.name,t.name ORDER BY gc_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH
  window_frames AS (
   SELECT DISTINCT f.upid, f.ui_thread_utid, a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.name AS process, t.name AS thread, count(*) AS gc_events, sum(g.gc_dur)/1e6 AS gc_ms, max(g.gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid JOIN thread t ON t.utid=g.utid
WHERE g.upid=(SELECT upid FROM app)
GROUP BY p.name,t.name ORDER BY gc_ms DESC
```

### c3. The UI thread's rendering work also expanded: baseline traversal and draw-VRI[MainActivity] each totaled about 15.6 seconds, while current totals were about 64.4 seconds; current Record View#draw() and AndroidOwner:draw dominated the UI slices.

The `baseline` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM main) AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM main) AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 adds a per-frame grain effect to PostCardSimple: it advances state with withFrameNanos and allocates a 6000-element random List inside drawWithContent on every draw.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

### c5. The added grain-effect lines in PostCards.kt are attributed by blame to commit bcd3ba1e926293a8681b6246ecdd271b5beb1592.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion uses one capture per side, so exact magnitudes may include run-to-run noise; the increase is nevertheless large relative to that limitation.
- Both captures ran on an Android emulator, and the current build was debuggable, so timings may not represent a release build on physical hardware.

## Run

`gpt-5.6-luna` on openai, effort medium: 20 tool calls, $0.0120, 76 s.
Tokens: 12 input, 20,161 cache read, 26,579 cache write, 4,092 output.
