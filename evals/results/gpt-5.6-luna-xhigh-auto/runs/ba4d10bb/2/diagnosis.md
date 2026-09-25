# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 5 claims kept, 1 dropped; 10 of 11 citations passed
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

### c2. Across 20 cold starts, the median bindApplication duration increased from 355.057126 ms to 1108.132709 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH binds AS (
  SELECT a.startup_id, s.dur / 1e6 AS bind_ms
  FROM android_startups AS a
  JOIN slice AS s
    ON s.name = 'bindApplication'
   AND s.ts >= a.ts AND s.ts < a.ts_end
  JOIN thread_track AS tr ON tr.id = s.track_id
  JOIN thread AS t ON t.utid = tr.utid
  WHERE a.startup_type = 'cold' AND a.package = 'com.example.jetnews'
    AND t.name = 'example.jetnews'
), ranked AS (
  SELECT bind_ms, row_number() OVER (ORDER BY bind_ms) AS rank, count(*) OVER () AS n
  FROM binds
)
SELECT count(*) AS cold_starts, min(bind_ms) AS min_bind_ms,
       max(bind_ms) AS max_bind_ms,
       (SELECT bind_ms FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms
FROM binds;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH binds AS (
  SELECT a.startup_id, s.dur / 1e6 AS bind_ms
  FROM android_startups AS a
  JOIN slice AS s
    ON s.name = 'bindApplication'
   AND s.ts >= a.ts AND s.ts < a.ts_end
  JOIN thread_track AS tr ON tr.id = s.track_id
  JOIN thread AS t ON t.utid = tr.utid
  WHERE a.startup_type = 'cold' AND a.package = 'com.example.jetnews'
    AND t.name = 'example.jetnews'
), ranked AS (
  SELECT bind_ms, row_number() OVER (ORDER BY bind_ms) AS rank, count(*) OVER () AS n
  FROM binds
)
SELECT count(*) AS cold_starts, min(bind_ms) AS min_bind_ms,
       max(bind_ms) AS max_bind_ms,
       (SELECT bind_ms FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms
FROM binds;
```

### c3. The representative current startup has a 1108.132709 ms bindApplication slice on the app's example.jetnews thread and includes the JetnewsApplication class slice; the corresponding baseline startup's bindApplication slice is 352.332917 ms.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH startup AS (SELECT ts, ts_end FROM android_startups WHERE startup_id = 176)
SELECT s.name, s.dur / 1e6 AS dur_ms, s.depth
FROM slice AS s
JOIN thread_track AS tr ON tr.id = s.track_id
JOIN thread AS t ON t.utid = tr.utid
WHERE t.name = 'example.jetnews'
  AND s.ts >= (SELECT ts FROM startup)
  AND s.ts < (SELECT ts_end FROM startup)
  AND s.name IN ('bindApplication', 'Startup', 'makeApplication', 'Lcom/example/jetnews/JetnewsApplication;')
ORDER BY s.ts;
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH startup AS (SELECT ts, ts_end FROM android_startups WHERE startup_id = 216)
SELECT s.name, s.dur / 1e6 AS dur_ms, s.depth
FROM slice AS s
JOIN thread_track AS tr ON tr.id = s.track_id
JOIN thread AS t ON t.utid = tr.utid
WHERE t.name = 'example.jetnews'
  AND s.ts >= (SELECT ts FROM startup)
  AND s.ts < (SELECT ts_end FROM startup)
  AND s.name IN ('bindApplication', 'Startup', 'makeApplication', 'Lcom/example/jetnews/JetnewsApplication;')
ORDER BY s.ts;
```

### c4. After the Startup slice, the current app thread spent 331.425296 ms in D state with io_wait=1; the baseline post-Startup interval has no D/io_wait state.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH startup AS (SELECT ts, ts_end FROM android_startups WHERE startup_id = 176), bind AS (
  SELECT s.ts, s.ts + s.dur AS end_ts, tr.utid
  FROM slice AS s JOIN thread_track AS tr ON tr.id = s.track_id
  JOIN startup ON s.ts >= startup.ts AND s.ts < startup.ts_end
  WHERE s.name = 'bindApplication' LIMIT 1
), startup_slice AS (
  SELECT s.ts + s.dur AS after_ts
  FROM slice AS s JOIN bind ON s.track_id = (SELECT track_id FROM slice WHERE name='bindApplication' AND ts=bind.ts LIMIT 1)
  WHERE s.name='Startup' AND s.ts >= bind.ts AND s.ts < bind.end_ts LIMIT 1
)
SELECT thread_state.state, thread_state.io_wait, count(*) AS intervals,
       sum(max(0, min(thread_state.ts + thread_state.dur, bind.end_ts) - max(thread_state.ts, startup_slice.after_ts))) / 1e6 AS overlap_ms
FROM thread_state JOIN bind ON thread_state.utid=bind.utid CROSS JOIN startup_slice
WHERE thread_state.ts < bind.end_ts AND thread_state.ts + thread_state.dur > startup_slice.after_ts
GROUP BY thread_state.state, thread_state.io_wait
ORDER BY overlap_ms DESC;
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH startup AS (SELECT ts, ts_end FROM android_startups WHERE startup_id = 216), bind AS (
  SELECT s.ts, s.ts + s.dur AS end_ts, tr.utid
  FROM slice AS s JOIN thread_track AS tr ON tr.id = s.track_id
  JOIN startup ON s.ts >= startup.ts AND s.ts < startup.ts_end
  WHERE s.name = 'bindApplication' LIMIT 1
), startup_slice AS (
  SELECT s.ts + s.dur AS after_ts
  FROM slice AS s JOIN bind ON s.track_id = (SELECT track_id FROM slice WHERE name='bindApplication' AND ts=bind.ts LIMIT 1)
  WHERE s.name='Startup' AND s.ts >= bind.ts AND s.ts < bind.end_ts LIMIT 1
)
SELECT thread_state.state, thread_state.io_wait, count(*) AS intervals,
       sum(max(0, min(thread_state.ts + thread_state.dur, bind.end_ts) - max(thread_state.ts, startup_slice.after_ts))) / 1e6 AS overlap_ms
FROM thread_state JOIN bind ON thread_state.utid=bind.utid CROSS JOIN startup_slice
WHERE thread_state.ts < bind.end_ts AND thread_state.ts + thread_state.dur > startup_slice.after_ts
GROUP BY thread_state.state, thread_state.io_wait
ORDER BY overlap_ms DESC;
```

### c5. CRC32-related JIT slices occur during the current representative startup—six slices totaling 0.307125 ms—while the corresponding baseline startup has none.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH s AS (SELECT ts, ts_end FROM android_startups WHERE startup_id=176)
SELECT count(*) AS crc32_slices_in_startup,
       min(ts) AS first_ts, max(ts) AS last_ts,
       coalesce(sum(dur),0) / 1e6 AS total_ms
FROM slice
WHERE name GLOB '*CRC32*'
  AND ts >= (SELECT ts FROM s) AND ts < (SELECT ts_end FROM s);
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH s AS (SELECT ts, ts_end FROM android_startups WHERE startup_id=216)
SELECT count(*) AS crc32_slices_in_startup,
       min(ts) AS first_ts, max(ts) AS last_ts,
       sum(dur) / 1e6 AS total_ms
FROM slice
WHERE name GLOB '*CRC32*'
  AND ts >= (SELECT ts FROM s) AND ts < (SELECT ts_end FROM s);
```

### c6. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 changes JetnewsApplication.kt so onCreate calls verifyArticleCache(), which can write a 768 MiB cache file and then read it through CRC32; head blame assigns these added lines to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This compares one baseline capture with one current capture, although each TTID value is a median over 20 cold starts; run-to-run noise is not independently estimated.
- Current run metadata reports a debuggable debug build on an sdk_gphone64_arm64 emulator running SDK 36, so production-device impact may differ.
- The trace exposes the launch I/O state and CRC32/JIT activity but does not contain a named verifyArticleCache slice.

## Dropped claims

### c1. Median cold-start TTID increased from 839.504417 ms in the baseline to 1596.432376 ms in the current trace, a 756.927959 ms regression.

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

`gpt-5.6-luna` on openai, effort xhigh: 73 tool calls, $0.0693, 698 s.
Tokens: 75 input, 1,090,133 cache read, 82,446 cache write, 22,400 output.
