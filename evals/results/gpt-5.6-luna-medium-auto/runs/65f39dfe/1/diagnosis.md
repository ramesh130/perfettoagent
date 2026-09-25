# Regression

- **Metric:** `frame_p99_ms` +24.14 ms (115.78 → 139.92 ms)
- **Culprit:** `7fd362610713` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** medium (never scored)

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

### c1. The app's frame p99 increased from 115.775458 ms in the baseline to 139.919292 ms in the current trace, a 24.143834 ms increase.

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

### c2. The measured app process was com.superplayer.demo in both traces; its frame count fell from 824 to 760 while total frame time rose from 31609.86214 ms to 32103.317178 ms.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count, sum(a.dur) / 1e6 AS total_frame_ms, max(a.dur) / 1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, f.ui_thread_utid
ORDER BY frame_count DESC
LIMIT 10
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count, sum(a.dur) / 1e6 AS total_frame_ms, max(a.dur) / 1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, f.ui_thread_utid
ORDER BY frame_count DESC
LIMIT 10
```

### c3. The UI-thread trace shows compose:lazy:prefetch:compose increasing from 270.720838 ms across 57 slices to 304.11613 ms across 61 slices, with its maximum slice increasing from 24.557917 ms to 34.039209 ms.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1), main_thread AS (SELECT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app) GROUP BY ui_thread_utid)
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid IN (SELECT utid FROM main_thread) AND s.depth=0 GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1), main_thread AS (SELECT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app) GROUP BY ui_thread_utid)
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON tt.id=s.track_id WHERE tt.utid IN (SELECT utid FROM main_thread) AND s.depth=0 GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

### c4. The range commit 7fd3626107135436b97973da12915e1e13f76255 changes FeedScreen.kt in the watched-row player acquisition path, matching the FeedScreen/Compose area where the regression is localized.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

## Caveats

- This diagnosis compares one capture per side; the frame p99 is sensitive to run-to-run variation.
- The captures were taken on an Android emulator (sdk_gphone64_arm64, SDK 36), so device scheduling may contribute to the observed change.
- The trace evidence localizes the change to Compose lazy prefetch and the commit changes the corresponding FeedScreen path, but does not provide a direct source-level stack attribution; the culprit is therefore correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort medium: 35 tool calls, $0.0126, 124 s.
Tokens: 21 input, 62,693 cache read, 17,482 cache write, 5,843 output.
