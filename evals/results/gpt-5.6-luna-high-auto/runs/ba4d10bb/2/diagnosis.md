# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (correlated); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
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

### c2. The change is localized to the app's main thread during cold start: baseline bindApplication slices were roughly 328–429 ms, while current slices were roughly 1004–1507 ms, across 20 cold starts on each side.

The `baseline` trace: 100 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT p.name AS process_name, t.name AS thread_name, s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE p.name = 'com.example.jetnews'
  AND EXISTS (SELECT 1 FROM android_startups AS a WHERE a.package = p.name AND a.startup_type = 'cold' AND s.ts >= a.ts AND s.ts < a.ts + a.dur)
GROUP BY p.name, t.name, s.name
ORDER BY total_ms DESC
LIMIT 100
```

The `current` trace: 100 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT p.name AS process_name, t.name AS thread_name, s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE p.name = 'com.example.jetnews'
  AND EXISTS (SELECT 1 FROM android_startups AS a WHERE a.package = p.name AND a.startup_type = 'cold' AND s.ts >= a.ts AND s.ts < a.ts + a.dur)
GROUP BY p.name, t.name, s.name
ORDER BY total_ms DESC
LIMIT 100
```

### c3. The current trace shows every cold start spending substantially longer in the app process's bindApplication slice than the baseline.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT a.startup_id, a.ts / 1e6 AS startup_ts_ms, a.dur / 1e6 AS startup_dur_ms, s.name, s.ts / 1e6 AS slice_ts_ms, s.dur / 1e6 AS slice_dur_ms
FROM android_startups AS a
JOIN slice AS s ON s.name = 'bindApplication'
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE a.package = 'com.example.jetnews' AND a.startup_type = 'cold' AND p.name = a.package
  AND s.ts >= a.ts AND s.ts < a.ts + a.dur
ORDER BY a.startup_id
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT a.startup_id, a.ts / 1e6 AS startup_ts_ms, a.dur / 1e6 AS startup_dur_ms, s.name, s.ts / 1e6 AS slice_ts_ms, s.dur / 1e6 AS slice_dur_ms
FROM android_startups AS a
JOIN slice AS s ON s.name = 'bindApplication'
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE a.package = 'com.example.jetnews' AND a.startup_type = 'cold' AND p.name = a.package
  AND s.ts >= a.ts AND s.ts < a.ts + a.dur
ORDER BY a.startup_id
```

### c4. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() directly to JetnewsApplication.onCreate(), including creation of a 768 MiB cache file when needed and a full-cache CRC read before the application container is initialized.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c5. The startup regression is attributed to bea44a9561ce48b23fc6102f729f1c78d49b2af5: its launch-time cache I/O correlates with the large increase in bindApplication duration and the TTID regression.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT a.startup_id, a.ts / 1e6 AS startup_ts_ms, a.dur / 1e6 AS startup_dur_ms, s.name, s.ts / 1e6 AS slice_ts_ms, s.dur / 1e6 AS slice_dur_ms
FROM android_startups AS a
JOIN slice AS s ON s.name = 'bindApplication'
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE a.package = 'com.example.jetnews' AND a.startup_type = 'cold' AND p.name = a.package
  AND s.ts >= a.ts AND s.ts < a.ts + a.dur
ORDER BY a.startup_id
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so smaller differences could be affected by run-to-run noise.
- The current trace metadata identifies a debuggable debug build running on the sdk_gphone64_arm64 emulator; results may differ on production builds and physical devices.
- The trace localizes the cost to bindApplication but does not contain an app-level stack row naming verifyArticleCache(), so the commit attribution is marked correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 36 tool calls, $0.0230, 541 s.
Tokens: 30 input, 219,118 cache read, 40,393 cache write, 7,131 output.
