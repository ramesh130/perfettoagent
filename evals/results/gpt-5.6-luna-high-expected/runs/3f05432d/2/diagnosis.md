# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The UI-time p95 increased from 26.299542 ms in baseline to 103.761958 ms in current, a 77.462416 ms regression.

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

### c2. The slow work is on com.example.jetnews's UI thread: its maximum doFrame grew from 59.515916 ms in baseline to 268.590125 ms in current.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.tid, t.name AS thread_name,
  COUNT(*) AS do_frame_count, MAX(s.dur) / 1e6 AS max_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
GROUP BY p.name, t.tid, t.name
ORDER BY do_frame_count DESC
LIMIT 10
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.tid, t.name AS thread_name,
  COUNT(*) AS do_frame_count, MAX(s.dur) / 1e6 AS max_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON s.track_id = tt.id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
GROUP BY p.name, t.tid, t.name
ORDER BY do_frame_count DESC
LIMIT 10
```

### c3. The current trace contains 536157 TextLayout:initLayout slices totaling 14372.316042 ms, while the baseline contains none; traversal also reaches 263.646208 ms in current versus 58.587958 ms in baseline.

The `baseline` trace: 1 row.

```sql
SELECT
  COUNT(CASE WHEN name = 'traversal' THEN 1 END) AS traversal_count,
  COALESCE(SUM(CASE WHEN name = 'traversal' THEN dur ELSE 0 END), 0) / 1e6 AS traversal_total_ms,
  MAX(CASE WHEN name = 'traversal' THEN dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  COUNT(CASE WHEN name = 'TextLayout:initLayout' THEN 1 END) AS text_layout_count,
  COALESCE(SUM(CASE WHEN name = 'TextLayout:initLayout' THEN dur ELSE 0 END), 0) / 1e6 AS text_layout_total_ms,
  COUNT(CASE WHEN name = 'Constructing StaticLayout' THEN 1 END) AS static_layout_count,
  COALESCE(SUM(CASE WHEN name = 'Constructing StaticLayout' THEN dur ELSE 0 END), 0) / 1e6 AS static_layout_total_ms
FROM slice
```

The `current` trace: 1 row.

```sql
SELECT
  COUNT(CASE WHEN name = 'traversal' THEN 1 END) AS traversal_count,
  COALESCE(SUM(CASE WHEN name = 'traversal' THEN dur ELSE 0 END), 0) / 1e6 AS traversal_total_ms,
  MAX(CASE WHEN name = 'traversal' THEN dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  COUNT(CASE WHEN name = 'TextLayout:initLayout' THEN 1 END) AS text_layout_count,
  COALESCE(SUM(CASE WHEN name = 'TextLayout:initLayout' THEN dur ELSE 0 END), 0) / 1e6 AS text_layout_total_ms,
  COUNT(CASE WHEN name = 'Constructing StaticLayout' THEN 1 END) AS static_layout_count,
  COALESCE(SUM(CASE WHEN name = 'Constructing StaticLayout' THEN dur ELSE 0 END), 0) / 1e6 AS static_layout_total_ms
FROM slice
```

### c4. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 changed PostCards.kt to add a per-title TextMeasurer loop and an infinite row-breath animation; blame assigns those lines to that same commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

### c5. The trace-localized text-layout and traversal increase directly match the new PostCards.kt work, so e15d633e79d2608f074e9c50a18f3064e15830d7 is the direct culprit.

The `current` trace: 1 row.

```sql
SELECT
  COUNT(CASE WHEN name = 'traversal' THEN 1 END) AS traversal_count,
  COALESCE(SUM(CASE WHEN name = 'traversal' THEN dur ELSE 0 END), 0) / 1e6 AS traversal_total_ms,
  MAX(CASE WHEN name = 'traversal' THEN dur ELSE NULL END) / 1e6 AS traversal_max_ms,
  COUNT(CASE WHEN name = 'TextLayout:initLayout' THEN 1 END) AS text_layout_count,
  COALESCE(SUM(CASE WHEN name = 'TextLayout:initLayout' THEN dur ELSE 0 END), 0) / 1e6 AS text_layout_total_ms,
  COUNT(CASE WHEN name = 'Constructing StaticLayout' THEN 1 END) AS static_layout_count,
  COALESCE(SUM(CASE WHEN name = 'Constructing StaticLayout' THEN dur ELSE 0 END), 0) / 1e6 AS static_layout_total_ms
FROM slice
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side has only one capture, so exact percentile values include run-to-run noise.
- The captures are from a debuggable build on an Android emulator; absolute timings may differ on physical release builds.

## Run

`gpt-5.6-luna` on openai, effort high: 20 tool calls, $0.0171, 117 s.
Tokens: 27 input, 93,744 cache read, 21,114 cache write, 8,294 output.
