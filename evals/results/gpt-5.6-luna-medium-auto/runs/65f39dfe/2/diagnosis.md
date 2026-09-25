# Regression

- **Metric:** `frame_p95_ms` +5.44 ms (67.81 → 73.25 ms)
- **Culprit:** `1d113d755374` (correlated); `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`
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

### c1. The app's UI-frame p95 increased from 67.812916 ms in the baseline to 73.252833 ms in the current trace.

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

### c2. The affected workload is the com.superplayer.demo UI thread: its total traced slice time rose from 49359.324528 ms to 52806.651438 ms, while the maximum slice remained in the same UI-thread workload.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT p.name AS process, t.name AS thread, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE t.utid IN (SELECT utid FROM ui) AND s.dur>0
GROUP BY p.name,t.name ORDER BY total_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT p.name AS process, t.name AS thread, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE t.utid IN (SELECT utid FROM ui) AND s.dur>0
GROUP BY p.name,t.name ORDER BY total_ms DESC
```

### c3. The current trace shows more total animation and Compose recomposition work than the baseline: animation rose from 3663.588971 ms to 4165.809446 ms, and Recomposer:recompose rose from 2777.615079 ms to 3238.453879 ms.

The `baseline` trace: 7 rows.

```sql
SELECT name,count(*) AS n,sum(dur)/1e6 AS total_ms,max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('animation','Recomposer:recompose','Compose:onForgotten','AndroidOwner:measureAndLayout','traversal','draw-VRI[MainActivity]','Drawing  0.00  0.00 1080.00 2400.00') GROUP BY name ORDER BY name
```

The `current` trace: 7 rows.

```sql
SELECT name,count(*) AS n,sum(dur)/1e6 AS total_ms,max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('animation','Recomposer:recompose','Compose:onForgotten','AndroidOwner:measureAndLayout','traversal','draw-VRI[MainActivity]','Drawing  0.00  0.00 1080.00 2400.00') GROUP BY name ORDER BY name
```

### c4. The likeliest correlated range change is the TV-controls timeout change in TvScreen.kt, which changed the hide interval to four seconds.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
1d113d755374a5a53047db5fbdb3d18385c0aa3f
```

## Caveats

- Only one capture per side is available, so the frame-tail change may include run-to-run emulator noise.
- The current capture is a non-debuggable benchmark build on an Android emulator.
- The trace does not directly identify TvScreen.kt or the controls-timeout constant in the hot UI slices; attribution is therefore correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort medium: 31 tool calls, $0.0218, 116 s.
Tokens: 18 input, 88,139 cache read, 54,236 cache write, 5,388 output.
