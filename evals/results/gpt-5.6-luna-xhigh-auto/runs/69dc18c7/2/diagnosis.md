# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `main_thread_blocked_ms` | ms | 25.28 | 731.53 | +706.25 |

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

### c1. The frame timeline selects com.superplayer.demo; its UI thread is utid 363 in the baseline and utid 367 in the current trace.

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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_count
FROM frames f
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_count
FROM frames f
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
```

### c2. Main-thread blocked time increased from 25.284169 ms to 731.530503 ms, a delta of 706.2463339999999 ms.

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

### c3. The baseline has no UI-thread deliverInputEvent slice longer than 100 ms. The current trace has six such events totaling 727.312415 ms, with individual durations from 120.548 ms to 122.348666 ms.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS long_input_events,
  sum(s.dur) / 1e6 AS total_input_ms,
  min(s.dur) / 1e6 AS shortest_input_ms,
  max(s.dur) / 1e6 AS longest_input_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 363
  AND s.name GLOB 'deliverInputEvent src=*'
  AND s.dur > 100000000
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS long_input_events,
  sum(s.dur) / 1e6 AS total_input_ms,
  min(s.dur) / 1e6 AS shortest_input_ms,
  max(s.dur) / 1e6 AS longest_input_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 367
  AND s.name GLOB 'deliverInputEvent src=*'
  AND s.dur > 100000000
```

### c4. Those six current input events overlap the UI thread's S state for 724.680584 ms across six segments.

The `current` trace: 4 rows.

```sql
WITH target AS (
  SELECT ts, dur
  FROM slice
  WHERE name GLOB 'deliverInputEvent src=*' AND dur > 100000000
)
SELECT ts_state.state,
  sum(min(ts_state.ts + ts_state.dur, target.ts + target.dur) - max(ts_state.ts, target.ts)) / 1e6 AS overlap_ms,
  count(*) AS segment_count
FROM target
JOIN thread_state AS ts_state
  ON ts_state.utid = 367
 AND ts_state.ts < target.ts + target.dur
 AND target.ts < ts_state.ts + ts_state.dur
GROUP BY ts_state.state
ORDER BY overlap_ms DESC
```

### c5. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b changed FeedScreen.kt to add Thread.sleep(TAP_HOLD_MS) and TAP_HOLD_MS = 120L. That change directly matches the six approximately 120 ms sleeping input deliveries in the current trace.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS long_input_events,
  sum(s.dur) / 1e6 AS total_input_ms,
  min(s.dur) / 1e6 AS shortest_input_ms,
  max(s.dur) / 1e6 AS longest_input_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 367
  AND s.name GLOB 'deliverInputEvent src=*'
  AND s.dur > 100000000
```

## Caveats

- Only one capture is available per side, so the whole-trace magnitude remains subject to run-to-run variation.
- The selected metric is a whole-trace sum of main-thread blocking outside doFrame; it diagnoses the input-blocking regression rather than frame-presentation latency.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 45 tool calls, $0.0323, 343 s.
Tokens: 36 input, 206,806 cache read, 36,418 cache write, 15,913 output.
