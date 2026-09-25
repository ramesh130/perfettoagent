# Regression

- **Metric:** `startup_ttfd_ms` +646.68 ms (2,077.31 → 2,723.99 ms)
- **Culprit:** `fb30a9c67862` (correlated); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 3 claims kept, 0 dropped; 6 of 6 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttfd_ms` | ms | 2,077.31 | 2,723.99 | +646.68 |

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

### c1. Median cold-start time to full display increased from 2077.310959 ms in the baseline to 2723.988335 ms in the current trace, a delta of 646.677376 ms.

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

The `current` trace: 1 row.

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

### c2. The current trace's cold starts show substantially longer startup activity, including more time in bindApplication and launching the demo activity than the baseline.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH s AS (SELECT ts, ts_end FROM android_startups WHERE startup_type='cold') SELECT sl.name, count(*) AS n, sum(sl.dur)/1e6 AS dur_ms FROM slice sl JOIN s ON sl.ts < s.ts_end AND sl.ts+sl.dur > s.ts WHERE sl.dur>0 GROUP BY sl.name ORDER BY dur_ms DESC LIMIT 20;
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH s AS (SELECT ts, ts_end FROM android_startups WHERE startup_type='cold') SELECT sl.name, count(*) AS n, sum(sl.dur)/1e6 AS dur_ms FROM slice sl JOIN s ON sl.ts < s.ts_end AND sl.ts+sl.dur > s.ts WHERE sl.dur>0 GROUP BY sl.name ORDER BY dur_ms DESC LIMIT 20;
```

### c3. The range's final commit adds DemoApplication as the application class and performs catalog-cache validation, possible 192 MiB cache rebuilding, and a CRC32 scan during Application.onCreate, making it the most likely cause of the startup regression.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- This conclusion is based on one baseline capture and one current capture, so run-to-run noise cannot be fully excluded.
- The captures were made on an Android emulator (sdk_gphone64_arm64, SDK 36).
- The trace evidence localizes the regression to startup work but does not contain a direct source-level stack attribution to DemoApplication; the commit attribution is therefore correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort low: 18 tool calls, $0.0071, 112 s.
Tokens: 18 input, 34,966 cache read, 14,333 cache write, 2,360 output.
