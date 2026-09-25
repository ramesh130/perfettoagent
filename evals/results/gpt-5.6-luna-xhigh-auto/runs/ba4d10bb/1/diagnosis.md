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

### c1. Median cold-start TTID increased from 839.504417 ms in baseline to 1596.432376 ms in current, a 756.927959 ms regression.

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

### c2. The regression localizes to the app process's main-thread bindApplication work: 20 slices averaged 361.7080627 ms in baseline versus 1138.5053027 ms in current.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS bind_applications,
       avg(s.dur) / 1e6 AS avg_ms,
       min(s.dur) / 1e6 AS min_ms,
       max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND t.tid = p.pid
  AND s.name = 'bindApplication'
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS bind_applications,
       avg(s.dur) / 1e6 AS avg_ms,
       min(s.dur) / 1e6 AS min_ms,
       max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND t.tid = p.pid
  AND s.name = 'bindApplication'
```

### c3. Current bindApplication windows contain 121 print markers naming java.util.zip.CRC32 across all 20 launches; baseline contains none.

The `baseline` trace: 1 row.

```sql
WITH binds AS (
  SELECT s.ts, s.ts + s.dur AS ts_end
  FROM slice AS s
  JOIN thread_track AS tt ON tt.id = s.track_id
  JOIN thread AS t ON t.utid = tt.utid
  JOIN process AS p ON p.upid = t.upid
  WHERE p.name = 'com.example.jetnews' AND t.tid = p.pid
    AND s.name = 'bindApplication'
)
SELECT count(*) AS crc32_prints,
       count(DISTINCT b.ts) AS bind_applications_with_crc32,
       min(e.ts) AS first_ts, max(e.ts) AS last_ts
FROM __intrinsic_ftrace_event AS e
JOIN __intrinsic_args AS a ON a.arg_set_id = e.arg_set_id
JOIN binds AS b ON e.ts >= b.ts AND e.ts < b.ts_end
WHERE e.name = 'print'
  AND a.string_value LIKE '%java.util.zip.CRC32%'
```

The `current` trace: 1 row.

```sql
WITH binds AS (
  SELECT s.ts, s.ts + s.dur AS ts_end
  FROM slice AS s
  JOIN thread_track AS tt ON tt.id = s.track_id
  JOIN thread AS t ON t.utid = tt.utid
  JOIN process AS p ON p.upid = t.upid
  WHERE p.name = 'com.example.jetnews' AND t.tid = p.pid
    AND s.name = 'bindApplication'
)
SELECT count(*) AS crc32_prints,
       count(DISTINCT b.ts) AS bind_applications_with_crc32,
       min(e.ts) AS first_ts, max(e.ts) AS last_ts
FROM __intrinsic_ftrace_event AS e
JOIN __intrinsic_args AS a ON a.arg_set_id = e.arg_set_id
JOIN binds AS b ON e.ts >= b.ts AND e.ts < b.ts_end
WHERE e.name = 'print'
  AND a.string_value LIKE '%java.util.zip.CRC32%'
```

### c4. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() to JetnewsApplication.onCreate and performs synchronous article-cache creation plus a full CRC32 verification in the changed application file.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c5. The new CRC32 activity occurs inside every current bindApplication window and matches the cache-verification code introduced by bea44a9561ce48b23fc6102f729f1c78d49b2af5, making that commit the direct attribution for the startup regression.

The `current` trace: 1 row.

```sql
WITH binds AS (
  SELECT s.ts, s.ts + s.dur AS ts_end
  FROM slice AS s
  JOIN thread_track AS tt ON tt.id = s.track_id
  JOIN thread AS t ON t.utid = tt.utid
  JOIN process AS p ON p.upid = t.upid
  WHERE p.name = 'com.example.jetnews' AND t.tid = p.pid
    AND s.name = 'bindApplication'
)
SELECT count(*) AS crc32_prints,
       count(DISTINCT b.ts) AS bind_applications_with_crc32,
       min(e.ts) AS first_ts, max(e.ts) AS last_ts
FROM __intrinsic_ftrace_event AS e
JOIN __intrinsic_args AS a ON a.arg_set_id = e.arg_set_id
JOIN binds AS b ON e.ts >= b.ts AND e.ts < b.ts_end
WHERE e.name = 'print'
  AND a.string_value LIKE '%java.util.zip.CRC32%'
```

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This compares one baseline capture with one current capture, so run-to-run noise is not independently estimated.
- The trace localizes the added startup work to bindApplication and CRC32 runtime activity rather than to a source line; the source-level attribution is based on matching that runtime activity to the commit's changed code.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 68 tool calls, $0.0609, 649 s.
Tokens: 60 input, 1,000,423 cache read, 86,373 cache write, 16,110 output.
