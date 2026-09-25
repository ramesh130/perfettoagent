# Inconclusive

- **Metric:** `frame_p95_ms` +5.44 ms (67.81 → 73.25 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. The selected UI-frame p95 increased from 67.812916 ms in baseline to 73.252833 ms in current, a delta of 5.439916999999994 ms.

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

### c2. The frame-owning process is com.superplayer.demo. Baseline recorded 824 frames averaging 38.3614831796117 ms; current recorded 760 frames averaging 42.2412068131579 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count, avg(a.dur) / 1e6 AS avg_frame_ms, max(a.dur) / 1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, f.ui_thread_utid, p.name, t.name
ORDER BY frame_count DESC
LIMIT 1
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count, avg(a.dur) / 1e6 AS avg_frame_ms, max(a.dur) / 1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, f.ui_thread_utid, p.name, t.name
ORDER BY frame_count DESC
LIMIT 1
```

### c3. The localized non-frame UI work is Compose lazy-list prefetching: baseline had 57 compose slices totaling 270.720838 ms and 8 idle-frame slices totaling 91.049293 ms; current had 61 totaling 304.11613 ms and 9 totaling 126.968208 ms.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid, ui_thread_utid
    FROM window_frames
    GROUP BY upid, ui_thread_utid
    ORDER BY count(*) DESC, upid
    LIMIT 1
  )
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = (SELECT ui_thread_utid FROM app)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame', 'animation', 'Recomposer:recompose', 'Compose:onForgotten')
GROUP BY s.name
ORDER BY total_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid, ui_thread_utid
    FROM window_frames
    GROUP BY upid, ui_thread_utid
    ORDER BY count(*) DESC, upid
    LIMIT 1
  )
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = (SELECT ui_thread_utid FROM app)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame', 'animation', 'Recomposer:recompose', 'Compose:onForgotten')
GROUP BY s.name
ORDER BY total_ms DESC
```

### c4. Commit 7fd3626107135436b97973da12915e1e13f76255 is the range commit that changes the FeedScreen player-acquisition code, but the trace contains no row naming that changed method or establishing causality. The evidence therefore does not support attributing the higher p95 to it.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid, ui_thread_utid
    FROM window_frames
    GROUP BY upid, ui_thread_utid
    ORDER BY count(*) DESC, upid
    LIMIT 1
  )
SELECT s.name, count(*) AS slice_count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = (SELECT ui_thread_utid FROM app)
  AND s.depth = 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:idle_frame', 'animation', 'Recomposer:recompose', 'Compose:onForgotten')
GROUP BY s.name
ORDER BY total_ms DESC
```

### c5. Synchronous binder wait on the app's UI thread increased from 282.071238 ms to 304.372374 ms, and both totals are entirely transactions to /system/bin/surfaceflinger, which is consistent with capture or display-pipeline variability rather than identifying an app method.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
SELECT client_process, client_thread, server_process, aidl_name, count(*) AS txn_count, sum(client_dur) / 1e6 AS wait_ms, max(client_dur) / 1e6 AS max_wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0 AND client_utid = 368
GROUP BY client_process, client_thread, server_process, aidl_name
ORDER BY wait_ms DESC
LIMIT 20
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
SELECT client_process, client_thread, server_process, aidl_name, count(*) AS txn_count, sum(client_dur) / 1e6 AS wait_ms, max(client_dur) / 1e6 AS max_wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0 AND client_utid = 362
GROUP BY client_process, client_thread, server_process, aidl_name
ORDER BY wait_ms DESC
LIMIT 20
```

## Caveats

- Only one capture is available for each side, so the p95 difference may be run-to-run noise.
- The recorded current run used an sdk_gphone64_arm64 Android 36 emulator and a non-debuggable benchmark build; baseline build metadata was not available.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 72 tool calls, $0.0615, 267 s.
Tokens: 63 input, 942,810 cache read, 74,967 cache write, 19,925 output.
