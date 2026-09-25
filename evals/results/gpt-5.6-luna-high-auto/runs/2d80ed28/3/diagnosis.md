# Regression

- **Metric:** `gc_time_ms` +5,821.88 ms (32.61 → 5,854.49 ms)
- **Culprit:** `bcd3ba1e9262` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

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

### c1. App GC time increased from 32.61125 ms in the baseline to 5854.487717 ms in the current trace, a 5821.876467 ms increase.

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

### c2. The Jetnews process went from 2 GC events totaling 32.61125 ms in the baseline to 575 events totaling 5854.487717 ms in the current trace.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.pid, p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur)/1e6 AS gc_ms,
       sum(g.gc_running_dur)/1e6 AS running_ms, sum(g.gc_runnable_dur)/1e6 AS runnable_ms,
       sum(g.reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid
WHERE g.upid=(SELECT upid FROM app)
GROUP BY p.pid,p.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.pid, p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur)/1e6 AS gc_ms,
       sum(g.gc_running_dur)/1e6 AS running_ms, sum(g.gc_runnable_dur)/1e6 AS runnable_ms,
       sum(g.reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid
WHERE g.upid=(SELECT upid FROM app)
GROUP BY p.pid,p.name
```

### c3. The regression is concentrated in UI drawing: total doFrame time rose from 18919.493771 ms to 65201.813685 ms, the maximum doFrame rose from 51.815417 ms to 93.675042 ms, and app-deadline-missed frames rose from 267 to 1376.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC,upid LIMIT 1),
frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
ui AS (SELECT s.dur/1e6 AS ui_ms, s.ts, s.name FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid=(SELECT ui_thread_utid FROM app))
SELECT (SELECT count(*) FROM frames) AS frame_count,
       (SELECT count(*) FROM ui) AS do_frame_count,
       (SELECT sum(ui_ms) FROM ui) AS do_frame_total_ms,
       (SELECT max(ui_ms) FROM ui) AS max_do_frame_ms,
       (SELECT count(*) FROM frames WHERE jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC,upid LIMIT 1),
frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
ui AS (SELECT s.dur/1e6 AS ui_ms, s.ts, s.name FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid=(SELECT ui_thread_utid FROM app))
SELECT (SELECT count(*) FROM frames) AS frame_count,
       (SELECT count(*) FROM ui) AS do_frame_count,
       (SELECT sum(ui_ms) FROM ui) AS do_frame_total_ms,
       (SELECT max(ui_ms) FROM ui) AS max_do_frame_ms,
       (SELECT count(*) FROM frames WHERE jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
```

### c4. The current trace contains UI work attributed to com.example.jetnews.ui.home.PostCardsKt, and the only range commit changing that source file adds a per-frame grain effect that allocates a 6000-element random list during drawing; blame at the range head assigns those added lines to commit bcd3ba1e926293a8681b6246ecdd271b5beb1592.

The `current` trace: 33 rows.

```sql
SELECT name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms
FROM slice
WHERE name GLOB '*PostCard*' OR name GLOB '*PostCards*'
GROUP BY name ORDER BY total_ms DESC
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side has only one capture, so smaller changes could be affected by run-to-run noise; this change is nevertheless large and corroborated by GC, UI-time, and jank data.
- The captures are from a debuggable build on an Android SDK 36 emulator, and the GC metric is summed collector wall time rather than direct main-thread pause time.

## Run

`gpt-5.6-luna` on openai, effort high: 35 tool calls, $0.0178, 130 s.
Tokens: 30 input, 125,967 cache read, 21,625 cache write, 8,185 output.
