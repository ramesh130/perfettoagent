# Regression

- **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
- **Culprit:** `c70fd55eea99` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The app's main-thread blocked time increased from 25.284169 ms in baseline to 731.530503 ms in current, a delta of 706.2463339999999 ms.

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

### c2. The current trace localizes the increase to com.superplayer.demo's main thread, uperplayer.demo (tid 18340): six top-level deliverInputEvent slices longer than 100 ms account for 727.312415 ms, with a maximum of 122.348666 ms. Baseline has no such long input-event slice.

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, th.tid, th.name AS thread_name, count(*) AS long_input_events, sum(s.dur)/1e6 AS total_long_input_ms, max(s.dur)/1e6 AS max_long_input_ms FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid JOIN process p ON p.upid=th.upid WHERE tt.utid=367 AND s.depth=0 AND s.name GLOB 'deliverInputEvent*' AND s.dur>100000000 GROUP BY p.name,th.tid,th.name;
```

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS long_input_events, coalesce(sum(dur),0)/1e6 AS total_long_input_ms, coalesce(max(dur),0)/1e6 AS max_long_input_ms FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid=363 AND s.depth=0 AND s.name GLOB 'deliverInputEvent*' AND s.dur>100000000;
```

### c3. Those six current input events are almost entirely blocked: the trace shows blocked portions of approximately 120 ms for each event, inside deliverInputEvent on the main thread.

The `current` trace: 10 rows.

```sql
WITH work AS (SELECT s.ts,s.dur,s.name FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid=367 AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts,dur FROM thread_state WHERE utid=367 AND dur>0 AND state NOT IN ('Running','R','R+')), overlaps AS (SELECT w.name,w.ts,w.dur,sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts)) AS blocked_ns FROM work w JOIN blocked b ON b.ts<w.ts+w.dur AND w.ts<b.ts+w.dur GROUP BY w.name,w.ts,w.dur) SELECT name,ts/1e6 AS ts_ms,dur/1e6 AS dur_ms,blocked_ns/1e6 AS blocked_ms FROM overlaps WHERE name GLOB 'deliverInputEvent*' ORDER BY blocked_ms DESC LIMIT 10;
```

### c4. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b added Thread.sleep(TAP_HOLD_MS) to FeedScreen's onFeedTapped handler and defined TAP_HOLD_MS as 120L.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

### c5. The trace's repeated approximately 120 ms main-thread stalls directly match that newly added tap-handler sleep, so c70fd55eea9930f42380069d9b1f0a3f22bc403b is the direct culprit.

The `current` trace: 10 rows.

```sql
WITH work AS (SELECT s.ts,s.dur,s.name FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid=367 AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts,dur FROM thread_state WHERE utid=367 AND dur>0 AND state NOT IN ('Running','R','R+')), overlaps AS (SELECT w.name,w.ts,w.dur,sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts)) AS blocked_ns FROM work w JOIN blocked b ON b.ts<w.ts+w.dur AND w.ts<b.ts+w.dur GROUP BY w.name,w.ts,w.dur) SELECT name,ts/1e6 AS ts_ms,dur/1e6 AS dur_ms,blocked_ns/1e6 AS blocked_ms FROM overlaps WHERE name GLOB 'deliverInputEvent*' ORDER BY blocked_ms DESC LIMIT 10;
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c70fd55eea9930f42380069d9b1f0a3f22bc403b
```

## Caveats

- Only one capture is available for each side, so ordinary run-to-run noise is not quantified; however, the change is large and the trace pattern directly matches the 120 ms sleep introduced in the range.
- The metric excludes blocking inside Choreographer#doFrame and only counts blocking inside top-level traced work slices.

## Run

`gpt-5.6-luna` on openai, effort high: 51 tool calls, $0.0485, 164 s.
Tokens: 57 input, 659,590 cache read, 73,562 cache write, 14,053 output.
