# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
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

### c2. The startup delay is concentrated in the app's main-thread bindApplication work: current bindApplication totals 22770.106054 ms across 20 starts, with a maximum of 1506.993584 ms, versus 7234.161254 ms and 428.984792 ms in the baseline.

The `current` trace: 30 rows.

```sql
SELECT t.name AS thread, s.name, COUNT(*) AS occurrences, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid WHERE p.name='com.example.jetnews' AND s.dur>0 GROUP BY t.name,s.name ORDER BY total_ms DESC LIMIT 30;
```

The `baseline` trace: 10 rows.

```sql
SELECT t.name AS thread, s.name, COUNT(*) AS occurrences, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid WHERE p.name='com.example.jetnews' AND s.dur>0 GROUP BY t.name,s.name ORDER BY total_ms DESC LIMIT 10;
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() to JetnewsApplication.onCreate(), including synchronous cache writing and CRC verification before the application container is created; this directly matches the new launch-time main-thread work.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side has one capture, so run-to-run variability cannot be fully excluded.
- The traces were captured on an Android emulator and the current build is debuggable.

## Run

`gpt-5.6-luna` on openai, effort low: 16 tool calls, $0.0071, 111 s.
Tokens: 21 input, 55,536 cache read, 11,993 cache write, 2,508 output.
