# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
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

### c1. The selected UI-frame metric regressed: frame UI p95 increased from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a 77.462416 ms increase.

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

### c2. The regression is on the app's UI thread: the current trace recorded 1,825 doFrame slices totaling 56,544.265833 ms, versus 2,305 slices totaling 19,050.659162 ms in the baseline.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT t.utid, t.tid, t.name AS thread_name, count(*) AS doframe_count, sum(s.dur)/1e6 AS total_doframe_ms, max(s.dur)/1e6 AS max_doframe_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY t.utid, t.tid, t.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT t.utid, t.tid, t.name AS thread_name, count(*) AS doframe_count, sum(s.dur)/1e6 AS total_doframe_ms, max(s.dur)/1e6 AS max_doframe_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY t.utid, t.tid, t.name
```

### c3. Garbage collection increased sharply in the app process: baseline had 3 collections totaling 59.403749 ms, while current had 184 collections totaling 4,498.861341 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.upid, p.name AS process_name, sum(e.gc_dur)/1e6 AS gc_ms, count(*) AS gc_count, max(e.gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p ON p.upid = e.upid
WHERE e.upid = (SELECT upid FROM app)
GROUP BY p.upid, p.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.upid, p.name AS process_name, sum(e.gc_dur)/1e6 AS gc_ms, count(*) AS gc_count, max(e.gc_dur)/1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p ON p.upid = e.upid
WHERE e.upid = (SELECT upid FROM app)
GROUP BY p.upid, p.name
```

### c4. The current UI thread contains 536,157 TextLayout:initLayout slices and 536,157 Constructing StaticLayout slices; the baseline contains none of either. This localizes the added work to repeated text measurement/layout, alongside the current row animation activity.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT
  count(*) AS all_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_count,
  coalesce(sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_count,
  coalesce(sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'animation' THEN 1 ELSE 0 END) AS animation_count,
  coalesce(sum(CASE WHEN s.name = 'animation' THEN s.dur ELSE 0 END), 0) / 1e6 AS animation_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid IN (SELECT ui_thread_utid FROM frames)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT
  count(*) AS all_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_count,
  coalesce(sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_count,
  coalesce(sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'animation' THEN 1 ELSE 0 END) AS animation_count,
  coalesce(sum(CASE WHEN s.name = 'animation' THEN s.dur ELSE 0 END), 0) / 1e6 AS animation_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid IN (SELECT ui_thread_utid FROM frames)
```

### c5. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 adds the PostCards text-sizing loop using rememberTextMeasurer and the rowBreath infinite animation/padding. The head blame assigns those additions to that commit, directly matching the current-only text-layout surge and making it the direct culprit.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT
  count(*) AS all_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_count,
  coalesce(sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_count,
  coalesce(sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_count,
  coalesce(sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END), 0) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'animation' THEN 1 ELSE 0 END) AS animation_count,
  coalesce(sum(CASE WHEN s.name = 'animation' THEN s.dur ELSE 0 END), 0) / 1e6 AS animation_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
WHERE tt.utid IN (SELECT ui_thread_utid FROM frames)
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available, so run-to-run variance cannot be ruled out.
- The selected percentile and cumulative GC totals are sensitive to capture timing and scenario duration.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 50 tool calls, $0.0332, 664 s.
Tokens: 33 input, 191,699 cache read, 38,587 cache write, 16,467 output.
