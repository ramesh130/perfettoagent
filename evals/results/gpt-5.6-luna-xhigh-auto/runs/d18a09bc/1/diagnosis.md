# Regression

- **Metric:** `frame_p95_ms` +16.1 ms (19.91 → 36.01 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 4 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The app frame p95 increased from 19.914166 ms in the baseline to 36.011542 ms in the current trace, a 16.097376 ms regression.

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

### c2. The affected frame workload is com.example.jetnews: its UI thread recorded 75 frames and 1 app-deadline miss in the baseline, versus 77 frames and 5 misses currently.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  p.name AS process_name,
  p.pid,
  t.name AS ui_thread_name,
  t.utid,
  count(DISTINCT a.id) AS frame_count,
  sum(a.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  max(a.dur) / 1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.upid, p.name, p.pid, t.name, t.utid
ORDER BY frame_count DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  p.name AS process_name,
  p.pid,
  t.name AS ui_thread_name,
  t.utid,
  count(DISTINCT a.id) AS frame_count,
  sum(a.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  max(a.dur) / 1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p ON p.upid = f.upid
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.upid, p.name, p.pid, t.name, t.utid
ORDER BY frame_count DESC
```

### c3. On the app UI thread, traversal increased from 115.213079 ms total and 8.543375 ms maximum to 171.379503 ms total and 15.681292 ms maximum; draw-VRI[MainActivity] and postAndWait increased similarly.

The `baseline` trace: 100 rows.

```sql
SELECT
  s.depth,
  s.name,
  count(*) AS slice_count,
  sum(s.dur) / 1e6 AS total_ms,
  max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 313 AND s.dur > 0
GROUP BY s.depth, s.name
ORDER BY total_ms DESC
LIMIT 100
```

The `current` trace: 100 rows.

```sql
SELECT
  s.depth,
  s.name,
  count(*) AS slice_count,
  sum(s.dur) / 1e6 AS total_ms,
  max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 357 AND s.dur > 0
GROUP BY s.depth, s.name
ORDER BY total_ms DESC
LIMIT 100
```

### c4. Commit ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1 changes SelectTopicButton in the affected UI area from a 36 dp size to 40 dp; together with the UI traversal and draw increase, it is the likely correlated culprit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

The `baseline` trace: 100 rows.

```sql
SELECT
  s.depth,
  s.name,
  count(*) AS slice_count,
  sum(s.dur) / 1e6 AS total_ms,
  max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 313 AND s.dur > 0
GROUP BY s.depth, s.name
ORDER BY total_ms DESC
LIMIT 100
```

The `current` trace: 100 rows.

```sql
SELECT
  s.depth,
  s.name,
  count(*) AS slice_count,
  sum(s.dur) / 1e6 AS total_ms,
  max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid = 357 AND s.dur > 0
GROUP BY s.depth, s.name
ORDER BY total_ms DESC
LIMIT 100
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This compares one capture per side, so run-to-run variance cannot be ruled out.
- The current capture is from a debuggable debug build on an SDK 36 emulator.
- The trace localizes the change to UI traversal/draw framework slices rather than an app class or method, so the commit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 66 tool calls, $0.0352, 152 s.
Tokens: 45 input, 374,451 cache read, 46,182 cache write, 13,470 output.
