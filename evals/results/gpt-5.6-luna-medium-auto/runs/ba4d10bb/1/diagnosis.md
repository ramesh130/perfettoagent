# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. Median cold-start TTID increased from 839.504417 ms in the baseline to 1596.432376 ms in the current trace, a 756.927959 ms regression.

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

The `current` trace: 1 row.

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

### c2. The regression is concentrated in application startup: the first current cold start contains a 1284.525876 ms bindApplication slice, versus 428.984792 ms in the baseline.

The `current` trace: 30 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
WHERE s.ts >= 6942780297143 AND s.ts < 6944486056352
GROUP BY s.name
HAVING total_ms > 10
ORDER BY total_ms DESC
LIMIT 30
```

The `baseline` trace: 30 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s
WHERE s.ts >= 5701774685260 AND s.ts < 5702792260218
GROUP BY s.name
HAVING total_ms > 10
ORDER BY total_ms DESC
LIMIT 30
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds synchronous offline article-cache verification from JetnewsApplication.onCreate, matching the added work in bindApplication and making it the direct culprit.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

The `current` trace: 24 rows.

```sql
SELECT s.name, s.ts, s.dur / 1e6 AS dur_ms, s.track_id
FROM slice s
WHERE s.ts >= 6942780297143 AND s.ts < 6944486056352
  AND s.dur > 100000000
ORDER BY s.dur DESC
LIMIT 30
```

### c4. The cache-verification implementation is attributed to bea44a9561ce48b23fc6102f729f1c78d49b2af5 by blame, including the onCreate call and the file read/write and CRC loop.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side has one capture, so run-to-run variation cannot be completely excluded; however, the large TTID increase and matching bindApplication increase make noise unlikely.
- The traces were captured on an Android emulator (sdk_gphone64_arm64, SDK 36) using a debuggable debug build.

## Run

`gpt-5.6-luna` on openai, effort medium: 34 tool calls, $0.0237, 504 s.
Tokens: 39 input, 347,515 cache read, 44,462 cache write, 4,650 output.
