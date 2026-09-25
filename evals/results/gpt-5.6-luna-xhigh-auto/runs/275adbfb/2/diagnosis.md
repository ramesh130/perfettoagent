# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (correlated); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 3 claims kept, 1 dropped; 9 of 10 citations passed
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

### c2. Trace localization points to application startup: the com.superplayer.demo bindApplication slice is 102.318666 ms in the baseline startup interval and 465.286959 ms in the current interval.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH startup AS (
  SELECT s.ts, s.ts_end, d.upid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_id = 66
)
SELECT p.name AS process_name, th.name AS thread_name, sl.name, sl.dur / 1e6 AS dur_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS th ON tt.utid = th.utid
JOIN process AS p ON th.upid = p.upid
CROSS JOIN startup
WHERE th.upid = startup.upid
  AND sl.ts >= startup.ts
  AND sl.ts + sl.dur <= startup.ts_end
  AND sl.name = 'bindApplication'
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH startup AS (
  SELECT s.ts, s.ts_end, d.upid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_id = 86
)
SELECT p.name AS process_name, th.name AS thread_name, sl.name, sl.dur / 1e6 AS dur_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS th ON tt.utid = th.utid
JOIN process AS p ON th.upid = p.upid
CROSS JOIN startup
WHERE th.upid = startup.upid
  AND sl.ts >= startup.ts
  AND sl.ts + sl.dur <= startup.ts_end
  AND sl.name = 'bindApplication'
```

### c3. The startup-localized query finds 20 cold starts in each trace; median bindApplication duration increased from 97.692292 ms to 465.286959 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, s.ts_end, d.upid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, sl.dur,
    row_number() OVER (PARTITION BY st.startup_id ORDER BY sl.dur DESC) AS rn
  FROM starts AS st
  JOIN slice AS sl ON sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts + sl.dur <= st.ts_end
  JOIN thread_track AS tt ON sl.track_id = tt.id
  JOIN thread AS th ON tt.utid = th.utid
  WHERE th.upid = st.upid
), one_per_start AS (
  SELECT startup_id, dur FROM binds WHERE rn = 1
), ranked AS (
  SELECT dur, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
  FROM one_per_start
)
SELECT count(*) AS startup_count,
  (SELECT dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_application_ms
FROM one_per_start
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, s.ts_end, d.upid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, sl.dur,
    row_number() OVER (PARTITION BY st.startup_id ORDER BY sl.dur DESC) AS rn
  FROM starts AS st
  JOIN slice AS sl ON sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts + sl.dur <= st.ts_end
  JOIN thread_track AS tt ON sl.track_id = tt.id
  JOIN thread AS th ON tt.utid = th.utid
  WHERE th.upid = st.upid
), one_per_start AS (
  SELECT startup_id, dur FROM binds WHERE rn = 1
), ranked AS (
  SELECT dur, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
  FROM one_per_start
)
SELECT count(*) AS startup_count,
  (SELECT dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_application_ms
FROM one_per_start
```

### c4. Commit fb30a9c67862bd42f9d8fab36f6c8dff37069417 adds DemoApplication, registers it as the app Application, and performs a catalog-cache check, possible 192 MiB rebuild, and CRC read during Application.onCreate. Together with the repeated bindApplication expansion, this makes that commit the likely cause.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, s.ts_end, d.upid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, sl.dur,
    row_number() OVER (PARTITION BY st.startup_id ORDER BY sl.dur DESC) AS rn
  FROM starts AS st
  JOIN slice AS sl ON sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts + sl.dur <= st.ts_end
  JOIN thread_track AS tt ON sl.track_id = tt.id
  JOIN thread AS th ON tt.utid = th.utid
  WHERE th.upid = st.upid
), one_per_start AS (
  SELECT startup_id, dur FROM binds WHERE rn = 1
), ranked AS (
  SELECT dur, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
  FROM one_per_start
)
SELECT count(*) AS startup_count,
  (SELECT dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_application_ms
FROM one_per_start
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH starts AS (
  SELECT s.startup_id, s.ts, s.ts_end, d.upid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold'
), binds AS (
  SELECT st.startup_id, sl.dur,
    row_number() OVER (PARTITION BY st.startup_id ORDER BY sl.dur DESC) AS rn
  FROM starts AS st
  JOIN slice AS sl ON sl.name = 'bindApplication'
    AND sl.ts >= st.ts AND sl.ts + sl.dur <= st.ts_end
  JOIN thread_track AS tt ON sl.track_id = tt.id
  JOIN thread AS th ON tt.utid = th.utid
  WHERE th.upid = st.upid
), one_per_start AS (
  SELECT startup_id, dur FROM binds WHERE rn = 1
), ranked AS (
  SELECT dur, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
  FROM one_per_start
)
SELECT count(*) AS startup_count,
  (SELECT dur / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS median_bind_application_ms
FROM one_per_start
```

## Caveats

- Only one baseline/current trace pair is available, so run-to-run noise cannot be estimated independently.
- The causal attribution is correlated rather than based on a symbolized DemoApplication stack frame; the trace evidence localizes the change to application startup lifecycle work.
- The captures run on an emulator, so absolute startup timings may not generalize to physical devices.

## Dropped claims

### c1. Cold-start TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a 315.198625 ms regression.

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

`gpt-5.6-luna` on openai, effort xhigh: 58 tool calls, $0.0459, 406 s.
Tokens: 48 input, 488,705 cache read, 56,703 cache write, 18,314 output.
