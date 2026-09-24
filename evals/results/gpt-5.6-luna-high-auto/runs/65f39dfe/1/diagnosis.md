# Regression

- **Metric:** `frame_p95_ms` +5.44 ms (67.81 → 73.25 ms)
- **Culprit:** `7fd362610713` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 1 dropped; 9 of 10 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 67.81 | 73.25 | +5.44 |

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
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c2. The affected application is com.superplayer.demo, and the frame-drawing thread is the app's main thread. The current trace has fewer recorded frames but more App Deadline Missed frames.

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
SELECT p.name AS process_name, p.pid, t.name AS thread_name, t.tid,
  count(*) AS frame_count,
  min(dur) / 1e6 AS min_ms,
  avg(dur) / 1e6 AS avg_ms,
  max(dur) / 1e6 AS max_ms,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM frames f
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.name, p.pid, t.name, t.tid
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
SELECT p.name AS process_name, p.pid, t.name AS thread_name, t.tid,
  count(*) AS frame_count,
  min(dur) / 1e6 AS min_ms,
  avg(dur) / 1e6 AS avg_ms,
  max(dur) / 1e6 AS max_ms,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM frames f
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.name, p.pid, t.name, t.tid
```

### c3. On the app's main thread, compose:lazy:prefetch:compose increased from 270.720838 ms across 57 slices to 304.11613 ms across 61 slices.

The `baseline` trace: 30 rows.

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
  main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms,
  max(s.dur) / 1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id = s.track_id
WHERE tt.utid IN (SELECT utid FROM main_thread)
  AND s.depth = 0 AND s.dur > 0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

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
  main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames)
SELECT s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms,
  max(s.dur) / 1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id = s.track_id
WHERE tt.utid IN (SELECT utid FROM main_thread)
  AND s.depth = 0 AND s.dur > 0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

### c4. The corresponding playback-thread drainAndFeed work also increased: from 9525.973902 ms on SuperPlayer:Poo in the baseline to 9757.118609 ms in the current trace.

The `baseline` trace: 2 rows.

```sql
SELECT t.name AS thread_name, p.name AS process_name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE s.name='drainAndFeed' AND s.dur>0
GROUP BY p.name,t.name ORDER BY total_ms DESC
```

The `current` trace: 2 rows.

```sql
SELECT t.name AS thread_name, p.name AS process_name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE s.name='drainAndFeed' AND s.dur>0
GROUP BY p.name,t.name ORDER BY total_ms DESC
```

### c5. The range commit 7fd3626107135436b97973da12915e1e13f76255 changes FeedScreen's FeedRow player-acquisition code, which is the code path represented by the feed trace evidence; it is therefore the likely direct culprit.

The `current` trace: 1 row.

```sql
SELECT name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE dur > 0 AND name GLOB '*FeedScreen*' GROUP BY name ORDER BY total_ms DESC
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

## Caveats

- Only one capture is available for each side, so the frame-percentile and scheduling differences may include run-to-run noise.
- The capture is from an emulator (sdk_gphone64_arm64) using a non-debuggable benchmark build; the trace has no stack-profile samples to prove method-level CPU causality.

## Dropped claims

### c1. The UI frame p95 worsened from 67.812916 ms in the baseline to 73.252833 ms in the current trace.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort high: 53 tool calls, $0.0296, 229 s.
Tokens: 36 input, 227,791 cache read, 40,093 cache write, 12,486 output.
