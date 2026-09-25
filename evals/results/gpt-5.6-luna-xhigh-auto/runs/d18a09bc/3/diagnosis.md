# Regression

- **Metric:** `frame_p95_ms` +16.1 ms (19.91 → 36.01 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 2 claims kept, 2 dropped; 6 of 9 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 19.91 | 36.01 | +16.1 |

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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c3. On the UI thread, traversal and draw-VRI[MainActivity] work increased from 115.213079 ms total and 8.543375 ms maximum in the baseline to 171.379503 ms total and 15.681292 ms maximum in the current trace; postAndWait increased from 63.531836/8.071792 ms to 117.467704/14.897167 ms.

The `baseline` trace: 1 row.

```sql
SELECT t.name AS thread_name,
  sum(CASE WHEN s.name = 'traversal' THEN 1 ELSE 0 END) AS traversal_count,
  sum(CASE WHEN s.name = 'traversal' THEN s.dur ELSE 0 END) / 1e6 AS traversal_total_ms,
  max(CASE WHEN s.name = 'traversal' THEN s.dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN 1 ELSE 0 END) AS draw_count,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE 0 END) / 1e6 AS draw_total_ms,
  max(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE NULL END) / 1e6 AS draw_max_ms,
  sum(CASE WHEN s.name = 'postAndWait' THEN 1 ELSE 0 END) AS post_count,
  sum(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE 0 END) / 1e6 AS post_total_ms,
  max(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE NULL END) / 1e6 AS post_max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE t.name = 'example.jetnews'
  AND s.name IN ('traversal', 'draw-VRI[MainActivity]', 'postAndWait')
GROUP BY t.name
```

The `current` trace: 1 row.

```sql
SELECT t.name AS thread_name,
  sum(CASE WHEN s.name = 'traversal' THEN 1 ELSE 0 END) AS traversal_count,
  sum(CASE WHEN s.name = 'traversal' THEN s.dur ELSE 0 END) / 1e6 AS traversal_total_ms,
  max(CASE WHEN s.name = 'traversal' THEN s.dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN 1 ELSE 0 END) AS draw_count,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE 0 END) / 1e6 AS draw_total_ms,
  max(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE NULL END) / 1e6 AS draw_max_ms,
  sum(CASE WHEN s.name = 'postAndWait' THEN 1 ELSE 0 END) AS post_count,
  sum(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE 0 END) / 1e6 AS post_total_ms,
  max(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE NULL END) / 1e6 AS post_max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE t.name = 'example.jetnews'
  AND s.name IN ('traversal', 'draw-VRI[MainActivity]', 'postAndWait')
GROUP BY t.name
```

### c4. The likely correlated culprit is ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1, which changes SelectTopicButton from a 36 dp to a 40 dp control; the trace's increased work is in the UI traversal/draw path.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

The `baseline` trace: 1 row.

```sql
SELECT t.name AS thread_name,
  sum(CASE WHEN s.name = 'traversal' THEN 1 ELSE 0 END) AS traversal_count,
  sum(CASE WHEN s.name = 'traversal' THEN s.dur ELSE 0 END) / 1e6 AS traversal_total_ms,
  max(CASE WHEN s.name = 'traversal' THEN s.dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN 1 ELSE 0 END) AS draw_count,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE 0 END) / 1e6 AS draw_total_ms,
  max(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE NULL END) / 1e6 AS draw_max_ms,
  sum(CASE WHEN s.name = 'postAndWait' THEN 1 ELSE 0 END) AS post_count,
  sum(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE 0 END) / 1e6 AS post_total_ms,
  max(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE NULL END) / 1e6 AS post_max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE t.name = 'example.jetnews'
  AND s.name IN ('traversal', 'draw-VRI[MainActivity]', 'postAndWait')
GROUP BY t.name
```

The `current` trace: 1 row.

```sql
SELECT t.name AS thread_name,
  sum(CASE WHEN s.name = 'traversal' THEN 1 ELSE 0 END) AS traversal_count,
  sum(CASE WHEN s.name = 'traversal' THEN s.dur ELSE 0 END) / 1e6 AS traversal_total_ms,
  max(CASE WHEN s.name = 'traversal' THEN s.dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN 1 ELSE 0 END) AS draw_count,
  sum(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE 0 END) / 1e6 AS draw_total_ms,
  max(CASE WHEN s.name = 'draw-VRI[MainActivity]' THEN s.dur ELSE NULL END) / 1e6 AS draw_max_ms,
  sum(CASE WHEN s.name = 'postAndWait' THEN 1 ELSE 0 END) AS post_count,
  sum(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE 0 END) / 1e6 AS post_total_ms,
  max(CASE WHEN s.name = 'postAndWait' THEN s.dur ELSE NULL END) / 1e6 AS post_max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
WHERE t.name = 'example.jetnews'
  AND s.name IN ('traversal', 'draw-VRI[MainActivity]', 'postAndWait')
GROUP BY t.name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one baseline and one current capture are available, so run-to-run noise cannot be estimated.
- The current run metadata identifies a debuggable debug build on an sdk_gphone64_arm64 emulator (SDK 36).
- The trace localizes the change to generic UI traversal/draw and postAndWait slices rather than directly naming SelectTopicButton, so the commit attribution is correlated rather than direct.

## Dropped claims

### c1. The selected frame_p95_ms regressed from 19.914166 ms in the baseline to 36.011542 ms in the current trace, a delta of 16.097376 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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

### c2. The affected window belongs to com.example.jetnews on the example.jetnews UI thread: the baseline has 75 frames with 1 App Deadline Missed frame, while the current trace has 77 frames with 5 App Deadline Missed frames.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
  )
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name,
       count(*) AS frame_count,
       sum(f.dur) / 1e6 AS total_frame_ms,
       avg(f.dur) / 1e6 AS avg_frame_ms,
       max(f.dur) / 1e6 AS max_frame_ms,
       sum(f.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM frames AS f
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
GROUP BY p.name, p.pid, t.name
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
  )
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name,
       count(*) AS frame_count,
       sum(f.dur) / 1e6 AS total_frame_ms,
       avg(f.dur) / 1e6 AS avg_frame_ms,
       max(f.dur) / 1e6 AS max_frame_ms,
       sum(f.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM frames AS f
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
GROUP BY p.name, p.pid, t.name
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 57 tool calls, $0.0359, 181 s.
Tokens: 36 input, 206,615 cache read, 37,305 cache write, 18,711 output.
