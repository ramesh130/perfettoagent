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

### c1. main_thread_blocked_ms increased from 25.284169 ms to 731.530503 ms, a delta of 706.2463339999999 ms.

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
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

### c2. The selected app is com.superplayer.demo; its UI thread is tid 14487 in baseline and tid 18340 in current.

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
SELECT p.name AS process_name, t.tid, t.name AS thread_name, t.utid
FROM app JOIN process AS p ON p.upid = app.upid
JOIN thread AS t ON t.utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid = app.upid)
ORDER BY t.tid;
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
SELECT p.name AS process_name, t.tid, t.name AS thread_name, t.utid
FROM app JOIN process AS p ON p.upid = app.upid
JOIN thread AS t ON t.utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid = app.upid)
ORDER BY t.tid;
```

### c3. The current trace contains six AndroidOwner:onTouch slices longer than 100 ms, totaling 726.745251 ms, with durations from 120.473625 ms to 122.276042 ms; the baseline has no such slices.

The `current` trace: 1 row.

```sql
SELECT count(*) AS long_touch_slices, sum(dur) / 1e6 AS long_touch_ms, min(dur) / 1e6 AS min_ms, max(dur) / 1e6 AS max_ms
FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 367 AND s.name = 'AndroidOwner:onTouch' AND s.dur > 100000000;
```

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS long_touch_slices, sum(dur) / 1e6 AS long_touch_ms, min(dur) / 1e6 AS min_ms, max(dur) / 1e6 AS max_ms
FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 363 AND s.name = 'AndroidOwner:onTouch' AND s.dur > 100000000;
```

### c4. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b added Thread.sleep(TAP_HOLD_MS) to FeedScreen's onFeedTapped handler and defined TAP_HOLD_MS as 120 ms.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

### c5. The timing and location match: the six current long touch-handler slices account for 726.745251 ms of the 706.2463339999999 ms overall increase, making c70fd55eea9930f42380069d9b1f0a3f22bc403b the direct culprit.

The `current` trace: 1 row.

```sql
SELECT count(*) AS long_touch_slices, sum(dur) / 1e6 AS long_touch_ms, min(dur) / 1e6 AS min_ms, max(dur) / 1e6 AS max_ms
FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 367 AND s.name = 'AndroidOwner:onTouch' AND s.dur > 100000000;
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Caveats

- Only one capture per side is available, so ordinary run-to-run noise cannot be estimated; the roughly 706 ms increase and repeated roughly 120 ms waits are far larger than a small-noise delta.

## Run

`gpt-5.6-luna` on openai, effort high: 35 tool calls, $0.0258, 111 s.
Tokens: 30 input, 154,876 cache read, 37,949 cache write, 10,981 output.
