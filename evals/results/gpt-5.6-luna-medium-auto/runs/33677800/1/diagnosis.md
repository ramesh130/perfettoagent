# Inconclusive

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 2 claims kept, 1 dropped; 3 of 5 citations passed
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

### c2. Each trace contains 20 cold starts with TTID data. The baseline TTID range was 801.601458–1006.860583 ms, while the current range was 818.441458–895.549625 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT count(*) AS cold_starts, count(d.time_to_initial_display) AS with_ttid, min(d.time_to_initial_display)/1e6 AS min_ttid_ms, max(d.time_to_initial_display)/1e6 AS max_ttid_ms FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id) WHERE s.package='com.example.jetnews' AND s.startup_type='cold';
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT count(*) AS cold_starts, count(d.time_to_initial_display) AS with_ttid, min(d.time_to_initial_display)/1e6 AS min_ttid_ms, max(d.time_to_initial_display)/1e6 AS max_ttid_ms FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id) WHERE s.package='com.example.jetnews' AND s.startup_type='cold';
```

### c3. The range contains a UI thumbnail-size change in InterestsScreen, but the trace evidence does not directly connect that change to the startup-TTID difference.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one baseline and one current capture are available, so the 15.346750000000043 ms shift may be run-to-run noise.
- The current trace was captured on an Android emulator (sdk_gphone64_arm64, SDK 36) using a debuggable debug build.
- No commit is attributed because no trace-localized startup code maps directly to a changed commit in the supplied range.

## Dropped claims

### c1. Median cold-start time to initial display increased from 839.504417 ms in the baseline trace to 854.851167 ms in the current trace, a delta of 15.346750000000043 ms.

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort medium: 35 tool calls, $0.0120, 186 s.
Tokens: 27 input, 84,641 cache read, 17,882 cache write, 4,845 output.
