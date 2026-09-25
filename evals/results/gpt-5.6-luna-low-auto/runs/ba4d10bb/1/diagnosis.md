# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 5 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 839.5 | 1,596.43 | +756.93 |

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

### c1. Cold-start median TTID increased from 839.504417 ms in baseline to 1596.432376 ms in current, a 756.927959 ms increase.

The `baseline` trace: 1 row.

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

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c2. The current trace contains 20 cold-start records for com.example.jetnews, with startup durations around 1.6–2.0 seconds; the baseline records shown are around 0.8–1.0 seconds.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT * FROM android_startups LIMIT 5;
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT * FROM android_startups LIMIT 5;
```

### c3. The attributed change adds verifyArticleCache() to JetnewsApplication.onCreate(), including a 768 MiB cache check/write path and a full CRC32 read before application initialization continues.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. The current trace includes JetnewsApplication execution and CRC32-related startup activity, consistent with the new launch-time cache verification being on the startup path.

The `current` trace: 321 rows.

```sql
SELECT name, count(*) AS n, sum(dur)/1e6 AS total_ms FROM slice WHERE name GLOB '*cache*' OR name GLOB '*CRC*' OR name GLOB '*Application*' GROUP BY name ORDER BY total_ms DESC;
```

### c5. The launch-time verifyArticleCache() call and its implementation were introduced by commit bea44a9561ce48b23fc6102f729f1c78d49b2af5.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side provides a single capture, so run-to-run noise cannot be excluded completely.
- The current run metadata identifies a debuggable debug build on an Android emulator (sdk_gphone64_arm64, SDK 36).

## Run

`gpt-5.6-luna` on openai, effort low: 21 tool calls, $0.0118, 449 s.
Tokens: 24 input, 52,871 cache read, 32,064 cache write, 2,292 output.
