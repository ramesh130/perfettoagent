# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 37.95 | 69.29 | +31.34 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c1. The requested UI-time p95 increased from 37.952167 ms to 69.289541 ms, a 31.337373999999997 ms regression.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

### c2. The app's frame work shifted primarily into longer traversal slices: average traversal time rose from 8.55789081923715 ms to 24.1324418421673 ms, with the maximum rising from 77.021958 ms to 101.274292 ms.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  s.name,
  count(*) AS occurrences,
  sum(s.dur) / 1e6 AS total_ms,
  avg(s.dur) / 1e6 AS avg_ms,
  max(s.dur) / 1e6 AS max_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS f ON f.id = d.id
JOIN slice AS s ON s.parent_id = f.id
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo' AND s.name IN ('traversal', 'animation', 'input')
GROUP BY s.name
ORDER BY s.name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  s.name,
  count(*) AS occurrences,
  sum(s.dur) / 1e6 AS total_ms,
  avg(s.dur) / 1e6 AS avg_ms,
  max(s.dur) / 1e6 AS max_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS f ON f.id = d.id
JOIN slice AS s ON s.parent_id = f.id
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.superplayer.demo' AND s.name IN ('traversal', 'animation', 'input')
GROUP BY s.name
ORDER BY s.name
```

### c3. The strongest localized change is text layout: TextLayout:initLayout grew from 288 occurrences and 69.199128 ms total in the baseline to 1,859,699 occurrences and 7,192.994139 ms total in the current trace.

The `baseline` trace: 50 rows.

```sql
SELECT sl.name AS slice_name, count(*) AS occurrences, sum(sl.dur) / 1e6 AS total_ms, max(sl.dur) / 1e6 AS max_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS pr ON pr.upid = th.upid
WHERE pr.name = 'com.superplayer.demo'
  AND (sl.name GLOB '*RowTitle*' OR sl.name GLOB '*measure*' OR sl.name GLOB '*Text*' OR sl.name GLOB '*Compose*')
GROUP BY sl.name
ORDER BY total_ms DESC
LIMIT 50
```

The `current` trace: 50 rows.

```sql
SELECT sl.name AS slice_name, count(*) AS occurrences, sum(sl.dur) / 1e6 AS total_ms, max(sl.dur) / 1e6 AS max_ms
FROM slice AS sl
JOIN thread_track AS tt ON sl.track_id = tt.id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS pr ON pr.upid = th.upid
WHERE pr.name = 'com.superplayer.demo'
  AND (sl.name GLOB '*RowTitle*' OR sl.name GLOB '*measure*' OR sl.name GLOB '*Text*' OR sl.name GLOB '*Compose*')
GROUP BY sl.name
ORDER BY total_ms DESC
LIMIT 50
```

### c4. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 introduced both the RowTitle text-measurement loop and the continuously animated row padding in FeedScreen.kt; the trace's text-layout and traversal increase directly matches those changes.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- This conclusion is based on one capture per side, so run-to-run noise cannot be fully excluded.
- The captures run on an emulator; device scheduling and workload differences may affect absolute frame timings.

## Run

`gpt-5.6-luna` on openai, effort high: 24 tool calls, $0.0257, 102 s.
Tokens: 24 input, 139,476 cache read, 53,900 cache write, 7,861 output.
