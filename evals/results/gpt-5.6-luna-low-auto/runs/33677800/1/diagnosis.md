# No regression

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 2 claims kept, 1 dropped; 6 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 839.5 | 854.85 | +15.35 |

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

### c2. Each trace contains 20 cold starts, and the individual startup times vary substantially, so this single-trace median difference is not sufficient to establish a real regression.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT startup_id, package, startup_type, ts, time_to_initial_display FROM android_startups JOIN android_startup_time_to_display USING (startup_id) WHERE startup_type = 'cold' ORDER BY ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT startup_id, package, startup_type, ts, time_to_initial_display FROM android_startups JOIN android_startup_time_to_display USING (startup_id) WHERE startup_type = 'cold' ORDER BY ts
```

### c3. The supplied range contains changes to JetnewsApp.kt, MainActivity.kt, widget resources, and several UI source files, but the trace evidence does not directly identify any of them as the cause of the small startup difference.

Commit, changing `app/src/main/java/com/example/jetnews/ui/JetnewsApp.kt`:

```text
bb767eec9f98c0e9493140735e2e477828fcb9b1
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/MainActivity.kt`:

```text
c2c776e1f353e8994eb20a2d1c17589fe789df9a
```

Commit, changing `app/src/main/res/values/integers.xml`:

```text
432218a1e58c49007d18fae8bd3d76fa40b57272
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/HomeScreens.kt`:

```text
46caf51e9da40b16c4eec115794d69c9ddadb5a2
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis compares one capture per build, so run-to-run startup variance cannot be separated from a 15.346750000000043 ms change.
- The captures were taken on an emulator (sdk_gphone64_arm64, SDK 36) using a debuggable debug build.

## Dropped claims

### c1. Median cold-start time to initial display increased from 839.504417 ms in the baseline to 854.851167 ms in the current trace, a delta of 15.346750000000043 ms.

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

`gpt-5.6-luna` on openai, effort low: 13 tool calls, $0.0053, 83 s.
Tokens: 15 input, 25,914 cache read, 8,104 cache write, 2,264 output.
