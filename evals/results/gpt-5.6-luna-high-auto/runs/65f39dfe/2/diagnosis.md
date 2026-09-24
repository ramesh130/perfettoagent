# Regression

- **Metric:** `frame_p99_ms` +24.14 ms (115.78 → 139.92 ms)
- **Culprit:** `7fd362610713` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 2 claims kept, 2 dropped; 6 of 9 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p99_ms` | ms | 115.78 | 139.92 | +24.14 |

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

## Claims

### c3. The UI workload is concentrated in Compose lazy-prefetch and FeedRow code: lazy-prefetch composition totals 270.720838 ms in the baseline and 304.11613 ms in the current trace, while both traces contain a FeedScreenKt.FeedRow JIT slice.

The `baseline` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms,
       max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), main_thread AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms,
       max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `baseline` trace: 1 row.

```sql
SELECT name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms
FROM slice WHERE name LIKE '%DownloadsScreen%' OR name LIKE '%DownloadRow%' OR name LIKE '%FeedScreen%' OR name LIKE '%TvScreen%' OR name LIKE '%DemoApp%' GROUP BY name ORDER BY total_ms DESC
```

The `current` trace: 1 row.

```sql
SELECT name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms
FROM slice WHERE name LIKE '%DownloadsScreen%' OR name LIKE '%DownloadRow%' OR name LIKE '%FeedScreen%' OR name LIKE '%TvScreen%' OR name LIKE '%DemoApp%' GROUP BY name ORDER BY total_ms DESC
```

### c4. Commit 7fd3626107135436b97973da12915e1e13f76255 changes the FeedScreen FeedRow player-acquisition block from an if/else form to takeIf/let. Git blame assigns those changed lines to that commit, making it the best correlated candidate, but the trace does not isolate that branch, so the attribution is not direct.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

## Caveats

- Only one capture is available for each side, so the p99 and jank changes may include run-to-run noise.
- The captures are from an emulator benchmark build; the trace evidence correlates the change with FeedScreen but does not prove that the refactored branch caused the delta.

## Dropped claims

### c1. The app's frame p99 worsened from 115.775458 ms in the baseline to 139.919292 ms in the current trace, a delta of 24.143834 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

### c2. The frame timeline identifies the same app, com.superplayer.demo, on its UI thread in both captures; the current capture has 327 app-deadline-missed frames out of 760, versus 306 out of 824 in the baseline.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, f.upid, f.ui_thread_utid,
       count(*) AS frame_count, sum(f.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
       max(f.dur) / 1e6 AS max_frame_ms
FROM window_frames f
JOIN app ON app.upid = f.upid
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.name, p.pid, t.name, f.upid, f.ui_thread_utid
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 9 col 52 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, f.upid, f.ui_thread_utid,
       count(*) AS frame_count, sum(f.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
       max(f.dur) / 1e6 AS max_frame_ms
FROM window_frames f
JOIN app ON app.upid = f.upid
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.name, p.pid, t.name, f.upid, f.ui_thread_utid
```

## Run

`gpt-5.6-luna` on openai, effort high: 78 tool calls, $0.0482, 301 s.
Tokens: 45 input, 374,690 cache read, 95,839 cache write, 13,914 output.
