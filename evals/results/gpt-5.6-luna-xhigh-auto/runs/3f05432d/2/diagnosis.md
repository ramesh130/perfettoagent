# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.3 | 103.76 | +77.46 |

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

### c1. UI-thread frame p95 worsened from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a delta of 77.462416 ms.

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

### c2. The affected process is com.example.jetnews in both captures, with one UI thread; the frame-derived process has 2,138 rows in the baseline and 1,823 in the current trace.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.upid, p.pid, p.name, count(*) AS frame_count, count(DISTINCT f.ui_thread_utid) AS ui_threads
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.upid, p.pid, p.name
ORDER BY frame_count DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.upid, p.pid, p.name, count(*) AS frame_count, count(DISTINCT f.ui_thread_utid) AS ui_threads
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY p.upid, p.pid, p.name
ORDER BY frame_count DESC
```

### c3. The current UI thread recorded 536157 TextLayout:initLayout slices totaling 14372.316042 ms and 536157 Constructing StaticLayout slices totaling 11049.010378 ms. The baseline recorded zero of both; it had only 216 TextStringSimpleNode::measure slices totaling 1.149824 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH ui AS (
  SELECT DISTINCT f.ui_thread_utid AS utid
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
)
SELECT
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'TextStringSimpleNode::measure' THEN 1 ELSE 0 END) AS text_measure_slices,
  sum(CASE WHEN s.name = 'TextStringSimpleNode::measure' THEN s.dur ELSE 0 END) / 1e6 AS text_measure_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN ui ON ui.utid = tt.utid
WHERE s.dur > 0
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH ui AS (
  SELECT DISTINCT f.ui_thread_utid AS utid
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
)
SELECT
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'TextStringSimpleNode::measure' THEN 1 ELSE 0 END) AS text_measure_slices,
  sum(CASE WHEN s.name = 'TextStringSimpleNode::measure' THEN s.dur ELSE 0 END) / 1e6 AS text_measure_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN ui ON ui.utid = tt.utid
WHERE s.dur > 0
```

### c4. Garbage-collection activity in com.example.jetnews increased from 3 collections totaling 59.403749 ms in the baseline to 184 collections totaling 4498.861341 ms in the current trace, all on HeapTaskDaemon.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.upid, p.pid, p.name, count(*) AS gc_count, sum(e.gc_dur) / 1e6 AS gc_ms, max(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
GROUP BY p.upid, p.pid, p.name
ORDER BY gc_ms DESC
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.upid, p.pid, p.name, count(*) AS gc_count, sum(e.gc_dur) / 1e6 AS gc_ms, max(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
GROUP BY p.upid, p.pid, p.name
ORDER BY gc_ms DESC
```

### c5. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 changes PostCards.kt by adding repeated text measurement with rememberTextMeasurer and an animated row-breath recomposition path. That change matches the current-only text-layout surge and GC increase, making it the likely source of the regression.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH ui AS (
  SELECT DISTINCT f.ui_thread_utid AS utid
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
)
SELECT
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'TextStringSimpleNode::measure' THEN 1 ELSE 0 END) AS text_measure_slices,
  sum(CASE WHEN s.name = 'TextStringSimpleNode::measure' THEN s.dur ELSE 0 END) / 1e6 AS text_measure_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN ui ON ui.utid = tt.utid
WHERE s.dur > 0
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so run-to-run noise is not independently estimated.
- The traces were captured on an Android emulator using a debuggable build; absolute timings may include emulator and debug-build overhead.
- No app callstack samples were available for a symbol-level attribution, so the culprit is marked correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 64 tool calls, $0.0350, 492 s.
Tokens: 39 input, 212,374 cache read, 40,216 cache write, 17,282 output.
