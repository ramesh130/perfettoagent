# No regression

- **Metric:** `frame_p95_ms` -0.47 ms (59.13 → 58.65 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 7 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 59.13 | 58.65 | -0.47 |

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

### c2. The UI thread was the same app thread in the inspected frame rows, and the slowest current frames were dominated by Choreographer/draw and buffer-queue-related timing rather than a uniquely identified application method.

The `current` trace: 60 rows.

```sql
SELECT s.name, s.ts/1e6 AS start_ms, s.dur/1e6 AS dur_ms, s.depth FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid=365 AND s.ts < 5255104.658922*1000000 + 82.930375*1000000 AND s.ts+s.dur > 5255104.658922*1000000 ORDER BY s.depth, s.ts LIMIT 100;
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, t.utid FROM thread t JOIN process p ON t.upid=p.upid WHERE t.utid=365;
```

### c3. The current trace has a higher isolated p99 tail, but its largest frame is marked with Prediction Error, App Deadline Missed, and Buffer Stuffing; the baseline also has top frames with the same display-pipeline markers.

The `current` trace: 15 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT ts / 1e6 AS start_ms, dur / 1e6 AS frame_ms, jank_type, upid, ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app) ORDER BY dur DESC LIMIT 15;
```

The `baseline` trace: 15 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT ts / 1e6 AS start_ms, dur / 1e6 AS frame_ms, jank_type, upid, ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app) ORDER BY dur DESC LIMIT 15;
```

### c4. No commit in the supplied range can be directly attributed to a regression: the only range change identified as rendering-related changes the Interests screen thumbnail layout, while the trace evidence does not identify that code as the source of the slow frames.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

The `current` trace: 60 rows.

```sql
SELECT s.name, s.ts/1e6 AS start_ms, s.dur/1e6 AS dur_ms, s.depth FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid=365 AND s.ts < 5255104.658922*1000000 + 82.930375*1000000 AND s.ts+s.dur > 5255104.658922*1000000 ORDER BY s.depth, s.ts LIMIT 100;
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This comparison uses one capture per side, so the isolated p99 increase may be run-to-run emulator or display-pipeline variability.
- The current capture is a debuggable build on an Android emulator (sdk_gphone64_arm64, SDK 36).
- Startup metrics were unavailable because both traces lacked the required startup timing data.

## Dropped claims

### c1. The primary frame-duration metric did not regress: frame p95 decreased from baseline to current.

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

`gpt-5.6-luna` on openai, effort medium: 27 tool calls, $0.0115, 75 s.
Tokens: 24 input, 77,373 cache read, 17,658 cache write, 4,577 output.
