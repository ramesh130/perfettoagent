# Inconclusive

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 5 of 6 citations passed
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

### c2. Both traces contain 20 cold starts for com.superplayer.demo, but the individual TTFD values vary substantially, so one capture per side does not establish that the observed median shift exceeds run-to-run noise.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.ts
```

### c3. The range contains a change that doubles MoQ position-log frequency from every two seconds to every one second; the changed source line is attributed to commit 2fa1b7e9db091ea90dc7775f5c7c20cec0ca5279.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
2fa1b7e9db091ea90dc7775f5c7c20cec0ca5279
```

### c4. The trace evidence does not directly connect that logging change, or another commit in the range, to the TTFD increase, so no culprit is attributed.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
2fa1b7e9db091ea90dc7775f5c7c20cec0ca5279
```

## Caveats

- Each side has only one capture, making the TTFD comparison susceptible to run-to-run noise.
- The captures were made on an Android emulator (sdk_gphone64_arm64, SDK 36) using a benchmark build.
- The current trace metadata identifies commit 3c45fa773a148f0cd3f45cdf56318eb3dc52e6c0 and a clean tree; baseline build metadata was not available.

## Dropped claims

### c1. Median cold-start time to full display increased from 2077.310959 ms in the baseline to 2282.739626 ms in the current trace, a delta of 205.428667 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 21 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: 1 row.

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 21 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

## Run

`gpt-5.6-luna` on openai, effort medium: 39 tool calls, $0.0149, 226 s.
Tokens: 30 input, 110,952 cache read, 24,750 cache write, 5,446 output.
