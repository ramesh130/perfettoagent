# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. Main-thread blocking increased from 25.284169 ms in the baseline to 731.530503 ms in the current trace, a delta of 706.246334 ms.

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

### c2. The blocked work is concentrated on the app's UI thread in AndroidOwner:onTouch: baseline 367 slices totaling 148.281792 ms, versus current 387 slices totaling 917.909462 ms; the largest current slice is 122.276042 ms compared with 5.569625 ms baseline.

The `baseline` trace: 1 row.

```sql
SELECT t.name AS thread_name, s.name AS slice_name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE s.name = 'AndroidOwner:onTouch'
GROUP BY t.name, s.name
```

The `current` trace: 1 row.

```sql
SELECT t.name AS thread_name, s.name AS slice_name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE s.name = 'AndroidOwner:onTouch'
GROUP BY t.name, s.name
```

### c3. The current trace contains six long deliverInputEvent spans whose nested AndroidOwner:onTouch work totals 726.745251 ms, accounting for nearly all of the measured main-thread blocking increase.

The `current` trace: 28 rows.

```sql
WITH long_input AS (
  SELECT track_id, ts, dur, name
  FROM slice
  WHERE name LIKE 'deliverInputEvent%' AND dur > 100000000
)
SELECT child.name AS slice_name, child.depth, count(*) AS count,
  sum(child.dur) / 1e6 AS total_ms, max(child.dur) / 1e6 AS max_ms
FROM long_input AS parent
JOIN slice AS child
  ON child.track_id = parent.track_id
 AND child.ts >= parent.ts
 AND child.ts + child.dur <= parent.ts + parent.dur
GROUP BY child.name, child.depth
ORDER BY total_ms DESC
LIMIT 100
```

### c4. The likely cause is commit c70fd55eea9930f42380069d9b1f0a3f22bc403b, which added Thread.sleep(TAP_HOLD_MS) to FeedScreen's tap handler and set TAP_HOLD_MS to 120 ms; the current long input-handler slices match that intended hold duration.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

The `current` trace: 28 rows.

```sql
WITH long_input AS (
  SELECT track_id, ts, dur, name
  FROM slice
  WHERE name LIKE 'deliverInputEvent%' AND dur > 100000000
)
SELECT child.name AS slice_name, child.depth, count(*) AS count,
  sum(child.dur) / 1e6 AS total_ms, max(child.dur) / 1e6 AS max_ms
FROM long_input AS parent
JOIN slice AS child
  ON child.track_id = parent.track_id
 AND child.ts >= parent.ts
 AND child.ts + child.dur <= parent.ts + parent.dur
GROUP BY child.name, child.depth
ORDER BY total_ms DESC
LIMIT 100
```

### c5. Blame at the range head assigns both the Thread.sleep call and the 120 ms TAP_HOLD_MS constant to c70fd55eea9930f42380069d9b1f0a3f22bc403b.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Caveats

- Only one baseline and one current capture were available, so ordinary run-to-run noise cannot be excluded.
- The selected metric measures whole-trace main-thread blocking outside Choreographer#doFrame; it is not itself a frame-latency metric.
- Attribution is correlated rather than direct because the trace exposes the AndroidOwner:onTouch and deliverInputEvent slices, not a source-named FeedScreen stack frame.

## Run

`gpt-5.6-luna` on openai, effort high: 41 tool calls, $0.0225, 188 s.
Tokens: 27 input, 132,184 cache read, 30,683 cache write, 10,126 output.
