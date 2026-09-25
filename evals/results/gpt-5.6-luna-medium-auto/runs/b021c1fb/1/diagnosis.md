# No regression

- **Metric:** `frame_p95_ms` -9.2 ms (81.5 → 72.3 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 8 of 9 citations passed
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

### c2. The trace contains more completed frames in current than baseline, and fewer App Deadline Missed frames: 308 of 730 versus 370 of 676.

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
SELECT p.name AS process_name, t.name AS ui_thread, count(*) AS frames,
  round(avg(dur)/1e6,2) AS avg_frame_ms,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames w JOIN app USING (upid)
JOIN process p USING (upid) JOIN thread t ON t.utid=w.ui_thread_utid
GROUP BY p.name,t.name;
```

The `current` trace: 1 row.

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
SELECT p.name AS process_name, t.name AS ui_thread, count(*) AS frames,
  round(avg(dur)/1e6,2) AS avg_frame_ms,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames w JOIN app USING (upid)
JOIN process p USING (upid) JOIN thread t ON t.utid=w.ui_thread_utid
GROUP BY p.name,t.name;
```

### c3. The changed frame workload is localized to com.superplayer.demo's UI thread; its Compose lazy-prefetch work shifted from 57 compose-prefetch slices totaling 363.85 ms to 20 totaling 83.32 ms, while idle-frame prefetch increased from 10 slices totaling 67.20 ms to 38 totaling 305.58 ms.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (
 SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main AS (
 SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,2) AS total_ms, round(max(s.dur)/1e6,2) AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM main) AND s.depth=0 AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 20;
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (
 SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main AS (
 SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,2) AS total_ms, round(max(s.dur)/1e6,2) AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM main) AND s.depth=0 AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 20;
```

### c4. No commit in the supplied range is attributed as the cause: the trace hotspot is generic Compose prefetch work, while the only range commit inspected that changes list-row layout changes DownloadRow padding rather than the localized prefetch implementation.

The `baseline` trace: 100 rows.

```sql
SELECT name, count(*) AS occurrences, round(sum(dur)/1e6,2) AS total_ms FROM slice WHERE name GLOB '*Feed*' OR name GLOB '*Download*' OR name GLOB '*Tv*' OR name GLOB '*Moq*' OR name GLOB '*compose*' GROUP BY name ORDER BY total_ms DESC LIMIT 100;
```

The `current` trace: 100 rows.

```sql
SELECT name, count(*) AS occurrences, round(sum(dur)/1e6,2) AS total_ms FROM slice WHERE name GLOB '*Feed*' OR name GLOB '*Download*' OR name GLOB '*Tv*' OR name GLOB '*Moq*' OR name GLOB '*compose*' GROUP BY name ORDER BY total_ms DESC LIMIT 100;
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
2cd54b6fd57035346e6095e8daf08afce3a1c475
```

## Caveats

- This conclusion is based on one capture per side, so run-to-run variation cannot be ruled out.
- The captures were made on an Android emulator (sdk_gphone64_arm64, SDK 36) using a non-debuggable benchmark build.
- The current trace metadata identifies commit 82cde0d4acda1b40a0044ed8a118b168410d3aee and reports a clean tree; baseline build metadata was not available.

## Dropped claims

### c1. The selected frame p95 metric improved from baseline to current, decreasing by about 9.20 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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

## Run

`gpt-5.6-luna` on openai, effort medium: 30 tool calls, $0.0166, 100 s.
Tokens: 24 input, 94,681 cache read, 33,196 cache write, 5,363 output.
