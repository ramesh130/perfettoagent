# Inconclusive

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 1 claim kept, 2 dropped; 4 of 7 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttfd_ms` | ms | 2,077.31 | 2,282.74 | +205.43 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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

### c2. The difference is localized to top-level UI-thread Choreographer#doFrame work during the cold-start windows: the baseline accumulated 7776.390047 ms across 225 slices, versus 9993.339093 ms across 225 current slices.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.ts, d.time_to_full_display AS ttfd
  FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
  WHERE s.startup_type='cold' AND s.package='com.superplayer.demo'
), app_slices AS (
  SELECT sl.name, sl.ts, sl.dur
  FROM slice sl JOIN thread_track tt ON tt.id=sl.track_id JOIN thread t USING(utid) JOIN process p USING(upid)
  WHERE p.name='com.superplayer.demo' AND t.tid=p.pid AND sl.depth=0
), matched AS (
  SELECT a.name, a.dur FROM app_slices a JOIN cold c ON a.ts >= c.ts AND a.ts < c.ts + c.ttfd
)
SELECT count(*) AS doframe_slices, sum(dur)/1e6 AS doframe_total_ms, max(dur)/1e6 AS doframe_max_ms
FROM matched WHERE name GLOB 'Choreographer#doFrame*'
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.ts, d.time_to_full_display AS ttfd
  FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
  WHERE s.startup_type='cold' AND s.package='com.superplayer.demo'
), app_slices AS (
  SELECT sl.name, sl.ts, sl.dur
  FROM slice sl JOIN thread_track tt ON tt.id=sl.track_id JOIN thread t USING(utid) JOIN process p USING(upid)
  WHERE p.name='com.superplayer.demo' AND t.tid=p.pid AND sl.depth=0
), matched AS (
  SELECT a.name, a.dur FROM app_slices a JOIN cold c ON a.ts >= c.ts AND a.ts < c.ts + c.ttfd
)
SELECT count(*) AS doframe_slices, sum(dur)/1e6 AS doframe_total_ms, max(dur)/1e6 AS doframe_max_ms
FROM matched WHERE name GLOB 'Choreographer#doFrame*'
```

## Caveats

- This is a single capture per side, although each trace contains 20 cold starts; the individual startup times are variable, so the measured TTFD increase is not sufficient to attribute a regression confidently.
- The captures were taken on an emulator (sdk_gphone64_arm64, SDK 36), and the current run is a non-debuggable benchmark build.
- No trace stack or slice row directly names a method changed by a commit in the supplied range, so the culprit remains unassigned.

## Dropped claims

### c1. Median cold-start time to full display increased from 2077.310959 ms in the baseline to 2282.739626 ms in the current trace, a delta of 205.428667 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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
    SELECT s.package, d.time_to_full_display AS ns
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

### c3. The range contains an app-side MoQ logging-interval change and a DownloadsScreen layout-padding change, but the trace evidence only localizes the extra work to generic UI frames and does not directly identify either changed method.

Dropped: citation 2: d3c08a36dc94946972e19ee8d78aa3a4d9d65e28 names no commit in the repo (or is ambiguous)

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
2fa1b7e9db091ea90dc7775f5c7c20cec0ca5279
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`: Failed: d3c08a36dc94946972e19ee8d78aa3a4d9d65e28 names no commit in the repo (or is ambiguous)

```text
d3c08a36dc94946972e19ee8d78aa3a4d9d65e28
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.ts, d.time_to_full_display AS ttfd
  FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
  WHERE s.startup_type='cold' AND s.package='com.superplayer.demo'
), app_slices AS (
  SELECT sl.name, sl.ts, sl.dur
  FROM slice sl JOIN thread_track tt ON tt.id=sl.track_id JOIN thread t USING(utid) JOIN process p USING(upid)
  WHERE p.name='com.superplayer.demo' AND t.tid=p.pid AND sl.depth=0
), matched AS (
  SELECT a.name, a.dur FROM app_slices a JOIN cold c ON a.ts >= c.ts AND a.ts < c.ts + c.ttfd
)
SELECT count(*) AS doframe_slices, sum(dur)/1e6 AS doframe_total_ms, max(dur)/1e6 AS doframe_max_ms
FROM matched WHERE name GLOB 'Choreographer#doFrame*'
```

## Run

`gpt-5.6-luna` on openai, effort high: 58 tool calls, $0.0547, 343 s.
Tokens: 60 input, 1,000,236 cache read, 83,550 cache write, 11,501 output.
