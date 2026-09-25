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

### c1. Median cold-start TTID increased from 839.504417 ms to 1596.432376 ms, a delta of 756.927959 ms.

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

### c2. The startup cost is concentrated in the app's main thread: all 20 baseline bindApplication slices were 328.432542–428.984792 ms, versus 1003.669583–1506.993584 ms currently.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_count, min(s.dur)/1e6 AS min_bind_ms, max(s.dur)/1e6 AS max_bind_ms, avg(s.dur)/1e6 AS avg_bind_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread t ON t.utid=tt.utid
JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews' AND t.name='example.jetnews' AND s.name='bindApplication'
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_count, min(s.dur)/1e6 AS min_bind_ms, max(s.dur)/1e6 AS max_bind_ms, avg(s.dur)/1e6 AS avg_bind_ms
FROM slice s
JOIN thread_track tt ON tt.id=s.track_id
JOIN thread t ON t.utid=tt.utid
JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews' AND t.name='example.jetnews' AND s.name='bindApplication'
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() to JetnewsApplication.onCreate(), before the application container is created; the verifier can write a 768 MiB cache and then reads it in 64 KiB blocks for CRC verification.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. The launch call and the cache-verification method are both attributed by blame to bea44a9561ce48b23fc6102f729f1c78d49b2af5, linking the new synchronous startup work to the longer bindApplication interval.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis compares one capture per side, so smaller changes could be affected by run-to-run noise; the observed TTID increase is large and consistent across the startup slices.
- The current metadata identifies a debuggable emulator run, so absolute timings may differ from a release build on physical hardware.

## Run

`gpt-5.6-luna` on openai, effort high: 36 tool calls, $0.0295, 168 s.
Tokens: 36 input, 273,150 cache read, 55,136 cache write, 8,500 output.
