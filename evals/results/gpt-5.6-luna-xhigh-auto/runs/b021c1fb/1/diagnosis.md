# No regression

- **Metric:** `jank_frames_pct` -12.54 percent (54.73 → 42.19 percent)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 9 of 10 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `jank_frames_pct` | percent | 54.73 | 42.19 | -12.54 |

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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
```

## Claims

### c1. App-deadline-missed jank decreased from 54.7337278106509% in the baseline to 42.1917808219178% in the current trace, a delta of -12.541946988733095 percentage points; this is an improvement rather than a regression.

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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
```

### c2. The measured app was com.superplayer.demo. Its UI thread produced 676 frames with 370 app-deadline misses in the baseline, versus 730 frames with 308 misses in the current trace.

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
  frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, t.tid,
       count(*) AS frame_count,
       round(avg(frames.dur) / 1e6, 3) AS avg_frame_ms,
       round(max(frames.dur) / 1e6, 3) AS max_frame_ms,
       sum(frames.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM frames
JOIN process p ON p.upid = frames.upid
JOIN thread t ON t.utid = frames.ui_thread_utid
GROUP BY p.name, p.pid, t.name, t.tid
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
  frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, t.tid,
       count(*) AS frame_count,
       round(avg(frames.dur) / 1e6, 3) AS avg_frame_ms,
       round(max(frames.dur) / 1e6, 3) AS max_frame_ms,
       sum(frames.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM frames
JOIN process p ON p.upid = frames.upid
JOIN thread t ON t.utid = frames.ui_thread_utid
GROUP BY p.name, p.pid, t.name, t.tid
```

### c4. Commit 82cde0d4acda1b40a0044ed8a118b168410d3aee changes the TvScreen controls-hide timeout, while the localized trace rows are Compose lazy-prefetch spans; the available evidence does not support assigning that commit as a performance culprit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
82cde0d4acda1b40a0044ed8a118b168410d3aee
```

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT s.name, count(*) AS slice_count,
       round(sum(s.dur) / 1e6, 3) AS total_ms,
       round(max(s.dur) / 1e6, 3) AS max_ms
FROM slice s
JOIN thread_track t ON t.id = s.track_id
WHERE t.utid = (SELECT ui_thread_utid FROM frames LIMIT 1)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame')
GROUP BY s.name
ORDER BY s.name
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT s.name, count(*) AS slice_count,
       round(sum(s.dur) / 1e6, 3) AS total_ms,
       round(max(s.dur) / 1e6, 3) AS max_ms
FROM slice s
JOIN thread_track t ON t.id = s.track_id
WHERE t.utid = (SELECT ui_thread_utid FROM frames LIMIT 1)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame')
GROUP BY s.name
ORDER BY s.name
```

## Caveats

- Only one capture is available for each side, so run-to-run variance cannot be ruled out.
- The trace evidence localizes runtime Compose work but does not provide a source-level stack frame linking that work to a commit in the range.

## Dropped claims

### c3. The main-thread trace work that changed most visibly was Compose lazy prefetch: compose-prefetch time fell from 363.846 ms over 57 slices to 83.325 ms over 20 slices, while idle-frame prefetch rose from 67.201 ms over 10 slices to 305.578 ms over 38 slices.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT s.name, count(*) AS slice_count,
       round(sum(s.dur) / 1e6, 3) AS total_ms,
       round(max(s.dur) / 1e6, 3) AS max_ms
FROM slice s
JOIN thread_track t ON t.id = s.track_id
WHERE t.utid = (SELECT ui_thread_utid FROM frames LIMIT 1)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame')
GROUP BY s.name
ORDER BY s.name
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY count(*) ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT s.name, count(*) AS slice_count,
       round(sum(s.dur) / 1e6, 3) AS total_ms,
       round(max(s.dur) / 1e6, 3) AS max_ms
FROM slice s
JOIN thread_track t ON t.id = s.track_id
WHERE t.utid = (SELECT ui_thread_utid FROM frames LIMIT 1)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame')
GROUP BY s.name
ORDER BY s.name
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
82cde0d4acda1b40a0044ed8a118b168410d3aee
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 60 tool calls, $0.0423, 255 s.
Tokens: 45 input, 321,510 cache read, 44,387 cache write, 20,630 output.
