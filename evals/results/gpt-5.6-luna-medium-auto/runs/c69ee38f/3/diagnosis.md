# No regression

- **Metric:** `startup_ttid_ms` -39.14 ms (425.9 → 386.76 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 4 of 6 citations passed
- **Model's confidence:** high (never scored)

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

### c2. Both traces contain 20 cold starts of com.superplayer.demo with recorded time-to-initial-display values, so the selected metric has data on both sides.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, d.time_to_initial_display, d.time_to_full_display
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.startup_id;
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, d.time_to_initial_display, d.time_to_full_display
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.startup_id;
```

### c3. The range's tip commit only renames FeedPlayback's main-thread Handler variable and its use from mainThread to mainHandler; it does not change the Handler or posting behavior.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
d06e018fc738bebf0f5ccf2814efba445a6cfdfe
```

### c4. Another range commit changes only the PlayerPool parameter and local call from newPlayer to buildPlayer, which is also a naming-only change.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/PlayerPool.kt`:

```text
019c86afe8df459f24ca4cd8bddb24af9f8c97ae
```

## Caveats

- This compares one baseline capture with one current capture, so run-to-run variation cannot be ruled out.
- The current run is a non-debuggable benchmark build on an Android SDK 36 emulator.
- The traces show an improvement, not a regression; therefore no commit in the supplied range is attributed as a culprit.

## Dropped claims

### c1. Median cold-start time to initial display improved from 425.901458 ms in the baseline to 386.763334 ms in the current trace, a delta of -39.138124 ms.

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

`gpt-5.6-luna` on openai, effort medium: 21 tool calls, $0.0084, 128 s.
Tokens: 18 input, 45,591 cache read, 13,250 cache write, 3,466 output.
