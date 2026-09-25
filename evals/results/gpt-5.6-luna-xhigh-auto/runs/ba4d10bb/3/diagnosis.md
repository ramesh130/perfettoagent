# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. Median cold-start TTID increased from 839.504417 ms in the baseline to 1596.432376 ms in the current trace, a regression of 756.927959 ms.

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

### c2. Across 20 cold starts, the app's bindApplication slices grew from 7234.161254 ms total with a 428.984792 ms maximum in the baseline to 22770.106054 ms total with a 1506.993584 ms maximum in the current trace.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT ts, ts + dur AS end_ts
  FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
)
SELECT count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
  AND s.name = 'bindApplication'
  AND s.depth = 0
  AND EXISTS (SELECT 1 FROM starts WHERE s.ts >= starts.ts AND s.ts + s.dur <= starts.end_ts)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT ts, ts + dur AS end_ts
  FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
)
SELECT count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
  AND s.name = 'bindApplication'
  AND s.depth = 0
  AND EXISTS (SELECT 1 FROM starts WHERE s.ts >= starts.ts AND s.ts + s.dur <= starts.end_ts)
```

### c3. The JetnewsApplication class is present inside bindApplication in all 20 launches in both traces, localizing the changed launch work to application initialization.

The `baseline` trace: 1 row.

```sql
WITH ba AS (
  SELECT ts, ts + dur AS end_ts, track_id
  FROM slice
  WHERE name = 'bindApplication'
)
SELECT x.name, count(*) AS occurrences, sum(x.dur) / 1e6 AS total_ms, max(x.dur) / 1e6 AS max_ms
FROM slice AS x
WHERE x.name = 'Lcom/example/jetnews/JetnewsApplication;'
  AND EXISTS (SELECT 1 FROM ba WHERE x.track_id = ba.track_id AND x.ts >= ba.ts AND x.ts + x.dur <= ba.end_ts)
GROUP BY x.name
```

The `current` trace: 1 row.

```sql
WITH ba AS (
  SELECT ts, ts + dur AS end_ts, track_id
  FROM slice
  WHERE name = 'bindApplication'
)
SELECT x.name, count(*) AS occurrences, sum(x.dur) / 1e6 AS total_ms, max(x.dur) / 1e6 AS max_ms
FROM slice AS x
WHERE x.name = 'Lcom/example/jetnews/JetnewsApplication;'
  AND EXISTS (SELECT 1 FROM ba WHERE x.track_id = ba.track_id AND x.ts >= ba.ts AND x.ts + x.dur <= ba.end_ts)
GROUP BY x.name
```

### c4. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() to JetnewsApplication.onCreate(); the implementation performs synchronous article-cache validation/rebuild, reads the cache, and computes a CRC before application initialization continues.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c5. The trace-localized bindApplication slowdown and the source change are directly correlated, so bea44a9561ce48b23fc6102f729f1c78d49b2af5 is the attributed culprit.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT ts, ts + dur AS end_ts
  FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
)
SELECT count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
  AND s.name = 'bindApplication'
  AND s.depth = 0
  AND EXISTS (SELECT 1 FROM starts WHERE s.ts >= starts.ts AND s.ts + s.dur <= starts.end_ts)
```

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- There is one capture per build; the 20 repeated cold starts reduce but do not eliminate run-to-run noise.
- The trace does not expose a dedicated verifyArticleCache method slice, so attribution uses the enclosing bindApplication span, the JetnewsApplication class marker, and source blame.
- The current capture metadata identifies a debuggable debug build running on an Android emulator; baseline build metadata was not available.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 65 tool calls, $0.0508, 816 s.
Tokens: 54 input, 706,079 cache read, 68,976 cache write, 16,188 output.
