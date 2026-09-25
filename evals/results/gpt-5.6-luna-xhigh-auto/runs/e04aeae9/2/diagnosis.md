# No regression

- **Metric:** `frame_ui_time_p95_ms` -0.83 ms (26.55 → 25.72 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 1 dropped; 13 of 14 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.55 | 25.72 | -0.83 |

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

### c1. The selected app-side metric improved: UI-frame p95 fell from 26.550666 ms in the baseline to 25.719583 ms in the current trace, a delta of -0.8310829999999996 ms.

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

### c2. The frame owner is the same in both captures: process com.example.jetnews and UI thread example.jetnews, with upid/utid 365.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT DISTINCT p.name AS process_name, t.name AS thread_name, p.upid, t.utid
FROM process AS p
JOIN thread AS t USING (upid)
JOIN android_frames_layers AS f ON f.upid = p.upid AND f.ui_thread_utid = t.utid
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  AND p.name = 'com.example.jetnews'
  AND t.name = 'example.jetnews'
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT DISTINCT p.name AS process_name, t.name AS thread_name, p.upid, t.utid
FROM process AS p
JOIN thread AS t USING (upid)
JOIN android_frames_layers AS f ON f.upid = p.upid AND f.ui_thread_utid = t.utid
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  AND p.name = 'com.example.jetnews'
  AND t.name = 'example.jetnews'
```

### c3. On that UI thread, the representative Compose work was not higher in the current trace: traversal fell from 14908.30484 ms to 14262.19295 ms, recomposition fell, and lazy-prefetch composition fell from 189.745915 ms to 181.628419 ms despite three additional prefetch slices.

The `baseline` trace: 6 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 365 AND s.dur > 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:apply', 'compose:lazy:prefetch:measure', 'traversal', 'Recomposer:recompose', 'Compose:recompose')
GROUP BY s.name
ORDER BY s.name
```

The `current` trace: 6 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 365 AND s.dur > 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:apply', 'compose:lazy:prefetch:measure', 'traversal', 'Recomposer:recompose', 'Compose:recompose')
GROUP BY s.name
ORDER BY s.name
```

### c5. The range contains a UI-layout change in InterestsScreen: commit 91eb564a995b5f47ac2de9f35636027304e2d356 changes the TopicItem thumbnail from 56.dp to 48.dp and adjusts its divider inset. The trace localization remains at generic Compose slices rather than that class, so no commit can be directly attributed as a performance culprit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

The `current` trace: 6 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 365 AND s.dur > 0
  AND s.name IN ('compose:lazy:prefetch:compose', 'compose:lazy:prefetch:apply', 'compose:lazy:prefetch:measure', 'traversal', 'Recomposer:recompose', 'Compose:recompose')
GROUP BY s.name
ORDER BY s.name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each build, so small scheduler and tail-percentile differences cannot be separated from run-to-run noise.
- The current capture is a debuggable debug build on an sdk_gphone64_arm64 emulator; frame p99 also includes display-pipeline effects, while the selected metric isolates the app UI thread.

## Dropped claims

### c4. The frame-p99 increase is not corroborated by the more stable p95 or by app-deadline jank: p99 rose from 66.911833 ms to 71.153583 ms, while frame p95 fell from 59.127166 ms to 58.652709 ms and jank fell from 12.719506407214% to 12.2270742358079%. With one capture per side, the isolated p99 increase is likely capture or pipeline variation rather than an app-UI regression.

Dropped: citation 3: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 73 tool calls, $0.0564, 276 s.
Tokens: 60 input, 685,895 cache read, 63,841 cache write, 22,230 output.
