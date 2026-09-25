# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 1 claim kept, 3 dropped; 4 of 7 citations passed
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

### c3. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b adds Thread.sleep(TAP_HOLD_MS) to FeedScreen's tap handler and defines TAP_HOLD_MS as 120L.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Caveats

- Only one capture per side was available, so unrelated run-to-run variation cannot be excluded.
- The traces were captured on an Android emulator (sdk_gphone64_arm64, SDK 36), not physical hardware.
- Other frame metrics improved in the current trace; this diagnosis specifically concerns the large main-thread blocking regression.

## Dropped claims

### c1. Main-thread blocked time increased from 25.284169 ms in the baseline to 731.530503 ms in the current trace.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
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
SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)) THEN NULL ELSE coalesce((SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts)) FROM blocked AS b JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur), 0) / 1e6 END AS value
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

### c2. The current trace contains six main-thread deliverInputEvent slices lasting at least 100 ms, totaling 727.312415 ms; the baseline contains none.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 3 col 301 _timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app)) ^ syntax error near 'DESC'

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT count(*) FILTER (WHERE s.dur >= 100000000) AS over_100ms, coalesce(sum(s.dur) FILTER (WHERE s.dur >= 100000000),0)/1e6 AS over_100ms_total FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 3 col 301 _timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app)) ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT count(*) FILTER (WHERE s.dur >= 100000000) AS over_100ms, coalesce(sum(s.dur) FILTER (WHERE s.dur >= 100000000),0)/1e6 AS over_100ms_total FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
```

### c4. The added sleep is the direct match for the six roughly 120 ms input-handler stalls in the current trace, while the baseline has no comparable stalls.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 3 col 301 _timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app)) ^ syntax error near 'DESC'

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 3 col 301 _timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app)) ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY count(*) DESC,upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT count(*) FILTER (WHERE s.dur >= 100000000) AS over_100ms, coalesce(sum(s.dur) FILTER (WHERE s.dur >= 100000000),0)/1e6 AS over_100ms_total FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Run

`gpt-5.6-luna` on openai, effort medium: 42 tool calls, $0.0166, 150 s.
Tokens: 30 input, 122,994 cache read, 22,898 cache write, 7,019 output.
