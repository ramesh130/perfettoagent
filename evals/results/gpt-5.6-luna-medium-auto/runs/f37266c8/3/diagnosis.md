# No regression

- **Metric:** `frame_p95_ms` -3.29 ms (76.54 → 73.26 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 76.54 | 73.26 | -3.29 |

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

### c1. The selected frame p95 metric improved: it fell from 76.544292 ms in the baseline to 73.255125 ms in the current trace, a delta of -3.289166999999992 ms.

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

### c2. The trace-localized synchronous binder waits were to SurfaceFlinger; their summed waits increased from 287.81833 ms to 348.319381 ms, but this did not translate into a frame-p95 regression.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)) SELECT b.server_utid, p.name AS server_process, t.name AS server_thread, count(*) AS calls, sum(b.client_dur)/1e6 AS wait_ms FROM android_binder_txns b LEFT JOIN thread t ON t.utid=b.server_utid LEFT JOIN process p ON p.upid=t.upid WHERE b.is_sync AND b.client_dur>0 AND b.client_utid IN (SELECT ui_thread_utid FROM frames) GROUP BY b.server_utid,p.name,t.name ORDER BY wait_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)) SELECT b.server_utid, p.name AS server_process, t.name AS server_thread, count(*) AS calls, sum(b.client_dur)/1e6 AS wait_ms FROM android_binder_txns b LEFT JOIN thread t ON t.utid=b.server_utid LEFT JOIN process p ON p.upid=t.upid WHERE b.is_sync AND b.client_dur>0 AND b.client_utid IN (SELECT ui_thread_utid FROM frames) GROUP BY b.server_utid,p.name,t.name ORDER BY wait_ms DESC
```

### c3. The range's latest FeedScreen change only replaces a comment; blame attributes that line to f871266864fac1b4f44ff750e6a2fc5d5b07d4a1, so there is no direct code change there to attribute a frame regression to.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
f871266864fac1b4f44ff750e6a2fc5d5b07d4a1
```

## Caveats

- This conclusion is based on one capture per side, so small changes can be run-to-run noise.
- The captures were made on an Android emulator (sdk_gphone64_arm64, SDK 36), using a non-debuggable benchmark build.
- The binder-wait increase is a secondary metric and is not evidence of a frame-time regression by itself.

## Run

`gpt-5.6-luna` on openai, effort medium: 41 tool calls, $0.0169, 146 s.
Tokens: 42 input, 154,820 cache read, 20,974 cache write, 7,117 output.
