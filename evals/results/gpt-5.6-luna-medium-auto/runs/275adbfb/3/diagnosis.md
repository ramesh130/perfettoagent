# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (direct); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 2 claims kept, 1 dropped; 5 of 6 citations passed
- **Model's confidence:** high (never scored)

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

### c2. The regression is localized to application startup: the demo process's bindApplication work rose from 2,312.374002 ms across 20 launches in the baseline to 9,787.689047 ms across 20 launches in the current trace.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process, t.name AS thread, count(*) AS launches, sum(s.dur)/1e6 AS total_bind_ms, avg(s.dur)/1e6 AS mean_bind_ms, max(s.dur)/1e6 AS max_bind_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND s.name='bindApplication'
GROUP BY p.name,t.name
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process, t.name AS thread, count(*) AS launches, sum(s.dur)/1e6 AS total_bind_ms, avg(s.dur)/1e6 AS mean_bind_ms, max(s.dur)/1e6 AS max_bind_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND s.name='bindApplication'
GROUP BY p.name,t.name
```

### c3. Commit fb30a9c67862bd42f9d8fab36f6c8dff37069417 registers DemoApplication as the process Application and adds synchronous catalog-cache rebuilding and CRC32 file scanning in onCreate; blame assigns those lines to this commit.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- This diagnosis compares one baseline capture with one current capture, although each trace contains 20 cold starts; residual run-to-run variance cannot be separated completely.
- The capture ran on the sdk_gphone64_arm64 Android emulator and used a non-debuggable benchmark build.

## Dropped claims

### c1. Median cold-start TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a 315.198625 ms regression.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Run

`gpt-5.6-luna` on openai, effort medium: 26 tool calls, $0.0139, 161 s.
Tokens: 27 input, 110,776 cache read, 25,582 cache write, 4,391 output.
