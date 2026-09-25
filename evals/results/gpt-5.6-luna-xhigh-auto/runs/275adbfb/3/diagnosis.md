# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (direct); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 6 claims kept, 0 dropped; 12 of 12 citations passed
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

### c1. Median time to initial display increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a 315.198625 ms regression.

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

### c2. Both traces contain 20 cold starts for com.superplayer.demo, so the selected medians represent 20 starts per side.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT package, startup_type, count(*) AS cold_start_count
FROM android_startups
WHERE package = 'com.superplayer.demo' AND startup_type = 'cold'
GROUP BY package, startup_type;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT package, startup_type, count(*) AS cold_start_count
FROM android_startups
WHERE package = 'com.superplayer.demo' AND startup_type = 'cold'
GROUP BY package, startup_type;
```

### c3. The regression localizes to bindApplication on the app process thread: total bindApplication time grew from 2312.374002 ms, or 115.6187001 ms per bind, to 9787.689047 ms, or 489.38445235 ms per bind.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS bind_count, sum(sl.dur) / 1e6 AS total_bind_ms, avg(sl.dur) / 1e6 AS avg_bind_ms, max(sl.dur) / 1e6 AS max_bind_ms
FROM slice AS sl
JOIN thread_track AS tt ON tt.id = sl.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication' AND sl.depth = 0;
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS bind_count, sum(sl.dur) / 1e6 AS total_bind_ms, avg(sl.dur) / 1e6 AS avg_bind_ms, max(sl.dur) / 1e6 AS max_bind_ms
FROM slice AS sl
JOIN thread_track AS tt ON tt.id = sl.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication' AND sl.depth = 0;
```

### c4. Across those bindApplication intervals, D-state overlap increased from 733.649545 ms in the baseline to 2941.498574 ms in the current trace.

The `baseline` trace: 5 rows.

```sql
WITH binds AS (
  SELECT sl.ts, sl.ts + sl.dur AS end_ts, tt.utid
  FROM slice AS sl
  JOIN thread_track AS tt ON tt.id = sl.track_id
  JOIN thread AS th ON th.utid = tt.utid
  JOIN process AS p ON p.upid = th.upid
  WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication' AND sl.depth = 0
), overlaps AS (
  SELECT st.state,
    min(st.ts + st.dur, b.end_ts) - max(st.ts, b.ts) AS overlap_ns
  FROM thread_state AS st
  JOIN binds AS b ON st.utid = b.utid AND st.ts < b.end_ts AND b.ts < st.ts + st.dur
  WHERE st.dur > 0
)
SELECT state, count(*) AS intervals, sum(overlap_ns) / 1e6 AS overlapped_ms
FROM overlaps
WHERE overlap_ns > 0
GROUP BY state
ORDER BY overlapped_ms DESC;
```

The `current` trace: 5 rows.

```sql
WITH binds AS (
  SELECT sl.ts, sl.ts + sl.dur AS end_ts, tt.utid
  FROM slice AS sl
  JOIN thread_track AS tt ON tt.id = sl.track_id
  JOIN thread AS th ON th.utid = tt.utid
  JOIN process AS p ON p.upid = th.upid
  WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication' AND sl.depth = 0
), overlaps AS (
  SELECT st.state,
    min(st.ts + st.dur, b.end_ts) - max(st.ts, b.ts) AS overlap_ns
  FROM thread_state AS st
  JOIN binds AS b ON st.utid = b.utid AND st.ts < b.end_ts AND b.ts < st.ts + st.dur
  WHERE st.dur > 0
)
SELECT state, count(*) AS intervals, sum(overlap_ns) / 1e6 AS overlapped_ms
FROM overlaps
WHERE overlap_ns > 0
GROUP BY state
ORDER BY overlapped_ms DESC;
```

### c5. The head commit registers DemoApplication as the process Application and adds launch-time catalog-cache validation: its onCreate checks the file, optionally rebuilds it, and reads it through a CRC32 checksum before returning.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c6. The new Application.onCreate file work directly explains the expanded bindApplication interval and attributes the startup regression to fb30a9c67862bd42f9d8fab36f6c8dff37069417.

The `current` trace: 1 row.

```sql
SELECT count(*) AS bind_count, sum(sl.dur) / 1e6 AS total_bind_ms, avg(sl.dur) / 1e6 AS avg_bind_ms, max(sl.dur) / 1e6 AS max_bind_ms
FROM slice AS sl
JOIN thread_track AS tt ON tt.id = sl.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND sl.name = 'bindApplication' AND sl.depth = 0;
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- This compares one capture pair; although each side contains 20 cold starts, capture-to-capture noise is not independently quantified.
- The current run is a benchmark capture on an SDK 36 emulator, so absolute storage and startup timings may not generalize to physical devices.
- Trace localization is at the bindApplication slice and thread-state level rather than a source-line CPU profile.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 55 tool calls, $0.0309, 384 s.
Tokens: 39 input, 253,418 cache read, 38,327 cache write, 13,565 output.
