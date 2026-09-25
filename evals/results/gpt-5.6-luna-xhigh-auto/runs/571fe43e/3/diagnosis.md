# Inconclusive

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 11 of 11 citations passed
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

### c1. Median cold-start TTFD increased from 2077.310959 ms in the baseline to 2282.739626 ms in the current trace, a delta of 205.428667 ms.

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

### c2. TTID did not worsen alongside TTFD: its median was 349.682708 ms in the baseline and 345.470333 ms in the current trace, so the difference occurs after initial display.

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

### c3. The trace localizes the additional pre-first-frame work to the app's ExoPlayer loader: load:HlsMediaChunk totaled 37316.231146 ms in the baseline versus 39330.926774 ms in the current trace, with the maximum slice increasing from 285.387625 ms to 595.341209 ms.

The `baseline` trace: 2 rows.

```sql
SELECT sl.name, p.name AS process_name, t.name AS thread_name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON tt.id=sl.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE sl.name IN ('load:HlsMediaChunk','load:ParsingLoadable') AND p.name='com.superplayer.demo'
GROUP BY sl.name, p.name, t.name ORDER BY sl.name, total_ms DESC
```

The `current` trace: 2 rows.

```sql
SELECT sl.name, p.name AS process_name, t.name AS thread_name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON tt.id=sl.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE sl.name IN ('load:HlsMediaChunk','load:ParsingLoadable') AND p.name='com.superplayer.demo'
GROUP BY sl.name, p.name, t.name ORDER BY sl.name, total_ms DESC
```

### c4. The individual cold-start TTFD values vary and overlap between the two traces, so the median shift is not sufficient to distinguish a code regression from media or emulator run-to-run noise.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.ts, s.ts_end, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms, d.ttid_frame_id, d.ttfd_frame_id, d.upid
FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.startup_id
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.ts, s.ts_end, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms, d.ttid_frame_id, d.ttfd_frame_id, d.upid
FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id)
WHERE s.startup_type = 'cold'
ORDER BY s.startup_id
```

### c5. The range's FeedScreen changes are confined to the player-acquisition refactor and the main-thread-handler rename; the trace exposes HLS loader slices but no changed app method or source-line frame, so no in-range commit can be defensibly attributed as the culprit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7739a7d2261a5cd2880e7ebc4384d42da4ef8a14
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
3c45fa773a148f0cd3f45cdf56318eb3dc52e6c0
```

The `current` trace: 2 rows.

```sql
SELECT sl.name, p.name AS process_name, t.name AS thread_name, count(*) AS slices, sum(sl.dur)/1e6 AS total_ms, max(sl.dur)/1e6 AS max_ms
FROM slice sl JOIN thread_track tt ON tt.id=sl.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE sl.name IN ('load:HlsMediaChunk','load:ParsingLoadable') AND p.name='com.superplayer.demo'
GROUP BY sl.name, p.name, t.name ORDER BY sl.name, total_ms DESC
```

## Caveats

- Only one baseline/current capture pair is available; the traces contain multiple cold starts, but HLS and emulator timing remain noisy.
- The current build is a non-debuggable benchmark build on an sdk_gphone64_arm64 emulator; baseline build metadata was not recorded.
- The trace localizes work to slices and threads, not source lines or a sampled app callstack.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 95 tool calls, $0.0903, 469 s.
Tokens: 72 input, 1,532,974 cache read, 120,822 cache write, 24,496 output.
