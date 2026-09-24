# Regression

- **Metric:** `frame_p95_ms` +5.44 ms (67.81 → 73.25 ms)
- **Culprit:** `7fd362610713` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. The app's frame p95 increased from 67.812916 ms in the baseline to 73.252833 ms in the current trace, a 5.439916999999994 ms increase.

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
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

### c2. The selected workload is com.superplayer.demo; its UI thread is the recorded frame-drawing thread, and the app trace also contains SuperPlayer playback activity in both captures.

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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_rows
FROM window_frames wf
JOIN app USING (upid)
JOIN process p USING (upid)
JOIN thread t ON t.utid = wf.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
ORDER BY frame_rows DESC;
```

The `current` trace: 29 rows.

```sql
SELECT t.name AS thread_name,count(*) AS slices,sum(s.dur)/1e6 AS total_ms FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid WHERE p.name='com.superplayer.demo' GROUP BY t.name ORDER BY total_ms DESC LIMIT 30;
```

### c3. The current trace shows more aggregate Compose recomposition and forgotten-composition work than the baseline, while lazy-prefetch composition also increased; this localizes the change to the app UI workload rather than startup or memory metrics.

The `baseline` trace: 4 rows.

```sql
SELECT name,count(*) AS occurrences,sum(dur)/1e6 AS total_ms FROM slice WHERE name IN ('Compose:recompose','Recomposer:recompose','Compose:onForgotten','compose:lazy:prefetch:compose') GROUP BY name ORDER BY name;
```

The `current` trace: 4 rows.

```sql
SELECT name,count(*) AS occurrences,sum(dur)/1e6 AS total_ms FROM slice WHERE name IN ('Compose:recompose','Recomposer:recompose','Compose:onForgotten','compose:lazy:prefetch:compose') GROUP BY name ORDER BY name;
```

### c4. Commit 7fd3626107135436b97973da12915e1e13f76255 rewrites the watched-row player acquisition in FeedScreen from an if/else to takeIf/let, and blame at the range head assigns that changed expression to this commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

## Caveats

- Only one capture is available per side, so the frame delta may include run-to-run noise.
- The current capture was a non-debuggable benchmark build on an Android SDK 36 emulator.
- The culprit attribution is correlated rather than direct: the trace exposes Compose and playback slices but does not expose a source-level FeedScreen frame pointing uniquely to the changed expression.

## Run

`gpt-5.6-luna` on openai, effort high: 69 tool calls, $0.0447, 269 s.
Tokens: 54 input, 522,566 cache read, 74,996 cache write, 12,873 output.
