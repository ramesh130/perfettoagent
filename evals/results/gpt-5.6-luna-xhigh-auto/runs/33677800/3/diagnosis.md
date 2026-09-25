# Inconclusive

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 8 of 9 citations passed
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

### c2. Each trace contains 20 cold starts. The median shift is accompanied by overlapping ranges and a much smaller mean shift: baseline 801.601458–1006.860583 ms with mean 849.06890865 ms, versus current 818.441458–895.549625 ms with mean 852.8640378 ms. This makes run-to-run or emulator variance a plausible explanation for the median change.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.package, d.time_to_initial_display / 1e6 AS ttid_ms
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ttid_ms, row_number() OVER (ORDER BY ttid_ms) AS r, count(*) OVER () AS n
  FROM cold
)
SELECT count(*) AS cold_starts,
       min(ttid_ms) AS min_ms,
       (SELECT ttid_ms FROM ranked WHERE r = (n + 1) / 2) AS median_ms,
       avg(ttid_ms) AS mean_ms,
       max(ttid_ms) AS max_ms
FROM cold
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.package, d.time_to_initial_display / 1e6 AS ttid_ms
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.example.jetnews' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ttid_ms, row_number() OVER (ORDER BY ttid_ms) AS r, count(*) OVER () AS n
  FROM cold
)
SELECT count(*) AS cold_starts,
       min(ttid_ms) AS min_ms,
       (SELECT ttid_ms FROM ranked WHERE r = (n + 1) / 2) AS median_ms,
       avg(ttid_ms) AS mean_ms,
       max(ttid_ms) AS max_ms
FROM cold
```

### c3. The startup localization shows more time overlapping clientTransactionExecuted in the current trace (1305.409711 ms across the starts versus 1079.641335 ms baseline), while Compose:recompose and Compose:initializeView are both lower in the current trace. The trace therefore points to framework transaction/startup variance rather than increased measured Compose work.

The `baseline` trace: 50 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT startup_id, ts, ts_end
  FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
), main_tracks AS (
  SELECT s.startup_id, s.ts, s.ts_end, tt.id AS track_id
  FROM starts AS s
  JOIN process AS p ON p.name = 'com.example.jetnews'
    AND p.start_ts >= s.ts AND p.start_ts < s.ts_end
  JOIN thread AS t ON t.upid = p.upid AND t.tid = p.pid
  JOIN thread_track AS tt ON tt.utid = t.utid
)
SELECT sl.name, sl.depth, count(*) AS occurrences,
       sum(min(sl.ts + sl.dur, mt.ts_end) - max(sl.ts, mt.ts)) / 1e6 AS clipped_ms
FROM main_tracks AS mt
JOIN slice AS sl ON sl.track_id = mt.track_id
WHERE sl.dur > 0 AND sl.ts < mt.ts_end AND mt.ts < sl.ts + sl.dur
GROUP BY sl.name, sl.depth
ORDER BY clipped_ms DESC
LIMIT 50
```

The `current` trace: 50 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT startup_id, ts, ts_end
  FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
), main_tracks AS (
  SELECT s.startup_id, s.ts, s.ts_end, tt.id AS track_id
  FROM starts AS s
  JOIN process AS p ON p.name = 'com.example.jetnews'
    AND p.start_ts >= s.ts AND p.start_ts < s.ts_end
  JOIN thread AS t ON t.upid = p.upid AND t.tid = p.pid
  JOIN thread_track AS tt ON tt.utid = t.utid
)
SELECT sl.name, sl.depth, count(*) AS occurrences,
       sum(min(sl.ts + sl.dur, mt.ts_end) - max(sl.ts, mt.ts)) / 1e6 AS clipped_ms
FROM main_tracks AS mt
JOIN slice AS sl ON sl.track_id = mt.track_id
WHERE sl.dur > 0 AND sl.ts < mt.ts_end AND mt.ts < sl.ts + sl.dur
GROUP BY sl.name, sl.depth
ORDER BY clipped_ms DESC
LIMIT 50
```

### c4. The two range commits that modify the localized UI areas change InterestsScreen thumbnail sizing from 56 dp to 48 dp and SelectTopicButton sizing from 36 dp to 40 dp; neither change is directly represented by the startup slice names above.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
```

The `current` trace: 50 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
WITH starts AS (
  SELECT startup_id, ts, ts_end
  FROM android_startups
  WHERE package = 'com.example.jetnews' AND startup_type = 'cold'
), main_tracks AS (
  SELECT s.startup_id, s.ts, s.ts_end, tt.id AS track_id
  FROM starts AS s
  JOIN process AS p ON p.name = 'com.example.jetnews'
    AND p.start_ts >= s.ts AND p.start_ts < s.ts_end
  JOIN thread AS t ON t.upid = p.upid AND t.tid = p.pid
  JOIN thread_track AS tt ON tt.utid = t.utid
)
SELECT sl.name, sl.depth, count(*) AS occurrences,
       sum(min(sl.ts + sl.dur, mt.ts_end) - max(sl.ts, mt.ts)) / 1e6 AS clipped_ms
FROM main_tracks AS mt
JOIN slice AS sl ON sl.track_id = mt.track_id
WHERE sl.dur > 0 AND sl.ts < mt.ts_end AND mt.ts < sl.ts + sl.dur
GROUP BY sl.name, sl.depth
ORDER BY clipped_ms DESC
LIMIT 50
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one trace per build, even though each trace contains 20 startup iterations, so the 15.35 ms median difference cannot be separated confidently from capture and emulator variance.
- The current run is a debuggable debug build on the sdk_gphone64_arm64 emulator; baseline build metadata was not recorded.
- TTFD was unavailable in both traces, so the diagnosis is limited to time to initial display.

## Dropped claims

### c1. Cold-start TTID for com.example.jetnews increased from 839.504417 ms in the baseline to 854.851167 ms in the current trace, a delta of 15.34675 ms.

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

`gpt-5.6-luna` on openai, effort xhigh: 64 tool calls, $0.0382, 391 s.
Tokens: 60 input, 335,226 cache read, 44,222 cache write, 17,044 output.
