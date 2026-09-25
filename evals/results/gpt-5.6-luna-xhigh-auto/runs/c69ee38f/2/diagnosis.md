# Inconclusive

- **Metric:** `main_thread_blocked_ms` +19.21 ms (247.59 → 266.81 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The selected metric increased from baseline to current, so the measured blocked time got worse in the current trace.

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

### c2. The blocked time localizes to the launcher UI thread in both traces, primarily in clientTransactionExecuted and window-focus handling, rather than to com.superplayer.demo code.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), work AS (
  SELECT s.ts,s.dur,s.name,t.utid,th.name AS thread_name,p.name AS process_name
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  JOIN thread th ON th.utid=t.utid JOIN process p USING(upid)
  WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0
    AND s.name NOT GLOB 'Choreographer#doFrame*'
), blocked AS (
  SELECT ts,dur,utid FROM thread_state
  WHERE utid IN (SELECT utid FROM main_thread) AND dur>0
    AND state NOT IN ('Running','R','R+')
)
SELECT process_name,thread_name,name AS slice_name,
  sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms
FROM blocked b JOIN work w ON b.utid=w.utid
 AND b.ts<w.ts+w.dur AND w.ts<b.ts+w.dur
GROUP BY process_name,thread_name,name ORDER BY blocked_ms DESC LIMIT 5
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), work AS (
  SELECT s.ts,s.dur,s.name,t.utid,th.name AS thread_name,p.name AS process_name
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  JOIN thread th ON th.utid=t.utid JOIN process p USING(upid)
  WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0
    AND s.name NOT GLOB 'Choreographer#doFrame*'
), blocked AS (
  SELECT ts,dur,utid FROM thread_state
  WHERE utid IN (SELECT utid FROM main_thread) AND dur>0
    AND state NOT IN ('Running','R','R+')
)
SELECT process_name,thread_name,name AS slice_name,
  sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms
FROM blocked b JOIN work w ON b.utid=w.utid
 AND b.ts<w.ts+w.dur AND w.ts<b.ts+w.dur
GROUP BY process_name,thread_name,name ORDER BY blocked_ms DESC LIMIT 5
```

### c3. The metric's process-selection heuristic is dominated by the launcher: it has 1924 baseline and 1919 current window frames, while com.superplayer.demo has 473 and 476 respectively.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT a.id) AS window_frame_count
FROM android_frames_layers f
JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
JOIN process p USING(upid)
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
GROUP BY p.name ORDER BY window_frame_count DESC LIMIT 5
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT a.id) AS window_frame_count
FROM android_frames_layers f
JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
JOIN process p USING(upid)
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
GROUP BY p.name ORDER BY window_frame_count DESC LIMIT 5
```

### c4. The range includes a MoQ-screen logging change in c48c1214737c4fc1f3983993d9812f958485b4d1, but that commit touches MoqScreen.kt and is not a direct match for the launcher thread and slices measured here.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
c48c1214737c4fc1f3983993d9812f958485b4d1
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), work AS (
  SELECT s.ts,s.dur,s.name,t.utid,th.name AS thread_name,p.name AS process_name
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  JOIN thread th ON th.utid=t.utid JOIN process p USING(upid)
  WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0
    AND s.name NOT GLOB 'Choreographer#doFrame*'
), blocked AS (
  SELECT ts,dur,utid FROM thread_state
  WHERE utid IN (SELECT utid FROM main_thread) AND dur>0
    AND state NOT IN ('Running','R','R+')
)
SELECT process_name,thread_name,name AS slice_name,
  sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms
FROM blocked b JOIN work w ON b.utid=w.utid
 AND b.ts<w.ts+w.dur AND w.ts<b.ts+w.dur
GROUP BY process_name,thread_name,name ORDER BY blocked_ms DESC LIMIT 5
```

## Caveats

- This is one capture per side, so the 19.211433 ms increase may be run-to-run noise.
- The chosen canned metric selects the process with the most non-SurfaceView window frames; in these traces that is the Android launcher, which prevents a direct attribution to the SuperPlayer repository.
- The captures were made on an sdk_gphone64_arm64 Android 36 emulator in a benchmark, non-debuggable build.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 99 tool calls, $0.1028, 560 s.
Tokens: 87 input, 1,865,072 cache read, 127,341 cache write, 28,027 output.
