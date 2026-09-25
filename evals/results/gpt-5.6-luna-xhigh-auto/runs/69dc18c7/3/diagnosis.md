# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 2 claims kept, 1 dropped; 5 of 6 citations passed
- **Model's confidence:** medium (never scored)

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

### c2. The localized difference is on com.superplayer.demo's UI thread uperplayer.demo: the baseline has no top-level deliverInputEvent slice lasting at least 100 ms, while the current trace has 6 totaling 727.312415 ms.

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  input_events AS (
    SELECT s.id, s.dur
    FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.name GLOB 'deliverInputEvent*'
      AND s.dur >= 100000000
  )
SELECT p.name AS process, t.name AS thread,
       count(i.id) AS long_input_events,
       coalesce(sum(i.dur), 0) / 1e6 AS long_input_ms
FROM main_thread AS m
JOIN thread AS t ON t.utid = m.utid
JOIN process AS p ON p.upid = (SELECT upid FROM app)
LEFT JOIN input_events AS i ON 1 = 1
GROUP BY p.name, t.name
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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  input_events AS (
    SELECT s.id, s.dur
    FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.name GLOB 'deliverInputEvent*'
      AND s.dur >= 100000000
  )
SELECT p.name AS process, t.name AS thread,
       count(i.id) AS long_input_events,
       coalesce(sum(i.dur), 0) / 1e6 AS long_input_ms
FROM main_thread AS m
JOIN thread AS t ON t.utid = m.utid
JOIN process AS p ON p.upid = (SELECT upid FROM app)
LEFT JOIN input_events AS i ON 1 = 1
GROUP BY p.name, t.name
```

### c3. The six long current input-delivery slices overlap 724.680584 ms while the UI thread is in scheduler state S, matching a sleep in the input handler; commit c70fd55eea9930f42380069d9b1f0a3f22bc403b changed FeedScreen.kt to add the 120 ms tap hold.

The `current` trace: 4 rows.

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  input_events AS (
    SELECT s.id, s.ts, s.dur
    FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.name GLOB 'deliverInputEvent*'
      AND s.dur >= 100000000
  )
SELECT b.state,
       count(*) AS state_segments,
       sum(min(b.ts + b.dur, i.ts + i.dur) - max(b.ts, i.ts)) / 1e6 AS overlap_ms
FROM input_events AS i
JOIN thread_state AS b
  ON b.utid IN (SELECT utid FROM main_thread)
 AND b.ts < i.ts + i.dur AND i.ts < b.ts + b.dur
GROUP BY b.state
ORDER BY overlap_ms DESC
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Caveats

- Only one capture per side is available, and the captures run on an emulator, so unrelated scheduler variance cannot be fully ruled out.
- The trace does not contain app stack samples tying deliverInputEvent to the Kotlin method directly; attribution is therefore marked correlated rather than direct.

## Dropped claims

### c1. Main-thread blocked time increased from 25.284169 ms to 731.530503 ms, a 706.246334 ms regression.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 32 col 3 ) ^ syntax error near ')'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 32 col 3 ) ^ syntax error near ')'

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
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+'))
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

## Run

`gpt-5.6-luna` on openai, effort xhigh: 54 tool calls, $0.0381, 239 s.
Tokens: 45 input, 335,817 cache read, 36,947 cache write, 18,473 output.
