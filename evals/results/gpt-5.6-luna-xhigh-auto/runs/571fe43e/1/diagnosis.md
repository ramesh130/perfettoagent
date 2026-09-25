# Inconclusive

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 9 of 9 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttfd_ms` | ms | 2,077.31 | 2,282.74 | +205.43 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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

### c1. Cold-start time to full display was higher in the current trace: 2077.310959 ms in baseline versus 2282.739626 ms in current, a delta of 205.428667 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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
    SELECT s.package, d.time_to_full_display AS ns
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

### c2. The difference localizes to the media path after application startup: within the cold-start-to-TTFD windows, baseline contains 49 load:HlsMediaChunk slices totaling 5818.853 ms, while current contains 61 totaling 7831.68 ms. The reportFullyDrawn markers occur on the app's main thread 20 times in each trace.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold' AND s.package = 'com.superplayer.demo'
), app_threads AS (
  SELECT t.utid
  FROM thread AS t
  JOIN process AS p USING (upid)
  WHERE p.name = 'com.superplayer.demo'
)
SELECT sl.name, th.name AS thread_name, count(*) AS slice_count,
       round(sum(sl.dur) / 1e6, 3) AS total_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS th ON th.utid = tr.utid
JOIN app_threads AS at ON at.utid = th.utid
JOIN cold AS c ON sl.ts < c.ts + c.ttfd AND sl.ts + sl.dur > c.ts
WHERE sl.name IN ('load:HlsMediaChunk', 'reportFullyDrawn() for ComponentActivity', 'reportFullyDrawn() for {com.superplayer.demo/com.superplayer.demo.MainActivity}')
GROUP BY sl.name, th.name
ORDER BY sl.name, th.name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold' AND s.package = 'com.superplayer.demo'
), app_threads AS (
  SELECT t.utid
  FROM thread AS t
  JOIN process AS p USING (upid)
  WHERE p.name = 'com.superplayer.demo'
)
SELECT sl.name, th.name AS thread_name, count(*) AS slice_count,
       round(sum(sl.dur) / 1e6, 3) AS total_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS th ON th.utid = tr.utid
JOIN app_threads AS at ON at.utid = th.utid
JOIN cold AS c ON sl.ts < c.ts + c.ttfd AND sl.ts + sl.dur > c.ts
WHERE sl.name IN ('load:HlsMediaChunk', 'reportFullyDrawn() for ComponentActivity', 'reportFullyDrawn() for {com.superplayer.demo/com.superplayer.demo.MainActivity}')
GROUP BY sl.name, th.name
ORDER BY sl.name, th.name
```

### c3. The range does not establish a code culprit for this media-path difference. Its MainActivity change is commit 3a78df0448d62ccd759276ff8bb3b8739be06e46, while the FeedScreen changes are 7739a7d2261a5cd2880e7ebc4384d42da4ef8a14 and 3c45fa773a148f0cd3f45cdf56318eb3dc52e6c0; none is directly connected by the trace to the increased HLS loading.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold' AND s.package = 'com.superplayer.demo'
), app_threads AS (
  SELECT t.utid
  FROM thread AS t
  JOIN process AS p USING (upid)
  WHERE p.name = 'com.superplayer.demo'
)
SELECT sl.name, th.name AS thread_name, count(*) AS slice_count,
       round(sum(sl.dur) / 1e6, 3) AS total_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS th ON th.utid = tr.utid
JOIN app_threads AS at ON at.utid = th.utid
JOIN cold AS c ON sl.ts < c.ts + c.ttfd AND sl.ts + sl.dur > c.ts
WHERE sl.name IN ('load:HlsMediaChunk', 'reportFullyDrawn() for ComponentActivity', 'reportFullyDrawn() for {com.superplayer.demo/com.superplayer.demo.MainActivity}')
GROUP BY sl.name, th.name
ORDER BY sl.name, th.name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.startup_type = 'cold' AND s.package = 'com.superplayer.demo'
), app_threads AS (
  SELECT t.utid
  FROM thread AS t
  JOIN process AS p USING (upid)
  WHERE p.name = 'com.superplayer.demo'
)
SELECT sl.name, th.name AS thread_name, count(*) AS slice_count,
       round(sum(sl.dur) / 1e6, 3) AS total_ms
FROM slice AS sl
JOIN thread_track AS tr ON tr.id = sl.track_id
JOIN thread AS th ON th.utid = tr.utid
JOIN app_threads AS at ON at.utid = th.utid
JOIN cold AS c ON sl.ts < c.ts + c.ttfd AND sl.ts + sl.dur > c.ts
WHERE sl.name IN ('load:HlsMediaChunk', 'reportFullyDrawn() for ComponentActivity', 'reportFullyDrawn() for {com.superplayer.demo/com.superplayer.demo.MainActivity}')
GROUP BY sl.name, th.name
ORDER BY sl.name, th.name
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MainActivity.kt`:

```text
3a78df0448d62ccd759276ff8bb3b8739be06e46
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7739a7d2261a5cd2880e7ebc4384d42da4ef8a14
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
3c45fa773a148f0cd3f45cdf56318eb3dc52e6c0
```

## Caveats

- Only one capture is available for each build, so the TTFD and HLS/network timing difference cannot be separated from run-to-run noise.
- The current run metadata identifies an emulator benchmark build; TTFD includes the media loading and rendering pipeline, not just application initialization.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 61 tool calls, $0.0542, 345 s.
Tokens: 36 input, 486,204 cache read, 89,871 cache write, 18,328 output.
