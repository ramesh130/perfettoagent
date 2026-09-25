# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (direct); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 3 claims kept, 1 dropped; 9 of 10 citations passed
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

### c2. The increase is localized to the app process's main-thread bindApplication work: 20 slices totaled 2312.374 ms in the baseline versus 9787.689 ms in the current trace, with average slice duration rising from 115.619 ms to 489.384 ms.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_slices, round(sum(sl.dur) / 1e6, 3) AS bind_total_ms, round(avg(sl.dur) / 1e6, 3) AS bind_avg_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication'
GROUP BY p.name, t.name;
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_slices, round(sum(sl.dur) / 1e6, 3) AS bind_total_ms, round(avg(sl.dur) / 1e6, 3) AS bind_avg_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication'
GROUP BY p.name, t.name;
```

### c3. Commit fb30a9c67862bd42f9d8fab36f6c8dff37069417 adds DemoApplication and registers it in the manifest. Its onCreate performs synchronous catalog-cache validation, potentially writes a 192 MiB cache, and computes a checksum during application startup.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c4. The new application-start work matches the large bindApplication increase and is the direct cause attributed to the TTID regression.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_slices, round(sum(sl.dur) / 1e6, 3) AS bind_total_ms, round(avg(sl.dur) / 1e6, 3) AS bind_avg_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication'
GROUP BY p.name, t.name;
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS bind_slices, round(sum(sl.dur) / 1e6, 3) AS bind_total_ms, round(avg(sl.dur) / 1e6, 3) AS bind_avg_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS t ON tt.utid = t.utid
JOIN process AS p ON t.upid = p.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication'
GROUP BY p.name, t.name;
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- This conclusion is based on one baseline capture and one current capture, although each trace contains 20 cold starts.
- The current run metadata identifies an sdk_gphone64_arm64 emulator and a benchmark, non-debuggable build; emulator I/O timing may not represent production hardware.
- The trace localizes the added work at bindApplication granularity rather than exposing a dedicated DemoApplication method slice.

## Dropped claims

### c1. Cold-start TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a delta of 315.19862500000005 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 48 SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1 ^ syntax error near 'DESC'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 48 SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1 ^ syntax error near 'DESC'

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

`gpt-5.6-luna` on openai, effort high: 33 tool calls, $0.0276, 199 s.
Tokens: 48 input, 326,334 cache read, 35,166 cache write, 10,267 output.
