# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (correlated); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 5 claims kept, 0 dropped; 11 of 11 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 349.68 | 664.88 | +315.2 |

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

### c1. Median cold-start TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a 315.198625 ms regression.

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

### c2. The slowdown is concentrated in application binding: across 20 launches, main-thread bindApplication averaged 115.6187001 ms in the baseline and 489.38445235 ms in the current trace.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS starts, avg(s.dur) / 1e6 AS avg_bind_ms, min(s.dur) / 1e6 AS min_bind_ms, max(s.dur) / 1e6 AS max_bind_ms
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS th ON th.utid = tt.utid
WHERE s.name = 'bindApplication' AND th.is_main_thread = 1
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS starts, avg(s.dur) / 1e6 AS avg_bind_ms, min(s.dur) / 1e6 AS min_bind_ms, max(s.dur) / 1e6 AS max_bind_ms
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS th ON th.utid = tt.utid
WHERE s.name = 'bindApplication' AND th.is_main_thread = 1
```

### c3. For the first cold start, bindApplication lasted 465.286959 ms on the current app main thread versus 102.318666 ms in the baseline.

The `current` trace: 1 row.

```sql
SELECT s.name, s.ts, s.dur / 1e6 AS dur_ms, th.name AS thread_name, th.is_main_thread
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS th ON th.utid = tt.utid
WHERE th.upid = 385 AND s.name = 'bindApplication'
ORDER BY s.ts LIMIT 20
```

The `baseline` trace: 1 row.

```sql
SELECT s.name, s.ts, s.dur / 1e6 AS dur_ms, th.name AS thread_name, th.is_main_thread
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS th ON th.utid = tt.utid
WHERE th.upid = 381 AND s.name = 'bindApplication'
ORDER BY s.ts LIMIT 20
```

### c4. Commit fb30a9c67862bd42f9d8fab36f6c8dff37069417 wires a new DemoApplication into the manifest; its onCreate checks catalog.cache, may rebuild it, and computes a CRC over a 192 MiB cache during launch.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c5. The launch-time cache work is the likely cause of the TTID regression because the commit changes application startup and the trace shows a large, repeated increase in main-thread bindApplication duration.

The `current` trace: 1 row.

```sql
SELECT count(*) AS starts, avg(s.dur) / 1e6 AS avg_bind_ms, min(s.dur) / 1e6 AS min_bind_ms, max(s.dur) / 1e6 AS max_bind_ms
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS th ON th.utid = tt.utid
WHERE s.name = 'bindApplication' AND th.is_main_thread = 1
```

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS starts, avg(s.dur) / 1e6 AS avg_bind_ms, min(s.dur) / 1e6 AS min_bind_ms, max(s.dur) / 1e6 AS max_bind_ms
FROM slice AS s
JOIN track AS tr ON tr.id = s.track_id
JOIN thread_track AS tt ON tt.id = tr.id
JOIN thread AS th ON th.utid = tt.utid
WHERE s.name = 'bindApplication' AND th.is_main_thread = 1
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- There is only one capture per side, so run-to-run noise cannot be estimated independently.
- The captures use an sdk_gphone64_arm64 emulator; the current run is a non-debuggable benchmark build.
- The trace localizes the cost to bindApplication rather than providing a method-level timing for DemoApplication itself, so the commit attribution is correlated rather than a direct method-level trace attribution.

## Run

`gpt-5.6-luna` on openai, effort high: 43 tool calls, $0.0292, 305 s.
Tokens: 45 input, 342,772 cache read, 43,648 cache write, 9,482 output.
