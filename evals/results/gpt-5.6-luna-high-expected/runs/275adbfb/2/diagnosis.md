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

### c1. Median cold-start TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a +315.198625 ms regression.

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

### c2. The measured startup population contains 20 cold starts in each trace, so the comparison is not based on a single startup.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display AS tt_id_ns
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display AS tt_id_ns
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.ts
```

### c3. The regression is localized to the app's main thread during bindApplication: the baseline has 20 such slices averaging 115.618700 ms, while the current trace has 20 averaging 489.38445235 ms.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_count, min(sl.dur)/1e6 AS min_bind_ms, avg(sl.dur)/1e6 AS avg_bind_ms, max(sl.dur)/1e6 AS max_bind_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS t ON t.utid = tr.utid
JOIN process AS p ON p.upid = t.upid
WHERE sl.name = 'bindApplication' AND p.name = 'com.superplayer.demo'
GROUP BY p.name, t.name
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_count, min(sl.dur)/1e6 AS min_bind_ms, avg(sl.dur)/1e6 AS avg_bind_ms, max(sl.dur)/1e6 AS max_bind_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS t ON t.utid = tr.utid
JOIN process AS p ON p.upid = t.upid
WHERE sl.name = 'bindApplication' AND p.name = 'com.superplayer.demo'
GROUP BY p.name, t.name
```

### c4. The range's head commit adds DemoApplication as the process-wide Application and introduces launch-time catalog-cache checking, possible cache rebuilding, and checksum work; blame assigns those implementation lines to that commit.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c5. The expanded bindApplication interval and the new Application startup work make fb30a9c67862bd42f9d8fab36f6c8dff37069417 the likely cause of the TTID regression.

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_count, min(sl.dur)/1e6 AS min_bind_ms, avg(sl.dur)/1e6 AS avg_bind_ms, max(sl.dur)/1e6 AS max_bind_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS t ON t.utid = tr.utid
JOIN process AS p ON p.upid = t.upid
WHERE sl.name = 'bindApplication' AND p.name = 'com.superplayer.demo'
GROUP BY p.name, t.name
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- There is one capture per side, so run-to-run variance cannot be estimated independently.
- The trace localizes the added work to bindApplication but does not expose a slice named DemoApplication or a source-level method; attribution is therefore correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 31 tool calls, $0.0311, 180 s.
Tokens: 33 input, 259,801 cache read, 53,093 cache write, 10,508 output.
