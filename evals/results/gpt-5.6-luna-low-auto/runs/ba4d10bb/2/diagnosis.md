# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. Cold-start median TTID increased from 839.504417 ms in the baseline to 1596.432376 ms in the current trace, a 756.927959 ms regression.

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

### c2. The startup slowdown is concentrated in application binding: 20 bindApplication slices totaled 7234.161254 ms in the baseline and 22770.106054 ms in the current trace.

The `baseline` trace: 1 row.

```sql
SELECT name, count(*) AS launches, sum(dur)/1e6 AS total_ms, avg(dur)/1e6 AS avg_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name = 'bindApplication' GROUP BY name
```

The `current` trace: 1 row.

```sql
SELECT name, count(*) AS launches, sum(dur)/1e6 AS total_ms, avg(dur)/1e6 AS avg_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name = 'bindApplication' GROUP BY name
```

### c3. The current trace contains 20 JetnewsApplication slices and CRC32-related startup work, while the baseline does not show CRC32 work in the corresponding cache/application slice search.

The `current` trace: 553 rows.

```sql
SELECT name, count(*) AS n, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name GLOB '*[Cc]ache*' OR name GLOB '*CRC*' OR name GLOB '*Application*' GROUP BY name ORDER BY total_ms DESC
```

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() before AppContainer initialization, including creation/checking of a 768 MiB cache and CRC32 scanning during Application.onCreate().

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c5. The added verifyArticleCache() call and implementation are attributed by blame to bea44a9561ce48b23fc6102f729f1c78d49b2af5.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side contains one capture with 20 cold starts, so run-to-run variance cannot be fully excluded.
- The captures are from an emulator (sdk_gphone64_arm64, SDK 36) and a debuggable debug build.
- TTFD was unavailable in both traces; the diagnosis uses TTID.

## Run

`gpt-5.6-luna` on openai, effort low: 22 tool calls, $0.0135, 441 s.
Tokens: 18 input, 68,796 cache read, 35,503 cache write, 2,743 output.
