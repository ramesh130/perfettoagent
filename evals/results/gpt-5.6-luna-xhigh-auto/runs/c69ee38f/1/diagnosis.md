# No regression

- **Metric:** `startup_ttid_ms` -39.14 ms (425.9 → 386.76 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 8 of 10 citations passed
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

### c1. The app-specific scenario has 20 cold starts of com.superplayer.demo in each trace, so startup_ttid_ms is the relevant selected metric.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type,
       d.time_to_initial_display / 1e6 AS tt_id_ms,
       d.time_to_full_display / 1e6 AS tt_fd_ms
FROM android_startups s
JOIN android_startup_time_to_display d USING (startup_id)
WHERE s.package = 'com.superplayer.demo' AND s.startup_type = 'cold'
ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type,
       d.time_to_initial_display / 1e6 AS tt_id_ms,
       d.time_to_full_display / 1e6 AS tt_fd_ms
FROM android_startups s
JOIN android_startup_time_to_display d USING (startup_id)
WHERE s.package = 'com.superplayer.demo' AND s.startup_type = 'cold'
ORDER BY s.ts
```

### c3. As a trace-level cross-check, com.superplayer.demo frame p95 also improved from 274.668751 ms to 264.937 ms, while app-deadline jank was nearly unchanged at 60.4651162790698% versus 60.2941176470588%.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH frames AS (
  SELECT DISTINCT f.upid, a.id, a.dur, a.jank_type
  FROM android_frames_layers f
  JOIN actual_frame_timeline_slice a ON a.id = f.actual_frame_timeline_id
  JOIN process p ON p.upid = f.upid
  WHERE p.name = 'com.superplayer.demo'
    AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), ranked AS (
  SELECT dur, jank_type, row_number() OVER (ORDER BY dur) AS r, count(*) OVER () AS n
  FROM frames
)
SELECT count(*) AS frame_count,
       avg(dur)/1e6 AS avg_ms,
       (SELECT dur/1e6 FROM ranked WHERE r = (n*50+99)/100) AS p50_ms,
       (SELECT dur/1e6 FROM ranked WHERE r = (n*95+99)/100) AS p95_ms,
       (SELECT dur/1e6 FROM ranked WHERE r = (n*99+99)/100) AS p99_ms,
       100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS app_jank_pct
FROM frames
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH frames AS (
  SELECT DISTINCT f.upid, a.id, a.dur, a.jank_type
  FROM android_frames_layers f
  JOIN actual_frame_timeline_slice a ON a.id = f.actual_frame_timeline_id
  JOIN process p ON p.upid = f.upid
  WHERE p.name = 'com.superplayer.demo'
    AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), ranked AS (
  SELECT dur, jank_type, row_number() OVER (ORDER BY dur) AS r, count(*) OVER () AS n
  FROM frames
)
SELECT count(*) AS frame_count,
       avg(dur)/1e6 AS avg_ms,
       (SELECT dur/1e6 FROM ranked WHERE r = (n*50+99)/100) AS p50_ms,
       (SELECT dur/1e6 FROM ranked WHERE r = (n*95+99)/100) AS p95_ms,
       (SELECT dur/1e6 FROM ranked WHERE r = (n*99+99)/100) AS p99_ms,
       100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS app_jank_pct
FROM frames
```

### c4. The in-range source changes inspected are associated with MoQ logging, launch-state naming, the feed handler name, and download-row padding; the trace shows no direct evidence tying any of these commits to a startup regression, so no culprit is assigned.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
c48c1214737c4fc1f3983993d9812f958485b4d1
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MainActivity.kt`:

```text
e07b69dee9c0b34782c957f5a58b909b3a45e488
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
d06e018fc738bebf0f5ccf2814efba445a6cfdfe
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
53c9f8712216924f1fe829a44e7db1f13caeb3c3
```

## Caveats

- This compares one baseline/current capture pair, so the measured improvement is not a causal proof and run-to-run noise cannot be estimated.
- The captures run on an emulator; results may differ on physical devices.

## Dropped claims

### c2. The median time to initial display improved from 425.901458 ms to 386.763334 ms, a delta of -39.138124 ms; this metric did not regress.

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

`gpt-5.6-luna` on openai, effort xhigh: 74 tool calls, $0.0469, 387 s.
Tokens: 45 input, 395,304 cache read, 64,706 cache write, 18,988 output.
