# No regression

- **Metric:** `frame_ui_time_p95_ms` -9.8 ms (65.8 → 56 ms)
- **Culprit:** none attributed
- **Verified:** 2 claims kept, 1 dropped; 4 of 5 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 65.8 | 56 | -9.8 |

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

### c2. The localized frame work is in the com.superplayer.demo process's UI thread: the baseline contains 492 doFrame slices and the current trace contains 496.

The `baseline` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS do_frame_count, sum(s.dur) / 1e6 AS do_frame_ms, max(s.dur) / 1e6 AS max_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p ON p.upid = t.upid
GROUP BY p.name, t.name
ORDER BY do_frame_ms DESC
```

The `current` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS do_frame_count, sum(s.dur) / 1e6 AS do_frame_ms, max(s.dur) / 1e6 AS max_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p ON p.upid = t.upid
GROUP BY p.name, t.name
ORDER BY do_frame_ms DESC
```

### c3. The range's head commit changes FeedScreen.kt, but the trace evidence does not identify any commit in the range as the cause of a performance regression.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
d06e018fc738bebf0f5ccf2814efba445a6cfdfe
```

## Caveats

- Only one capture is available for each side, so the improvement may partly reflect run-to-run variability.
- The traces were captured on an emulator; the current run metadata identifies sdk_gphone64_arm64 on SDK 36.

## Dropped claims

### c1. The app's UI-time p95 improved from 65.80025 ms in the baseline to 56.004625 ms in the current trace, a delta of -9.795625 ms rather than a regression.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort medium: 19 tool calls, $0.0089, 160 s.
Tokens: 21 input, 47,711 cache read, 13,279 cache write, 3,839 output.
