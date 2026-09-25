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

### c1. Median cold-start time to initial display increased from 839.504417 ms in baseline to 1596.432376 ms in current, a 756.927959 ms regression.

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

### c2. The startup process is localized to bindApplication: its median duration across 20 cold starts rose from 355.057126 ms in baseline to 1108.132709 ms in current.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, d.time_to_initial_display AS ttid, d.upid
  FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, MAX(sl.dur) AS bind_dur
  FROM starts st
  JOIN thread th ON th.upid = st.upid
  JOIN thread_track tt ON tt.utid = th.utid
  JOIN slice sl ON sl.track_id = tt.id
  WHERE th.name = 'example.jetnews' AND sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttid
  GROUP BY st.startup_id
), ranked AS (
  SELECT bind_dur, ROW_NUMBER() OVER (ORDER BY bind_dur) AS rank, COUNT(*) OVER () AS n
  FROM binds
)
SELECT COUNT(*) AS cold_starts_with_bind, (SELECT bind_dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms,
       MIN(bind_dur) / 1e6 AS min_bind_ms, MAX(bind_dur) / 1e6 AS max_bind_ms
FROM binds
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, d.time_to_initial_display AS ttid, d.upid
  FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, MAX(sl.dur) AS bind_dur
  FROM starts st
  JOIN thread th ON th.upid = st.upid
  JOIN thread_track tt ON tt.utid = th.utid
  JOIN slice sl ON sl.track_id = tt.id
  WHERE th.name = 'example.jetnews' AND sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttid
  GROUP BY st.startup_id
), ranked AS (
  SELECT bind_dur, ROW_NUMBER() OVER (ORDER BY bind_dur) AS rank, COUNT(*) OVER () AS n
  FROM binds
)
SELECT COUNT(*) AS cold_starts_with_bind, (SELECT bind_dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms,
       MIN(bind_dur) / 1e6 AS min_bind_ms, MAX(bind_dur) / 1e6 AS max_bind_ms
FROM binds
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds a synchronous verifyArticleCache call to JetnewsApplication.onCreate and implements a 768 MiB cache write/checksum pass at launch; blame assigns those added lines to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. The launch cache verification is the direct explanation for the bindApplication regression: the changed code runs from JetnewsApplication.onCreate, while the trace shows the large increase in the application binding portion of startup.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, d.time_to_initial_display AS ttid, d.upid
  FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, MAX(sl.dur) AS bind_dur
  FROM starts st
  JOIN thread th ON th.upid = st.upid
  JOIN thread_track tt ON tt.utid = th.utid
  JOIN slice sl ON sl.track_id = tt.id
  WHERE th.name = 'example.jetnews' AND sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttid
  GROUP BY st.startup_id
), ranked AS (
  SELECT bind_dur, ROW_NUMBER() OVER (ORDER BY bind_dur) AS rank, COUNT(*) OVER () AS n
  FROM binds
)
SELECT COUNT(*) AS cold_starts_with_bind, (SELECT bind_dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms,
       MIN(bind_dur) / 1e6 AS min_bind_ms, MAX(bind_dur) / 1e6 AS max_bind_ms
FROM binds
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, d.time_to_initial_display AS ttid, d.upid
  FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, MAX(sl.dur) AS bind_dur
  FROM starts st
  JOIN thread th ON th.upid = st.upid
  JOIN thread_track tt ON tt.utid = th.utid
  JOIN slice sl ON sl.track_id = tt.id
  WHERE th.name = 'example.jetnews' AND sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttid
  GROUP BY st.startup_id
), ranked AS (
  SELECT bind_dur, ROW_NUMBER() OVER (ORDER BY bind_dur) AS rank, COUNT(*) OVER () AS n
  FROM binds
)
SELECT COUNT(*) AS cold_starts_with_bind, (SELECT bind_dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_ms,
       MIN(bind_dur) / 1e6 AS min_bind_ms, MAX(bind_dur) / 1e6 AS max_bind_ms
FROM binds
```

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- The evidence is from one baseline capture and one current capture, although each capture contains 20 cold starts.
- Both runs are debuggable emulator captures on sdk_gphone64_arm64, so absolute startup timings may differ from release builds or physical devices.
- The trace localizes the added cost to application binding; it does not expose a Java stack sample naming verifyArticleCache itself.

## Run

`gpt-5.6-luna` on openai, effort high: 67 tool calls, $0.0393, 642 s.
Tokens: 57 input, 428,532 cache read, 62,990 cache write, 12,454 output.
