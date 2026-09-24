# No regression

- **Metric:** `main_thread_blocked_ms` +19.21 ms (247.59 → 266.81 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `main_thread_blocked_ms` | ms | 247.59 | 266.81 | +19.21 |

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
```

## Claims

### c1. The selected metric increased from 247.594911 ms to 266.806344 ms, a delta of 19.211433 ms.

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
```

### c2. The canned metric selects the process with the most presented frames. That is com.google.android.apps.nexuslauncher in both captures, not com.superplayer.demo: baseline has 1924 versus 473 frames, and current has 1919 versus 476.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT a.id) AS presented_frames
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.name
ORDER BY presented_frames DESC
LIMIT 20
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT a.id) AS presented_frames
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.name
ORDER BY presented_frames DESC
LIMIT 20
```

### c3. A direct com.superplayer.demo frame comparison does not show a frame-duration regression: its frame p95 is 274.668751 ms in baseline and 264.937 ms in current.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH frames AS (
 SELECT DISTINCT f.ui_thread_utid, a.id, a.dur
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 JOIN process p ON p.upid=f.upid
 WHERE p.name='com.superplayer.demo' AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), ranked AS (
 SELECT dur/1e6 AS frame_ms, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER() AS n FROM frames
)
SELECT (SELECT frame_ms FROM ranked WHERE rank=(n*95+99)/100) AS app_frame_p95_ms,
       (SELECT count(*) FROM frames) AS frame_count
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH frames AS (
 SELECT DISTINCT f.ui_thread_utid, a.id, a.dur
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 JOIN process p ON p.upid=f.upid
 WHERE p.name='com.superplayer.demo' AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), ranked AS (
 SELECT dur/1e6 AS frame_ms, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER() AS n FROM frames
)
SELECT (SELECT frame_ms FROM ranked WHERE rank=(n*95+99)/100) AS app_frame_p95_ms,
       (SELECT count(*) FROM frames) AS frame_count
```

### c4. The range includes a MoQ logging-cadence change in c48c1214737c4fc1f3983993d9812f958485b4d1 and a FeedScreen handler rename in d06e018fc738bebf0f5ccf2814efba445a6cfdfe; neither is directly connected by the measured main-thread-blocked rows, which are selected from the launcher process.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
c48c1214737c4fc1f3983993d9812f958485b4d1
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
d06e018fc738bebf0f5ccf2814efba445a6cfdfe
```

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT a.id) AS presented_frames
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.name
ORDER BY presented_frames DESC
LIMIT 20
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT a.id) AS presented_frames
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.name
ORDER BY presented_frames DESC
LIMIT 20
```

## Caveats

- Only one capture is available per side, so the 19.211433 ms change cannot be separated from run-to-run noise.
- The canned metric is dominated by the launcher because it has more presented frames than the demo process; this makes it unsuitable for attributing an app-code regression in this trace pair.
- The app-only UI p95 changed slightly in the opposite direction, so the evidence is mixed rather than a high-confidence performance result.

## Run

`gpt-5.6-luna` on openai, effort high: 67 tool calls, $0.0397, 1009 s.
Tokens: 42 input, 407,785 cache read, 53,280 cache write, 15,149 output.
