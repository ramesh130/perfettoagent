# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (correlated); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. Cold-start time to initial display increased from 839.504417 ms in the baseline to 1596.432376 ms in the current trace, a 756.927959 ms regression.

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

### c2. The additional startup time is localized to the app's main-thread bindApplication span: its summed duration across the cold starts rose from 7234.161254 ms to 22770.106054 ms.

The `baseline` trace: 4 rows.

```sql
SELECT p.name AS process, t.name AS thread, sl.name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON sl.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid
WHERE p.name='com.example.jetnews' AND t.name='example.jetnews' AND sl.name IN ('bindApplication','Startup','ActivityThreadMain','performCreate:com.example.jetnews.ui.MainActivity')
GROUP BY p.name,t.name,sl.name ORDER BY sl.name
```

The `current` trace: 4 rows.

```sql
SELECT p.name AS process, t.name AS thread, sl.name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON sl.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid
WHERE p.name='com.example.jetnews' AND t.name='example.jetnews' AND sl.name IN ('bindApplication','Startup','ActivityThreadMain','performCreate:com.example.jetnews.ui.MainActivity')
GROUP BY p.name,t.name,sl.name ORDER BY sl.name
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds a verifyArticleCache() call to JetnewsApplication.onCreate(), including synchronous cache-file creation, a full cache read, and CRC computation before the application container is initialized.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. The startup regression is therefore correlated with bea44a9561ce48b23fc6102f729f1c78d49b2af5: the commit adds work directly to application launch, while the trace shows the corresponding app-main-thread bindApplication span becoming substantially longer.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

The `baseline` trace: 4 rows.

```sql
SELECT p.name AS process, t.name AS thread, sl.name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON sl.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid
WHERE p.name='com.example.jetnews' AND t.name='example.jetnews' AND sl.name IN ('bindApplication','Startup','ActivityThreadMain','performCreate:com.example.jetnews.ui.MainActivity')
GROUP BY p.name,t.name,sl.name ORDER BY sl.name
```

The `current` trace: 4 rows.

```sql
SELECT p.name AS process, t.name AS thread, sl.name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON sl.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid
WHERE p.name='com.example.jetnews' AND t.name='example.jetnews' AND sl.name IN ('bindApplication','Startup','ActivityThreadMain','performCreate:com.example.jetnews.ui.MainActivity')
GROUP BY p.name,t.name,sl.name ORDER BY sl.name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This comparison uses one trace per build, so run-to-run noise cannot be ruled out completely, although the regression is large and consistent across the cold starts recorded in each trace.
- The captures are from a debuggable emulator build, so absolute startup timings may not represent release performance.

## Run

`gpt-5.6-luna` on openai, effort high: 49 tool calls, $0.0302, 625 s.
Tokens: 39 input, 274,161 cache read, 51,485 cache write, 9,885 output.
