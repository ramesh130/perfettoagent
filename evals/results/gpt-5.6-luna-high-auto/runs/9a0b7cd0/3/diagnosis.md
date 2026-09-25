# Inconclusive

- **Metric:** `frame_p95_ms` +0.5 ms (58.63 → 59.13 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 1 dropped; 8 of 9 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 58.63 | 59.13 | +0.5 |

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

### c2. The measured frames came from com.example.jetnews on the example.jetnews UI thread. The baseline had 2,120 frames with a 27.490378 ms mean and an 80.504541 ms maximum; the current had 2,107 frames with a 26.8752602781205 ms mean and an 81.048584 ms maximum, so the p95 movement is not accompanied by a broad increase in mean frame time.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, f.frame_id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  )
SELECT p.name AS process_name, t.name AS ui_thread, count(*) AS frame_count,
       sum(w.dur) / 1e6 AS total_frame_ms,
       avg(w.dur) / 1e6 AS mean_frame_ms,
       max(w.dur) / 1e6 AS max_frame_ms
FROM window_frames AS w
JOIN process AS p ON p.upid = w.upid
JOIN thread AS t ON t.utid = w.ui_thread_utid
GROUP BY p.name, t.name
ORDER BY frame_count DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, f.frame_id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  )
SELECT p.name AS process_name, t.name AS ui_thread, count(*) AS frame_count,
       sum(w.dur) / 1e6 AS total_frame_ms,
       avg(w.dur) / 1e6 AS mean_frame_ms,
       max(w.dur) / 1e6 AS max_frame_ms
FROM window_frames AS w
JOIN process AS p ON p.upid = w.upid
JOIN thread AS t ON t.utid = w.ui_thread_utid
GROUP BY p.name, t.name
ORDER BY frame_count DESC
```

### c3. The slowest frames in both traces are Choreographer#doFrame slices carrying display-pipeline tags such as Buffer Stuffing and Prediction Error; the current trace does not isolate the change to an application method or class.

The `baseline` trace: 10 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, f.frame_id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  )
SELECT p.name AS process_name, t.name AS ui_thread, w.dur / 1e6 AS frame_ms,
       w.jank_type, s.name AS do_frame_name, s.dur / 1e6 AS ui_ms
FROM window_frames AS w
JOIN process AS p ON p.upid = w.upid
JOIN thread AS t ON t.utid = w.ui_thread_utid
JOIN android_frames_choreographer_do_frame AS d ON d.frame_id = w.frame_id
JOIN slice AS s ON s.id = d.id
WHERE p.name = 'com.example.jetnews'
ORDER BY w.dur DESC
LIMIT 10
```

The `current` trace: 10 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, f.frame_id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  )
SELECT p.name AS process_name, t.name AS ui_thread, w.dur / 1e6 AS frame_ms,
       w.jank_type, s.name AS do_frame_name, s.dur / 1e6 AS ui_ms
FROM window_frames AS w
JOIN process AS p ON p.upid = w.upid
JOIN thread AS t ON t.utid = w.ui_thread_utid
JOIN android_frames_choreographer_do_frame AS d ON d.frame_id = w.frame_id
JOIN slice AS s ON s.id = d.id
WHERE p.name = 'com.example.jetnews'
ORDER BY w.dur DESC
LIMIT 10
```

### c4. The range includes a layout change that reduced Interests-row thumbnails from 56.dp to 48.dp and changed the divider inset, introduced by commit 77a061c0c715ba071167b2104fcebb2c2be12c8d.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

### c5. The range also includes commit 75ac1f34f73c512b2314e138de1cf6f8b8faa012, which changes the widget update-period resource; the trace evidence does not connect that resource change to the measured frame tail.

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
```

The `current` trace: 10 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, f.frame_id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  )
SELECT p.name AS process_name, t.name AS ui_thread, w.dur / 1e6 AS frame_ms,
       w.jank_type, s.name AS do_frame_name, s.dur / 1e6 AS ui_ms
FROM window_frames AS w
JOIN process AS p ON p.upid = w.upid
JOIN thread AS t ON t.utid = w.ui_thread_utid
JOIN android_frames_choreographer_do_frame AS d ON d.frame_id = w.frame_id
JOIN slice AS s ON s.id = d.id
WHERE p.name = 'com.example.jetnews'
ORDER BY w.dur DESC
LIMIT 10
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so a 0.500583 ms p95 shift is insufficient to distinguish a regression from run-to-run variability.
- The evidence does not provide a direct stack or source-method attribution for the changed frame tail.

## Dropped claims

### c1. The app frame p95 increased from 58.626583 ms in the baseline to 59.127166 ms in the current trace, a 0.500583 ms delta.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 23 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 23 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT upid FROM window_frames GROUP BY count(*) ORDER BY count(*) DESC, upid LIMIT 1
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

`gpt-5.6-luna` on openai, effort high: 72 tool calls, $0.0298, 183 s.
Tokens: 45 input, 254,106 cache read, 31,610 cache write, 13,987 output.
