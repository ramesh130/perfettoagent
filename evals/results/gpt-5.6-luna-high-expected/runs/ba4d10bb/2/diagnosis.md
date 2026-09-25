# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (direct); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. Cold-start median TTID increased from 839.504417 ms in the baseline to 1596.432376 ms in the current trace, a 756.927959 ms regression.

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

### c2. The regression is localized to the app's main thread during bindApplication: across 20 cold starts, average bindApplication duration increased from 361.7080627 ms to 1138.5053027 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH cold AS (
 SELECT startup_id, ts, ts_end FROM android_startups WHERE startup_type='cold' AND package='com.example.jetnews'
), binds AS (
 SELECT c.startup_id, s.dur FROM cold c JOIN slice s ON s.ts >= c.ts AND s.ts < c.ts_end
 JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid JOIN process p ON p.upid=th.upid
 WHERE p.name='com.example.jetnews' AND th.name='example.jetnews' AND s.name='bindApplication'
)
SELECT count(*) AS bind_count, min(dur)/1e6 AS min_bind_ms, max(dur)/1e6 AS max_bind_ms, avg(dur)/1e6 AS avg_bind_ms
FROM binds
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH cold AS (
 SELECT startup_id, ts, ts_end FROM android_startups WHERE startup_type='cold' AND package='com.example.jetnews'
), binds AS (
 SELECT c.startup_id, s.dur FROM cold c JOIN slice s ON s.ts >= c.ts AND s.ts < c.ts_end
 JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid JOIN process p ON p.upid=th.upid
 WHERE p.name='com.example.jetnews' AND th.name='example.jetnews' AND s.name='bindApplication'
)
SELECT count(*) AS bind_count, min(dur)/1e6 AS min_bind_ms, max(dur)/1e6 AS max_bind_ms, avg(dur)/1e6 AS avg_bind_ms
FROM binds
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() directly to JetnewsApplication.onCreate() before AppContainerImpl is constructed; the method may create a 768 MiB cache file and then read it to compute a CRC32.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. The startup timing increase is directly attributed to bea44a9561ce48b23fc6102f729f1c78d49b2af5: the commit's newly added synchronous application-start work matches the large increase in bindApplication duration.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH cold AS (
 SELECT startup_id, ts, ts_end FROM android_startups WHERE startup_type='cold' AND package='com.example.jetnews'
), binds AS (
 SELECT c.startup_id, s.dur FROM cold c JOIN slice s ON s.ts >= c.ts AND s.ts < c.ts_end
 JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid JOIN process p ON p.upid=th.upid
 WHERE p.name='com.example.jetnews' AND th.name='example.jetnews' AND s.name='bindApplication'
)
SELECT count(*) AS bind_count, min(dur)/1e6 AS min_bind_ms, max(dur)/1e6 AS max_bind_ms, avg(dur)/1e6 AS avg_bind_ms
FROM binds
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH cold AS (
 SELECT startup_id, ts, ts_end FROM android_startups WHERE startup_type='cold' AND package='com.example.jetnews'
), binds AS (
 SELECT c.startup_id, s.dur FROM cold c JOIN slice s ON s.ts >= c.ts AND s.ts < c.ts_end
 JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid JOIN process p ON p.upid=th.upid
 WHERE p.name='com.example.jetnews' AND th.name='example.jetnews' AND s.name='bindApplication'
)
SELECT count(*) AS bind_count, min(dur)/1e6 AS min_bind_ms, max(dur)/1e6 AS max_bind_ms, avg(dur)/1e6 AS avg_bind_ms
FROM binds
```

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one baseline capture and one current capture, although each contains 20 cold starts.
- Both the recorded current build and device metadata identify a debuggable debug build running on an emulator, so absolute timings may not represent release hardware performance.

## Run

`gpt-5.6-luna` on openai, effort high: 35 tool calls, $0.0265, 164 s.
Tokens: 51 input, 313,852 cache read, 35,153 cache write, 9,545 output.
