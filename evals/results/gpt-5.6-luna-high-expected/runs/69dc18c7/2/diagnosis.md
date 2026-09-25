# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. main_thread_blocked_ms increased from 25.284169 ms in the baseline to 731.530503 ms in the current trace, a delta of 706.246334 ms.

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

### c2. The current trace contains six long top-level deliverInputEvent slices whose blocked overlap totals 724.680584 ms; the baseline contains no such slice over 100 ms.

The `current` trace: 1 row.

```sql
SELECT count(*) AS input_events, sum(s.dur)/1e6 AS input_slice_ms, coalesce(sum(min(ts.ts+ts.dur,s.ts+s.dur)-max(ts.ts,s.ts)),0)/1e6 AS blocked_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
JOIN thread_state ts ON ts.utid=t.utid AND ts.ts<s.ts+s.dur AND s.ts<ts.ts+ts.dur AND ts.state NOT IN ('Running','R','R+')
WHERE p.name='com.superplayer.demo' AND t.name='uperplayer.demo' AND s.depth=0 AND s.name GLOB 'deliverInputEvent*' AND s.dur>100000000;
```

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS input_events, sum(s.dur)/1e6 AS input_slice_ms, coalesce(sum(min(ts.ts+ts.dur,s.ts+s.dur)-max(ts.ts,s.ts)),0)/1e6 AS blocked_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
JOIN thread_state ts ON ts.utid=t.utid AND ts.ts<s.ts+s.dur AND s.ts<ts.ts+ts.dur AND ts.state NOT IN ('Running','R','R+')
WHERE p.name='com.superplayer.demo' AND t.name='uperplayer.demo' AND s.depth=0 AND s.name GLOB 'deliverInputEvent*' AND s.dur>100000000;
```

### c3. The long input events contain six AndroidOwner:onTouch slices over 100 ms, totaling 726.745251 ms in the current trace; the analogous baseline query finds none.

The `current` trace: 1 row.

```sql
SELECT count(*) AS on_touch_events, sum(s.dur)/1e6 AS on_touch_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND t.name='uperplayer.demo' AND s.depth=2 AND s.name='AndroidOwner:onTouch' AND s.dur>100000000;
```

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS on_touch_events, coalesce(sum(s.dur)/1e6,0) AS on_touch_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND t.name='uperplayer.demo' AND s.depth=2 AND s.name='AndroidOwner:onTouch' AND s.dur>100000000;
```

### c4. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b added Thread.sleep(TAP_HOLD_MS) to FeedScreen's tap handler; the six roughly 120 ms touch stalls make this commit the likely cause of the regression.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS on_touch_events, sum(s.dur)/1e6 AS on_touch_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND t.name='uperplayer.demo' AND s.depth=2 AND s.name='AndroidOwner:onTouch' AND s.dur>100000000;
```

## Caveats

- Each side is a single capture, so the exact blocked-time magnitude may vary between runs.
- The capture was on an Android emulator (sdk_gphone64_arm64, SDK 36); the current build was a non-debuggable benchmark build.

## Run

`gpt-5.6-luna` on openai, effort high: 36 tool calls, $0.0372, 125 s.
Tokens: 54 input, 601,357 cache read, 50,178 cache write, 10,556 output.
