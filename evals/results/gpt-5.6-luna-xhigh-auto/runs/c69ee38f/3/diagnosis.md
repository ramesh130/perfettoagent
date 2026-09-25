# No regression

- **Metric:** `startup_ttid_ms` -39.14 ms (425.9 → 386.76 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 5 of 7 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 425.9 | 386.76 | -39.14 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Claims

### c2. The startup measurement is for com.superplayer.demo: each trace contains 20 cold starts, and all 20 have both initial-display and full-display timings.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.package, s.startup_type, count(*) AS starts,
       sum(d.time_to_initial_display IS NOT NULL) AS with_ttid,
       sum(d.time_to_full_display IS NOT NULL) AS with_ttfd,
       min(d.time_to_initial_display) / 1e6 AS min_ttid_ms,
       max(d.time_to_initial_display) / 1e6 AS max_ttid_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
GROUP BY s.package, s.startup_type
ORDER BY starts DESC, s.package;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.package, s.startup_type, count(*) AS starts,
       sum(d.time_to_initial_display IS NOT NULL) AS with_ttid,
       sum(d.time_to_full_display IS NOT NULL) AS with_ttfd,
       min(d.time_to_initial_display) / 1e6 AS min_ttid_ms,
       max(d.time_to_initial_display) / 1e6 AS max_ttid_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
GROUP BY s.package, s.startup_type
ORDER BY starts DESC, s.package;
```

### c3. The frame data contains substantially more window frames for the launcher than for com.superplayer.demo, so frame-oriented canned metrics are not reliable evidence of a target-app regression in this capture.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT p.pid) AS process_instances,
       count(DISTINCT a.id) AS window_frames,
       min(a.ts) / 1e9 AS first_frame_s,
       max(a.ts + a.dur) / 1e9 AS last_frame_s
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.name
ORDER BY window_frames DESC
LIMIT 20;
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, count(DISTINCT p.pid) AS process_instances,
       count(DISTINCT a.id) AS window_frames,
       min(a.ts) / 1e9 AS first_frame_s,
       max(a.ts + a.dur) / 1e9 AS last_frame_s
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.name
ORDER BY window_frames DESC
LIMIT 20;
```

### c4. The range head includes d06e018fc738bebf0f5ccf2814efba445a6cfdfe, a FeedScreen.kt change titled “Rename the feed's main-thread handler”; no trace evidence points to that rename, or to another commit in the range, as a cause of a startup regression.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
d06e018fc738bebf0f5ccf2814efba445a6cfdfe
```

## Caveats

- This compares one capture per side, so run-to-run noise remains; each capture nevertheless contains 20 cold starts for the selected startup metric.
- The current capture is from an emulator benchmark build, and the frame-oriented process selection is dominated by launcher activity rather than the target app.

## Dropped claims

### c1. Cold-start time to initial display improved from 425.901458 ms in the baseline to 386.763334 ms in the current trace, a delta of -39.138124 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 42 tool calls, $0.0267, 327 s.
Tokens: 30 input, 144,241 cache read, 30,808 cache write, 13,450 output.
