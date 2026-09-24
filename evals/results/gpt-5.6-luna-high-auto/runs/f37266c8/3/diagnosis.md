# No regression

- **Metric:** `frame_p95_ms` -3.29 ms (76.54 → 73.26 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. The selected user-visible frame metric improved: frame p95 decreased from 76.544292 ms in baseline to 73.255125 ms in current, a delta of -3.289167 ms.

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

### c2. Both captures select com.superplayer.demo as the app with the most window frames; the selected UI thread is uperplayer.demo, with 746 baseline frames and 834 current frames.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
 SELECT upid, count(*) AS frame_count FROM window_frames GROUP BY upid ORDER BY frame_count DESC, upid LIMIT 1
)
SELECT a.upid, a.frame_count, p.name AS process_name, t.utid AS ui_thread_utid, t.name AS thread_name
FROM app a JOIN process p ON p.upid=a.upid JOIN thread t ON t.utid=(SELECT ui_thread_utid FROM window_frames WHERE upid=a.upid LIMIT 1)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
 SELECT upid, count(*) AS frame_count FROM window_frames GROUP BY upid ORDER BY frame_count DESC, upid LIMIT 1
)
SELECT a.upid, a.frame_count, p.name AS process_name, t.utid AS ui_thread_utid, t.name AS thread_name
FROM app a JOIN process p ON p.upid=a.upid JOIN thread t ON t.utid=(SELECT ui_thread_utid FROM window_frames WHERE upid=a.upid LIMIT 1)
```

### c3. A secondary aggregate moved upward: synchronous UI-thread binder wait to /system/bin/surfaceflinger was 287.81833 ms across 371 transactions in baseline and 348.319381 ms across 400 transactions in current. This does not correspond to a worse frame p95.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid, ui_thread_utid FROM window_frames GROUP BY upid, ui_thread_utid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT server_process, interface, method_name, aidl_name, count(*) AS txn_count, sum(client_dur)/1e6 AS total_wait_ms, max(client_dur)/1e6 AS max_wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0 AND client_utid=(SELECT ui_thread_utid FROM app)
GROUP BY server_process, interface, method_name, aidl_name
ORDER BY total_wait_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid, ui_thread_utid FROM window_frames GROUP BY upid, ui_thread_utid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT server_process, interface, method_name, aidl_name, count(*) AS txn_count, sum(client_dur)/1e6 AS total_wait_ms, max(client_dur)/1e6 AS max_wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0 AND client_utid=(SELECT ui_thread_utid FROM app)
GROUP BY server_process, interface, method_name, aidl_name
ORDER BY total_wait_ms DESC
```

### c4. The range contains FeedScreen changes, including the player-acquisition change in 328304f8f1081e484f20030bb6518b1b1ee03c82 and the final FeedScreen change in f871266864fac1b4f44ff750e6a2fc5d5b07d4a1; the trace evidence does not support attributing a frame-performance regression to either.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
328304f8f1081e484f20030bb6518b1b1ee03c82
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
f871266864fac1b4f44ff750e6a2fc5d5b07d4a1
```

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

- There is only one capture per side, so the binder-wait increase and the modest frame-p95 improvement may include run-to-run noise.
- The traces do not contain startup, heap-graph, native-heapprofd, or Java stack-sampling data, so those dimensions could not be used for attribution.

## Run

`gpt-5.6-luna` on openai, effort high: 61 tool calls, $0.0379, 240 s.
Tokens: 48 input, 426,718 cache read, 47,648 cache write, 14,541 output.
