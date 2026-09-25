# No regression

- **Metric:** `binder_wait_ms` +60.5 ms (287.82 → 348.32 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The selected metric, synchronous binder wait on the app's UI thread, increased from 287.81833 ms in the baseline to 348.319381 ms in the current trace.

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

### c2. The UI thread's synchronous binder calls were all to SurfaceFlinger; the baseline had 371 calls and the current trace had 400 calls.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1), tx AS (SELECT t.*, p.name AS process_name FROM android_binder_txns t LEFT JOIN process p ON p.upid=t.server_upid WHERE t.is_sync AND t.client_dur>0 AND t.client_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app))) SELECT process_name, aidl_name, count(*) AS cnt, sum(client_dur)/1e6 AS wait_ms FROM tx GROUP BY process_name, aidl_name ORDER BY wait_ms DESC LIMIT 20
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1), tx AS (SELECT t.*, p.name AS process_name FROM android_binder_txns t LEFT JOIN process p ON p.upid=t.server_upid WHERE t.is_sync AND t.client_dur>0 AND t.client_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app))) SELECT process_name, aidl_name, count(*) AS cnt, sum(client_dur)/1e6 AS wait_ms FROM tx GROUP BY process_name, aidl_name ORDER BY wait_ms DESC LIMIT 20
```

### c3. The range does not provide a code-level culprit for this increase: the apparent candidate at the range head changes only a FeedScreen comment, while the surrounding player/collector behavior is unchanged.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
f871266864fac1b4f44ff750e6a2fc5d5b07d4a1
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
328304f8f1081e484f20030bb6518b1b1ee03c82
```

### c4. The frame-level metrics did not worsen: frame p95 decreased from 76.544292 ms to 73.255125 ms, and UI-thread frame p95 decreased from 39.433416 ms to 36.989875 ms.

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

## Caveats

- Each side is a single capture, so the binder-wait increase may be run-to-run variability.
- The capture ran on an Android emulator (sdk_gphone64_arm64, SDK 36); no startup timing data was present.
- The current build was non-debuggable and had no recorded tree dirtiness.

## Run

`gpt-5.6-luna` on openai, effort low: 15 tool calls, $0.0069, 62 s.
Tokens: 18 input, 40,864 cache read, 8,007 cache write, 3,377 output.
