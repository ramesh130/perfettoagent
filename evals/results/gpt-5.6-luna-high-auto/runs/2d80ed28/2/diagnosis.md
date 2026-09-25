# Regression

- **Metric:** `gc_time_ms` +5,821.88 ms (32.61 → 5,854.49 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. The app's garbage-collection time increased from 32.61125 ms in the baseline to 5854.487717 ms in the current trace, a delta of 5821.876467 ms.

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

### c2. The current trace contains 575 GC events for com.example.jetnews totaling 5854.487717 ms, versus 2 events totaling 32.61125 ms in the baseline.

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur)/1e6 AS gc_ms, sum(g.reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events g JOIN process p USING(upid)
GROUP BY p.upid,p.name ORDER BY gc_ms DESC LIMIT 10
```

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, count(*) AS gc_count, sum(g.gc_dur)/1e6 AS gc_ms, sum(g.reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events g JOIN process p USING(upid)
GROUP BY p.upid,p.name ORDER BY gc_ms DESC LIMIT 10
```

### c3. The main-thread traversal work also became substantially more expensive: average traversal duration was 46.6962898484409 ms in the current trace versus 7.11420816742493 ms in the baseline.

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid,count(*) AS n FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY n DESC LIMIT 1)
SELECT s.name,count(*) AS slices,sum(s.dur)/1e6 AS total_ms,avg(s.dur)/1e6 AS avg_ms,max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid=(SELECT ui_thread_utid FROM app) AND s.name IN ('traversal','draw-VRI[MainActivity]','Record View#draw()','AndroidOwner:draw','Compose:recompose','AndroidOwner:measureAndLayout')
GROUP BY s.name ORDER BY total_ms DESC
```

The `baseline` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid,count(*) AS n FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY n DESC LIMIT 1)
SELECT s.name,count(*) AS slices,sum(s.dur)/1e6 AS total_ms,avg(s.dur)/1e6 AS avg_ms,max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid=(SELECT ui_thread_utid FROM app) AND s.name IN ('traversal','draw-VRI[MainActivity]','Record View#draw()','AndroidOwner:draw','Compose:recompose','AndroidOwner:measureAndLayout')
GROUP BY s.name ORDER BY total_ms DESC
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 adds a per-frame LaunchedEffect and drawWithContent implementation in PostCards.kt that creates a 6000-element random List during drawing; git blame assigns those lines to this commit. This matches the current trace's increased drawing cost and allocation-driven GC, making it the correlated culprit in the range.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side, so small changes could be run-to-run noise; the observed GC and drawing changes are large.
- The traces were captured on an Android emulator using a debuggable debug build.

## Run

`gpt-5.6-luna` on openai, effort high: 45 tool calls, $0.0202, 142 s.
Tokens: 27 input, 108,584 cache read, 27,447 cache write, 9,265 output.
