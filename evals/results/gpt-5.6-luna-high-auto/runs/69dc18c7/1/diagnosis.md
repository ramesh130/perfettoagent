# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 1 dropped; 9 of 11 citations passed
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

### c2. The frame-selected app is com.superplayer.demo, and its UI thread is recorded as uperplayer.demo in both traces.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
)
SELECT p.name AS process, t.name AS thread, t.utid
FROM app JOIN process p ON p.upid=app.upid JOIN thread t ON t.utid=app.ui_thread_utid;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
)
SELECT p.name AS process, t.name AS thread, t.utid
FROM app JOIN process p ON p.upid=app.upid JOIN thread t ON t.utid=app.ui_thread_utid;
```

### c3. The baseline has no top-level deliverInputEvent slice longer than 100 ms, while the current trace has six, totaling 727.312415 ms with a maximum of 122.348666 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
), long AS (
  SELECT s.ts, s.dur, s.track_id FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN app ON app.ui_thread_utid=tt.utid
  WHERE s.depth=0 AND s.dur>100000000 AND s.name GLOB 'deliverInputEvent*'
)
SELECT count(*) AS long_input_events, coalesce(sum(dur),0)/1e6 AS total_ms, coalesce(max(dur),0)/1e6 AS max_ms
FROM long;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
), long AS (
  SELECT s.ts, s.dur, s.track_id FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN app ON app.ui_thread_utid=tt.utid
  WHERE s.depth=0 AND s.dur>100000000 AND s.name GLOB 'deliverInputEvent*'
)
SELECT count(*) AS long_input_events, coalesce(sum(dur),0)/1e6 AS total_ms, coalesce(max(dur),0)/1e6 AS max_ms
FROM long;
```

### c4. The six long current input events are almost entirely AndroidOwner:onTouch work and sleeping UI-thread states: the child slices total 726.745251 ms, while S states total 724.680584 ms.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
), long AS (
  SELECT s.ts,s.dur,s.track_id FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN app ON app.ui_thread_utid=tt.utid
  WHERE s.depth=0 AND s.dur>100000000 AND s.name GLOB 'deliverInputEvent*'
)
SELECT count(*) AS on_touch_children, coalesce(sum(c.dur),0)/1e6 AS on_touch_ms, coalesce(max(c.dur),0)/1e6 AS max_on_touch_ms
FROM long l JOIN slice c ON c.track_id=l.track_id AND c.ts>=l.ts AND c.ts<l.ts+l.dur
WHERE c.name='AndroidOwner:onTouch';
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
), long AS (
  SELECT s.ts,s.dur,s.track_id FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN app ON app.ui_thread_utid=tt.utid
  WHERE s.depth=0 AND s.dur>100000000 AND s.name GLOB 'deliverInputEvent*'
)
SELECT count(*) AS sleeping_states, coalesce(sum(st.dur),0)/1e6 AS sleeping_ms, coalesce(max(st.dur),0)/1e6 AS max_sleep_ms
FROM long l JOIN thread_state st ON st.utid=(SELECT ui_thread_utid FROM app) AND st.ts>=l.ts AND st.ts<l.ts+l.dur
WHERE st.state='S';
```

### c5. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b added Thread.sleep(TAP_HOLD_MS) to FeedScreen's onFeedTapped handler and set TAP_HOLD_MS to 120L; blame at the range head attributes both lines to that commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

### c6. The matching six roughly 120 ms sleeping input handlers and the c70 change directly attribute the blocking regression to c70fd55eea9930f42380069d9b1f0a3f22bc403b.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid, f.ui_thread_utid
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  GROUP BY f.upid, f.ui_thread_utid ORDER BY count(*) DESC LIMIT 1
), long AS (
  SELECT s.ts,s.dur,s.track_id FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN app ON app.ui_thread_utid=tt.utid
  WHERE s.depth=0 AND s.dur>100000000 AND s.name GLOB 'deliverInputEvent*'
)
SELECT count(*) AS sleeping_states, coalesce(sum(st.dur),0)/1e6 AS sleeping_ms, coalesce(max(st.dur),0)/1e6 AS max_sleep_ms
FROM long l JOIN thread_state st ON st.utid=(SELECT ui_thread_utid FROM app) AND st.ts>=l.ts AND st.ts<l.ts+l.dur
WHERE st.state='S';
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Caveats

- Only one capture per side is available, so unrelated run-to-run variation cannot be ruled out.
- The selected metric measures blocked time in non-frame top-level traced work; it is a blocking regression even though it is not itself a frame-latency percentile.

## Dropped claims

### c1. Main-thread blocked time increased from 25.284169 ms in the baseline to 731.530503 ms in the current trace, a delta of 706.2463339999999 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 43 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such table: frames; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 43 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such table: frames

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 43 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such table: frames

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 43 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such table: frames

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

## Run

`gpt-5.6-luna` on openai, effort high: 43 tool calls, $0.0242, 780 s.
Tokens: 24 input, 92,485 cache read, 26,874 cache write, 13,010 output.
