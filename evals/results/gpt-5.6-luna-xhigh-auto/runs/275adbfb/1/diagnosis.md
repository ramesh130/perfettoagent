# Regression

- **Metric:** `startup_ttfd_ms` +646.68 ms (2,077.31 → 2,723.99 ms)
- **Culprit:** `fb30a9c67862` (direct); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 3 claims kept, 1 dropped; 9 of 10 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttfd_ms` | ms | 2,077.31 | 2,723.99 | +646.68 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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

### c2. Across 20 recorded app bindApplication spans on the main thread, average duration rose from 115.6187001 ms in baseline to 489.38445235 ms in current. The current range was 335.670458–659.952501 ms, versus 62.514417–467.453209 ms at baseline.

The `baseline` trace: 1 row.

```sql
SELECT COUNT(*) AS launches, MIN(s.dur) / 1e6 AS min_bind_application_ms, MAX(s.dur) / 1e6 AS max_bind_application_ms, AVG(s.dur) / 1e6 AS avg_bind_application_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE s.name = 'bindApplication' AND p.name = 'com.superplayer.demo' AND t.tid = p.pid;
```

The `current` trace: 1 row.

```sql
SELECT COUNT(*) AS launches, MIN(s.dur) / 1e6 AS min_bind_application_ms, MAX(s.dur) / 1e6 AS max_bind_application_ms, AVG(s.dur) / 1e6 AS avg_bind_application_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE s.name = 'bindApplication' AND p.name = 'com.superplayer.demo' AND t.tid = p.pid;
```

### c3. fb30a9c67862bd42f9d8fab36f6c8dff37069417 wires DemoApplication into the manifest and adds Application.onCreate work that checks a catalog cache, may rebuild it, and computes a CRC32 over a 192 MiB cache.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c4. The launch-time Application work matches the large bindApplication increase in the current trace, so fb30a9c67862bd42f9d8fab36f6c8dff37069417 is the direct culprit for the startup regression.

The `baseline` trace: 1 row.

```sql
SELECT COUNT(*) AS launches, MIN(s.dur) / 1e6 AS min_bind_application_ms, MAX(s.dur) / 1e6 AS max_bind_application_ms, AVG(s.dur) / 1e6 AS avg_bind_application_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE s.name = 'bindApplication' AND p.name = 'com.superplayer.demo' AND t.tid = p.pid;
```

The `current` trace: 1 row.

```sql
SELECT COUNT(*) AS launches, MIN(s.dur) / 1e6 AS min_bind_application_ms, MAX(s.dur) / 1e6 AS max_bind_application_ms, AVG(s.dur) / 1e6 AS avg_bind_application_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE s.name = 'bindApplication' AND p.name = 'com.superplayer.demo' AND t.tid = p.pid;
```

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- This comparison uses one baseline/current capture pair, so independent run-to-run variance is not estimated.
- The current capture metadata identifies an SDK 36 sdk_gphone64_arm64 emulator and a non-debuggable benchmark build; results may differ on physical devices or other build configurations.

## Dropped claims

### c1. Median cold-start time to full display increased from 2077.310959 ms in baseline to 2723.988335 ms in current, a delta of 646.677376 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 48 SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1 ^ syntax error near 'DESC'

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 48 SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1 ^ syntax error near 'DESC'

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 65 tool calls, $0.0465, 424 s.
Tokens: 51 input, 513,121 cache read, 67,913 cache write, 16,039 output.
