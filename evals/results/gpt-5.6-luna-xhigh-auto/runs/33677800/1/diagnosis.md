# Inconclusive

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 14 of 14 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 839.5 | 854.85 | +15.35 |

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

### c1. Median cold-start TTID increased from 839.504417 ms to 854.851167 ms across 20 starts per trace, a delta of 15.346750000000043 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold WHERE ns IS NOT NULL
)
SELECT count(*) AS cold_start_count,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_ttid_ms
FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold WHERE ns IS NOT NULL
)
SELECT count(*) AS cold_start_count,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_ttid_ms
FROM ranked
```

### c2. The distribution does not show a broad tail regression: the 75th percentile is 860.496126 ms in baseline and 860.762792 ms in current, although the median differs.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold WHERE ns IS NOT NULL
)
SELECT count(*) AS cold_start_count,
       min(ns) / 1e6 AS min_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 3) / 4) AS p25_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (3 * n + 3) / 4) AS p75_ttid_ms,
       max(ns) / 1e6 AS max_ttid_ms
FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold WHERE ns IS NOT NULL
)
SELECT count(*) AS cold_start_count,
       min(ns) / 1e6 AS min_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 3) / 4) AS p25_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (3 * n + 3) / 4) AS p75_ttid_ms,
       max(ns) / 1e6 AS max_ttid_ms
FROM ranked
```

### c3. The localized activity is the Jetnews main thread, named example.jetnews. Current startup slices have 1305.409711 ms in clientTransactionExecuted versus 1079.641335 ms in baseline, while bindApplication decreases from 7234.161254 ms to 6554.871669 ms; this does not identify a changed app source method.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT s.startup_id, s.ts, s.ts_end, p.upid
  FROM android_startups AS s
  JOIN android_startup_processes AS p USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), main AS (
  SELECT DISTINCT st.startup_id, st.ts, st.ts_end, st.upid, t.utid, t.name AS thread_name
  FROM starts AS st
  JOIN thread AS t ON t.upid = st.upid
  WHERE t.is_main_thread
), slices AS (
  SELECT m.startup_id, m.thread_name, s.name, s.dur
  FROM main AS m
  JOIN thread_track AS tt ON tt.utid = m.utid
  JOIN slice AS s ON s.track_id = tt.id
  WHERE s.ts >= m.ts AND s.ts < m.ts_end AND s.depth = 0 AND s.dur > 0
)
SELECT thread_name, count(DISTINCT startup_id) AS cold_starts,
       sum(CASE WHEN name = 'bindApplication' THEN dur ELSE 0 END) / 1e6 AS bind_application_ms,
       sum(CASE WHEN name = 'clientTransactionExecuted' THEN dur ELSE 0 END) / 1e6 AS client_transaction_ms,
       sum(CASE WHEN name = 'ActivityThreadMain' THEN dur ELSE 0 END) / 1e6 AS activity_thread_main_ms
FROM slices
GROUP BY thread_name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT s.startup_id, s.ts, s.ts_end, p.upid
  FROM android_startups AS s
  JOIN android_startup_processes AS p USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), main AS (
  SELECT DISTINCT st.startup_id, st.ts, st.ts_end, st.upid, t.utid, t.name AS thread_name
  FROM starts AS st
  JOIN thread AS t ON t.upid = st.upid
  WHERE t.is_main_thread
), slices AS (
  SELECT m.startup_id, m.thread_name, s.name, s.dur
  FROM main AS m
  JOIN thread_track AS tt ON tt.utid = m.utid
  JOIN slice AS s ON s.track_id = tt.id
  WHERE s.ts >= m.ts AND s.ts < m.ts_end AND s.depth = 0 AND s.dur > 0
)
SELECT thread_name, count(DISTINCT startup_id) AS cold_starts,
       sum(CASE WHEN name = 'bindApplication' THEN dur ELSE 0 END) / 1e6 AS bind_application_ms,
       sum(CASE WHEN name = 'clientTransactionExecuted' THEN dur ELSE 0 END) / 1e6 AS client_transaction_ms,
       sum(CASE WHEN name = 'ActivityThreadMain' THEN dur ELSE 0 END) / 1e6 AS activity_thread_main_ms
FROM slices
GROUP BY thread_name
```

### c4. The range changes a topic-selection button size and a widget refresh interval; blame assigns those lines to 3e2fdaf2216b048731671bb61bd0fe7d2f2372a8 and 432218a1e58c49007d18fae8bd3d76fa40b57272 respectively. The MainActivity change is a variable rename.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
```

Commit, changing `app/src/main/res/values/integers.xml`:

```text
432218a1e58c49007d18fae8bd3d76fa40b57272
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/MainActivity.kt`:

```text
c2c776e1f353e8994eb20a2d1c17589fe789df9a
```

### c5. The median TTID increase is therefore not attributable to a specific commit in this range; the observed change is consistent with capture-to-capture startup noise rather than an established range regression.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold WHERE ns IS NOT NULL
)
SELECT count(*) AS cold_start_count,
       min(ns) / 1e6 AS min_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 3) / 4) AS p25_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (3 * n + 3) / 4) AS p75_ttid_ms,
       max(ns) / 1e6 AS max_ttid_ms
FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold WHERE ns IS NOT NULL
)
SELECT count(*) AS cold_start_count,
       min(ns) / 1e6 AS min_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 3) / 4) AS p25_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_ttid_ms,
       (SELECT ns / 1e6 FROM ranked WHERE rank = (3 * n + 3) / 4) AS p75_ttid_ms,
       max(ns) / 1e6 AS max_ttid_ms
FROM ranked
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
```

Commit, changing `app/src/main/res/values/integers.xml`:

```text
432218a1e58c49007d18fae8bd3d76fa40b57272
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/MainActivity.kt`:

```text
c2c776e1f353e8994eb20a2d1c17589fe789df9a
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one baseline capture and one current capture are available; the traces contain 20 cold starts each, but cross-capture startup timing remains noisy.
- The current run is a debuggable debug build on the sdk_gphone64_arm64 emulator (SDK 36), which limits confidence in small timing differences.
- The trace localization reaches top-level startup slices and the main thread, not a source line or a uniquely identified application method.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 75 tool calls, $0.0469, 440 s.
Tokens: 60 input, 457,193 cache read, 50,868 cache write, 20,883 output.
