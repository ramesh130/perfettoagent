# No regression

- **Metric:** `binder_wait_ms` +60.5 ms (287.82 → 348.32 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `binder_wait_ms` | ms | 287.82 | 348.32 | +60.5 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.binder;
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
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
```

## Claims

### c1. Synchronous binder wait on the app's UI thread increased from 287.81833 ms in the baseline to 348.319381 ms in the current trace, a delta of 60.501051 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
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
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
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
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
```

### c2. The increased UI-thread binder wait is concentrated in synchronous calls to SurfaceFlinger; the grouped trace query reports 371 calls and 277.81742 ms in the baseline, versus 400 calls and 348.318318 ms in the current trace.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (SELECT DISTINCT f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), b AS (SELECT * FROM android_binder_txns WHERE is_sync AND client_dur>0 AND client_utid IN (SELECT ui_thread_utid FROM wf)) SELECT server_process, server_thread, aidl_name, count(*) AS calls, sum(client_dur)/1e6 AS wait_ms FROM b GROUP BY server_process,server_thread,aidl_name ORDER BY wait_ms DESC LIMIT 20;
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (SELECT DISTINCT f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), b AS (SELECT * FROM android_binder_txns WHERE is_sync AND client_dur>0 AND client_utid IN (SELECT ui_thread_utid FROM wf)) SELECT server_process, server_thread, aidl_name, count(*) AS calls, sum(client_dur)/1e6 AS wait_ms FROM b GROUP BY server_process,server_thread,aidl_name ORDER BY wait_ms DESC LIMIT 20;
```

### c3. The range includes a FeedScreen change that rewrites player acquisition using takeIf, but the trace evidence only identifies SurfaceFlinger binder activity and does not connect that activity to this commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
328304f8f1081e484f20030bb6518b1b1ee03c82
```

## Caveats

- Each side is represented by a single capture, so the binder delta may be run-to-run variance.
- The captures ran on an Android emulator (sdk_gphone64_arm64, SDK 36), which can add variability to SurfaceFlinger and binder timing.
- The current build was a non-debuggable benchmark build; baseline build metadata was not available.

## Run

`gpt-5.6-luna` on openai, effort low: 21 tool calls, $0.0075, 73 s.
Tokens: 18 input, 41,904 cache read, 11,382 cache write, 3,211 output.
