# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
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

### c1. The median cold-start TTID increased from 839.504417 ms to 1596.432376 ms, a 756.927959 ms regression.

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

### c2. The slowdown is localized to application binding: across 20 cold starts, the median bindApplication duration increased from 355.057126 ms to 1108.132709 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT startup_id, ts, ts_end FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
), binds AS (
  SELECT s.startup_id, b.dur / 1e6 AS bind_ms
  FROM starts AS s
  JOIN slice AS b ON b.name = 'bindApplication' AND b.ts <= s.ts_end AND b.ts + b.dur >= s.ts
  JOIN thread_track AS tt ON b.track_id = tt.id
  JOIN thread AS t ON tt.utid = t.utid
  WHERE t.name = 'example.jetnews'
), ranked AS (
  SELECT bind_ms, row_number() OVER (ORDER BY bind_ms) AS rank, count(*) OVER () AS n
  FROM binds
)
SELECT count(*) AS cold_starts, min(bind_ms) AS min_bind_ms, max(bind_ms) AS max_bind_ms,
       (SELECT bind_ms FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms
FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT startup_id, ts, ts_end FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
), binds AS (
  SELECT s.startup_id, b.dur / 1e6 AS bind_ms
  FROM starts AS s
  JOIN slice AS b ON b.name = 'bindApplication' AND b.ts <= s.ts_end AND b.ts + b.dur >= s.ts
  JOIN thread_track AS tt ON b.track_id = tt.id
  JOIN thread AS t ON tt.utid = t.utid
  WHERE t.name = 'example.jetnews'
), ranked AS (
  SELECT bind_ms, row_number() OVER (ORDER BY bind_ms) AS rank, count(*) OVER () AS n
  FROM binds
)
SELECT count(*) AS cold_starts, min(bind_ms) AS min_bind_ms, max(bind_ms) AS max_bind_ms,
       (SELECT bind_ms FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms
FROM ranked
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() to JetnewsApplication.onCreate(), including creation/checking of a 768 MiB articles.cache file and a full CRC read at launch.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. Blame at the range head assigns the launch call and cache-verification implementation to bea44a9561ce48b23fc6102f729f1c78d49b2af5.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one baseline capture and one current capture, so run-to-run noise cannot be fully quantified.
- The captures were from a debuggable build on an emulator; absolute startup times may not generalize to production hardware.

## Run

`gpt-5.6-luna` on openai, effort high: 40 tool calls, $0.0276, 154 s.
Tokens: 36 input, 274,717 cache read, 47,876 cache write, 8,421 output.
