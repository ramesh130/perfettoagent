# Regression

- **Metric:** `frame_ui_time_p95_ms` +22.31 ms (37.95 → 60.26 ms)
- **Culprit:** `9d89ce1ec350` (correlated); `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 37.95 | 60.26 | +22.31 |

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c1. The app UI thread's p95 frame time increased from 37.952167 ms to 60.2595 ms, a 22.307333 ms increase.

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

### c2. The trace shows substantially more expensive UI drawing work in the current capture: total 'traversal' time rose from 6841.511081 ms across 574 slices to 8247.222121 ms across 375 slices, and 'Record View#draw()' rose from 618.119505 ms across 147 slices to 7115.910336 ms across 310 slices.

The `baseline` trace: 30 rows.

```sql
SELECT s.name, COUNT(*) AS n, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice s WHERE s.dur > 1000000 GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

```sql
SELECT s.name, COUNT(*) AS n, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice s WHERE s.dur > 1000000 GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

### c3. The range's head commit increases each download row's vertical padding from 8.dp to 12.dp in DownloadsScreen.kt.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
9d89ce1ec3503aadda240ce37feb754b809eeb38
```

### c4. The changed padding line is directly attributed by blame to commit 9d89ce1ec3503aadda240ce37feb754b809eeb38.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
9d89ce1ec3503aadda240ce37feb754b809eeb38
```

## Caveats

- Each side has only one capture, so run-to-run variability cannot be separated from the measured change.
- The capture ran on an Android emulator (sdk_gphone64_arm64, SDK 36), which may not represent physical-device performance.
- The trace evidence localizes the increase to UI drawing/traversal but does not uniquely identify DownloadsScreen as the executed screen; therefore the culprit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort low: 13 tool calls, $0.0051, 45 s.
Tokens: 15 input, 24,949 cache read, 7,300 cache write, 2,314 output.
