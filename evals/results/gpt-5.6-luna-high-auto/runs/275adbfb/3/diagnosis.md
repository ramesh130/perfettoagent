# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (correlated); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. Median cold-start TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a regression of 315.198625 ms.

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 100) AS value
```

### c2. The regression is localized to application binding on the app's main thread: the first current bindApplication slice lasted 465.286959 ms, versus 113.503791 ms in the baseline, while makeApplication and Startup remained short in both traces.

The `baseline` trace: 3 rows.

```sql
SELECT p.name, t.tid, t.name AS thread_name, s.name, s.ts, s.dur
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.ts >= 1612281204727 AND s.ts < 1612393003477
  AND s.name IN ('bindApplication','makeApplication','Startup')
ORDER BY s.ts;
```

The `current` trace: 3 rows.

```sql
SELECT p.name, t.tid, t.name AS thread_name, s.name, s.ts, s.dur
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.ts >= 1760197336505 AND s.ts < 1760661135756
  AND s.name IN ('bindApplication','makeApplication','Startup')
ORDER BY s.ts;
```

### c3. The current bindApplication interval also contains substantially more uninterruptible waiting: 123.55241 ms in state D versus 18.040036 ms in the comparable baseline interval.

The `baseline` trace: 5 rows.

```sql
SELECT state, sum(dur) / 1e6 AS ms, count(*) AS slices
FROM thread_state
WHERE utid = (SELECT tt.utid
              FROM thread_track AS tt
              JOIN slice AS s ON s.track_id = tt.id
              WHERE s.name = 'bindApplication' AND s.ts = 1612281204727)
  AND ts >= 1612281204727 AND ts < 1612393003477
GROUP BY state
ORDER BY ms DESC;
```

The `current` trace: 5 rows.

```sql
SELECT state, sum(dur) / 1e6 AS ms, count(*) AS slices
FROM thread_state
WHERE utid = (SELECT tt.utid
              FROM thread_track AS tt
              JOIN slice AS s ON s.track_id = tt.id
              WHERE s.name = 'bindApplication' AND s.ts = 1760197336505)
  AND ts >= 1760197336505 AND ts < 1760661135756
GROUP BY state
ORDER BY ms DESC;
```

### c4. The range's head commit adds DemoApplication as the process Application and introduces launch-time catalog-cache rebuild and checksum work in DemoApplication.kt; blame attributes those lines to the same commit.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c5. The launch-time cache work is therefore likely the cause of the startup regression, although the trace exposes the enclosing bindApplication slice rather than a method-level DemoApplication slice.

The `current` trace: 3 rows.

```sql
SELECT p.name, t.tid, t.name AS thread_name, s.name, s.ts, s.dur
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo'
  AND s.ts >= 1760197336505 AND s.ts < 1760661135756
  AND s.name IN ('bindApplication','makeApplication','Startup')
ORDER BY s.ts;
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- Each side is a single capture, so run-to-run noise cannot be measured independently.
- The captures were made on an Android emulator; the current run metadata identifies sdk_gphone64_arm64 on SDK 36.
- Attribution is correlated rather than direct because the trace records the enclosing bindApplication work, not source-level DemoApplication methods.

## Run

`gpt-5.6-luna` on openai, effort high: 35 tool calls, $0.0193, 248 s.
Tokens: 27 input, 139,846 cache read, 31,474 cache write, 7,200 output.
