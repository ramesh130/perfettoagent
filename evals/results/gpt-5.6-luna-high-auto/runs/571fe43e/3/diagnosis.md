# Regression

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** `d3c08a36dc94` (correlated); `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** medium (never scored)

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

### c1. Median cold-start TTFD increased from 2077.310959 ms over 20 starts in baseline to 2282.739626 ms over 20 starts in current, a 205.428667 ms regression.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH ranked AS (
 SELECT d.time_to_full_display/1e6 AS ttfd_ms,
        row_number() OVER (ORDER BY d.time_to_full_display) AS r,
        count(*) OVER () AS n
 FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
 WHERE s.startup_type='cold'
)
SELECT count(*) AS cold_starts, min(ttfd_ms) AS min_ttfd_ms, max(ttfd_ms) AS max_ttfd_ms,
       (SELECT ttfd_ms FROM ranked WHERE r=(n+1)/2) AS median_ttfd_ms
FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH ranked AS (
 SELECT d.time_to_full_display/1e6 AS ttfd_ms,
        row_number() OVER (ORDER BY d.time_to_full_display) AS r,
        count(*) OVER () AS n
 FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
 WHERE s.startup_type='cold'
)
SELECT count(*) AS cold_starts, min(ttfd_ms) AS min_ttfd_ms, max(ttfd_ms) AS max_ttfd_ms,
       (SELECT ttfd_ms FROM ranked WHERE r=(n+1)/2) AS median_ttfd_ms
FROM ranked
```

### c2. The regression is localized to the app's main-thread UI work during the startup-to-full-display interval: traversal increased from 6985.105894 ms to 9086.851044 ms across the 20 starts, while draw-VRI[MainActivity] increased from 4735.372619 ms to 6804.722472 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
 SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
 FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
 WHERE s.startup_type='cold'
), main_slices AS (
 SELECT c.startup_id, sum(CASE WHEN sl.name='traversal' THEN sl.dur ELSE 0 END)/1e6 AS traversal_ms,
        sum(CASE WHEN sl.name='draw-VRI[MainActivity]' THEN sl.dur ELSE 0 END)/1e6 AS draw_ms
 FROM cold c JOIN process p ON p.name='com.superplayer.demo' AND p.start_ts<c.ts+c.ttfd/1.0 AND (p.end_ts IS NULL OR p.end_ts>c.ts)
 JOIN thread t ON t.upid=p.upid AND t.tid=p.pid JOIN thread_track tt ON tt.utid=t.utid JOIN slice sl ON sl.track_id=tt.id
 WHERE sl.ts>=c.ts AND sl.ts<c.ts+c.ttfd GROUP BY c.startup_id
)
SELECT count(*) AS starts, sum(traversal_ms) AS traversal_total_ms, sum(draw_ms) AS draw_total_ms FROM main_slices
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
 SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
 FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
 WHERE s.startup_type='cold'
), main_slices AS (
 SELECT c.startup_id, sum(CASE WHEN sl.name='traversal' THEN sl.dur ELSE 0 END)/1e6 AS traversal_ms,
        sum(CASE WHEN sl.name='draw-VRI[MainActivity]' THEN sl.dur ELSE 0 END)/1e6 AS draw_ms
 FROM cold c JOIN process p ON p.name='com.superplayer.demo' AND p.start_ts<c.ts+c.ttfd/1.0 AND (p.end_ts IS NULL OR p.end_ts>c.ts)
 JOIN thread t ON t.upid=p.upid AND t.tid=p.pid JOIN thread_track tt ON tt.utid=t.utid JOIN slice sl ON sl.track_id=tt.id
 WHERE sl.ts>=c.ts AND sl.ts<c.ts+c.ttfd GROUP BY c.startup_id
)
SELECT count(*) AS starts, sum(traversal_ms) AS traversal_total_ms, sum(draw_ms) AS draw_total_ms FROM main_slices
```

### c3. d3c08a36dc94946928b95e758595f66aa083b2cd is the correlated culprit: it changed the DownloadsScreen DownloadRow layout padding, and the trace shows substantially more Compose traversal and MainActivity drawing during startup. The trace does not identify DownloadRow directly, so this attribution is correlated rather than direct.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
d3c08a36dc94946928b95e758595f66aa083b2cd
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
 SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
 FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
 WHERE s.startup_type='cold'
), main_slices AS (
 SELECT c.startup_id, sum(CASE WHEN sl.name='traversal' THEN sl.dur ELSE 0 END)/1e6 AS traversal_ms,
        sum(CASE WHEN sl.name='draw-VRI[MainActivity]' THEN sl.dur ELSE 0 END)/1e6 AS draw_ms
 FROM cold c JOIN process p ON p.name='com.superplayer.demo' AND p.start_ts<c.ts+c.ttfd/1.0 AND (p.end_ts IS NULL OR p.end_ts>c.ts)
 JOIN thread t ON t.upid=p.upid AND t.tid=p.pid JOIN thread_track tt ON tt.utid=t.utid JOIN slice sl ON sl.track_id=tt.id
 WHERE sl.ts>=c.ts AND sl.ts<c.ts+c.ttfd GROUP BY c.startup_id
)
SELECT count(*) AS starts, sum(traversal_ms) AS traversal_total_ms, sum(draw_ms) AS draw_total_ms FROM main_slices
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
 SELECT s.startup_id, s.ts, d.time_to_full_display AS ttfd
 FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
 WHERE s.startup_type='cold'
), main_slices AS (
 SELECT c.startup_id, sum(CASE WHEN sl.name='traversal' THEN sl.dur ELSE 0 END)/1e6 AS traversal_ms,
        sum(CASE WHEN sl.name='draw-VRI[MainActivity]' THEN sl.dur ELSE 0 END)/1e6 AS draw_ms
 FROM cold c JOIN process p ON p.name='com.superplayer.demo' AND p.start_ts<c.ts+c.ttfd/1.0 AND (p.end_ts IS NULL OR p.end_ts>c.ts)
 JOIN thread t ON t.upid=p.upid AND t.tid=p.pid JOIN thread_track tt ON tt.utid=t.utid JOIN slice sl ON sl.track_id=tt.id
 WHERE sl.ts>=c.ts AND sl.ts<c.ts+c.ttfd GROUP BY c.startup_id
)
SELECT count(*) AS starts, sum(traversal_ms) AS traversal_total_ms, sum(draw_ms) AS draw_total_ms FROM main_slices
```

## Caveats

- Both sides are single emulator captures on sdk_gphone64_arm64 with 20 cold starts each; TTFD includes rendering and system-pipeline effects.
- The trace exposes generic traversal and draw slices, not a DownloadRow-specific slice or app callstack, so the commit attribution remains correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 86 tool calls, $0.0802, 544 s.
Tokens: 78 input, 1,595,584 cache read, 100,051 cache write, 19,371 output.
