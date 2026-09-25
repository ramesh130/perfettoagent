# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 3 claims kept, 1 dropped; 7 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.3 | 103.76 | +77.46 |

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

### c2. The regression is concentrated in the app's UI process: the current trace has 762 deadline-missed frames out of 1823, versus 271 out of 2138 in the baseline; its maximum frame is also longer.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name, (SELECT t.name FROM thread t WHERE t.utid=(SELECT ui_thread_utid FROM frames LIMIT 1)) AS thread_name, count(*) AS frame_count, sum(jank_type GLOB '*App Deadline Missed*') AS jank_count, max(dur)/1e6 AS max_frame_ms FROM frames;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT (SELECT p.name FROM process p WHERE p.upid=(SELECT upid FROM app)) AS process_name, (SELECT t.name FROM thread t WHERE t.utid=(SELECT ui_thread_utid FROM frames LIMIT 1)) AS thread_name, count(*) AS frame_count, sum(jank_type GLOB '*App Deadline Missed*') AS jank_count, max(dur)/1e6 AS max_frame_ms FROM frames;
```

### c3. The current UI trace shows substantially more layout and text-measurement work: AndroidOwner:measureAndLayout totals 39896.66464 ms and TextLayout:initLayout totals 14372.316042 ms, compared with 964.653869 ms and no listed TextLayout:initLayout row in the baseline query.

The `baseline` trace: 15 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name GLOB '*Text*' OR name GLOB '*measure*' OR name GLOB '*compose*' GROUP BY name ORDER BY total_ms DESC LIMIT 15;
```

The `current` trace: 15 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name GLOB '*Text*' OR name GLOB '*measure*' OR name GLOB '*compose*' GROUP BY name ORDER BY total_ms DESC LIMIT 15;
```

### c4. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 adds repeated text measurement in PostTitle and an infinite row animation that changes row padding in PostCards.kt; those changes correlate with the current trace's increased text/layout and recomposition work.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `current` trace: 15 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name GLOB '*Text*' OR name GLOB '*measure*' OR name GLOB '*compose*' GROUP BY name ORDER BY total_ms DESC LIMIT 15;
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side, so run-to-run variability cannot be ruled out.
- The current run metadata identifies a debuggable debug build on the sdk_gphone64_arm64 emulator.
- No usable stack-profile frames were recorded, so attribution is correlated with the localized trace work rather than a direct symbolized callstack match.

## Dropped claims

### c1. The app UI-thread p95 frame time increased from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a delta of 77.462416 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

## Run

`gpt-5.6-luna` on openai, effort medium: 34 tool calls, $0.0147, 246 s.
Tokens: 27 input, 97,723 cache read, 26,254 cache write, 5,115 output.
