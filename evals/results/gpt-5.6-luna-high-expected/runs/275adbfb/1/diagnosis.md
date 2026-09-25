# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (correlated); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c2. The change is localized to application startup: the first current cold start has a bindApplication slice totaling 465.286959 ms, versus 113.503791 ms for the corresponding baseline startup.

The `baseline` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH startup AS (
  SELECT s.ts AS start_ts, s.ts + d.time_to_initial_display AS end_ts, d.upid
  FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_id = 74
)
SELECT sl.name, t.name AS thread_name, count(*) AS slices, sum(sl.dur) / 1e6 AS total_slice_ms, max(sl.dur) / 1e6 AS max_slice_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS t USING (utid)
JOIN startup ON t.upid = startup.upid
WHERE sl.ts < startup.end_ts AND sl.ts + sl.dur > startup.start_ts
GROUP BY sl.name, t.name
ORDER BY total_slice_ms DESC
LIMIT 30
```

The `current` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH startup AS (
  SELECT s.ts AS start_ts, s.ts + d.time_to_initial_display AS end_ts, d.upid
  FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_id = 86
)
SELECT sl.name, t.name AS thread_name, count(*) AS slices, sum(sl.dur) / 1e6 AS total_slice_ms, max(sl.dur) / 1e6 AS max_slice_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS t USING (utid)
JOIN startup ON t.upid = startup.upid
WHERE sl.ts < startup.end_ts AND sl.ts + sl.dur > startup.start_ts
GROUP BY sl.name, t.name
ORDER BY total_slice_ms DESC
LIMIT 30
```

### c3. The additional startup time is consistent with synchronous file I/O on the main thread: D-state I/O-wait time rose from 40.042994 ms in the baseline to 155.082492 ms in the current startup interval.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH startup AS (
  SELECT s.ts AS start_ts, s.ts + d.time_to_initial_display AS end_ts, d.upid
  FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_id = 74
), main AS (
  SELECT t.utid FROM thread AS t JOIN startup ON t.upid = startup.upid WHERE t.is_main_thread
)
SELECT state, io_wait, blocked_function, sum(ts.dur) / 1e6 AS total_ms, max(ts.dur) / 1e6 AS max_ms
FROM __intrinsic_thread_state AS ts JOIN main ON ts.utid = main.utid, startup
WHERE ts.ts < startup.end_ts AND ts.ts + ts.dur > startup.start_ts
GROUP BY state, io_wait, blocked_function
ORDER BY total_ms DESC
```

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH startup AS (
  SELECT s.ts AS start_ts, s.ts + d.time_to_initial_display AS end_ts, d.upid
  FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_id = 86
), main AS (
  SELECT t.utid FROM thread AS t JOIN startup ON t.upid = startup.upid WHERE t.is_main_thread
)
SELECT state, io_wait, blocked_function, sum(ts.dur) / 1e6 AS total_ms, max(ts.dur) / 1e6 AS max_ms
FROM __intrinsic_thread_state AS ts JOIN main ON ts.utid = main.utid, startup
WHERE ts.ts < startup.end_ts AND ts.ts + ts.dur > startup.start_ts
GROUP BY state, io_wait, blocked_function
ORDER BY total_ms DESC
```

### c4. The range head adds DemoApplication as the manifest-declared Application and performs launch-time catalog-cache rebuilding and checksum reading in its onCreate; this is the strongest correlation with the added main-thread startup I/O.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- There is only one capture per side, so run-to-run noise cannot be estimated independently.
- The captures ran on an Android emulator in a benchmark build, and the trace does not expose a method-level DemoApplication slice; therefore the culprit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 49 tool calls, $0.0294, 244 s.
Tokens: 78 input, 403,260 cache read, 28,076 cache write, 11,899 output.
