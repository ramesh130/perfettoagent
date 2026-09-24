# No regression

- **Metric:** `frame_p95_ms` -9.2 ms (81.5 → 72.3 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 1 dropped; 11 of 11 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 81.5 | 72.3 | -9.2 |

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

### c1. The selected UI frame p95 improved from 81.499417 ms in the baseline to 72.295959 ms in the current trace, a delta of -9.203457999999998 ms; this is not a performance regression.

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

### c2. The measured frame population is in com.superplayer.demo: 676 frames in the baseline and 730 in the current trace. Its average frame duration also fell from 44.5898089408284 ms to 40.7364576136986 ms.

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
    SELECT * FROM window_frames WHERE upid IN (SELECT upid FROM app)
  )
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count,
  min(a.dur)/1e6 AS min_frame_ms, max(a.dur)/1e6 AS max_frame_ms,
  avg(a.dur)/1e6 AS avg_frame_ms
FROM frames f
JOIN process p ON p.upid=f.upid
JOIN thread t ON t.utid=f.ui_thread_utid
JOIN actual_frame_timeline_slice a ON a.id=f.id
GROUP BY p.name,t.name
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
    SELECT * FROM window_frames WHERE upid IN (SELECT upid FROM app)
  )
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count,
  min(a.dur)/1e6 AS min_frame_ms, max(a.dur)/1e6 AS max_frame_ms,
  avg(a.dur)/1e6 AS avg_frame_ms
FROM frames f
JOIN process p ON p.upid=f.upid
JOIN thread t ON t.utid=f.ui_thread_utid
JOIN actual_frame_timeline_slice a ON a.id=f.id
GROUP BY p.name,t.name
```

### c3. A secondary metric, synchronous binder wait on the app UI thread, increased from 214.334244 ms to 227.248289 ms. All of these waits were attributed to /system/bin/surfaceflinger, with 336 transactions in the baseline and 352 in the current trace.

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
    SELECT * FROM window_frames WHERE upid IN (SELECT upid FROM app)
  )
SELECT server_process, method_name, aidl_name,
  count(*) AS txn_count,
  sum(client_dur) / 1e6 AS wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0
  AND client_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY server_process, method_name, aidl_name
ORDER BY wait_ms DESC
LIMIT 20
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
    SELECT * FROM window_frames WHERE upid IN (SELECT upid FROM app)
  )
SELECT server_process, method_name, aidl_name,
  count(*) AS txn_count,
  sum(client_dur) / 1e6 AS wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0
  AND client_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY server_process, method_name, aidl_name
ORDER BY wait_ms DESC
LIMIT 20
```

### c4. The range contains runtime-facing changes to MoQ position logging, TV control timeout behavior, and Downloads row layout; blame assigns those lines to 6ef4e8aa95bcd45752e1fd3e907d8febdc5cb921, 82cde0d4acda1b40a0044ed8a118b168410d3aee, and 2cd54b6fd57035346e6095e8daf08afce3a1c475 respectively.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
6ef4e8aa95bcd45752e1fd3e907d8febdc5cb921
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
82cde0d4acda1b40a0044ed8a118b168410d3aee
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
2cd54b6fd57035346e6095e8daf08afce3a1c475
```

### c5. No culprit is assigned because the primary frame metric improved, while the trace evidence localizes the secondary binder change to SurfaceFlinger transactions rather than to a changed application method.

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
    SELECT * FROM window_frames WHERE upid IN (SELECT upid FROM app)
  )
SELECT server_process, method_name, aidl_name,
  count(*) AS txn_count,
  sum(client_dur) / 1e6 AS wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0
  AND client_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY server_process, method_name, aidl_name
ORDER BY wait_ms DESC
LIMIT 20
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
    SELECT * FROM window_frames WHERE upid IN (SELECT upid FROM app)
  )
SELECT server_process, method_name, aidl_name,
  count(*) AS txn_count,
  sum(client_dur) / 1e6 AS wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0
  AND client_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY server_process, method_name, aidl_name
ORDER BY wait_ms DESC
LIMIT 20
```

## Caveats

- The frame percentile is based on one capture per side; this supports the no-regression conclusion for this run but is not a repeated-build variance estimate.
- Startup, heap-graph, and native-heapprofd metrics had no data in these traces.

## Dropped claims

### c6. The current trace metadata describes a benchmark build on an sdk_gphone64_arm64 emulator, and only one capture is available for each side, so small secondary deltas may be run-to-run noise.

Dropped: the claim cites nothing

## Run

`gpt-5.6-luna` on openai, effort high: 40 tool calls, $0.0199, 164 s.
Tokens: 24 input, 76,899 cache read, 24,393 cache write, 10,187 output.
