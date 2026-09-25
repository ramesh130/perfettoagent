# Regression

- **Metric:** `gc_time_ms` +4,439.46 ms (59.4 → 4,498.86 ms)
- **Culprit:** `e15d633e79d2` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 59.4 | 4,498.86 | +4,439.46 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
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
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_garbage_collection_events) THEN NULL
    ELSE coalesce((
      SELECT sum(gc_dur) FROM android_garbage_collection_events
      WHERE upid = (SELECT upid FROM app)
    ), 0) / 1e6
  END AS value
```

## Claims

### c1. App garbage-collection time increased from 59.403749 ms across 3 app GC events in baseline to 4498.861341 ms across 184 app GC events in current.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, count(*) AS gc_count, sum(gc_dur) / 1e6 AS total_gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY process_name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, count(*) AS gc_count, sum(gc_dur) / 1e6 AS total_gc_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY process_name
```

### c2. The new work localizes to com.example.jetnews's example.jetnews thread: current has 536157 TextLayout:initLayout slices totaling 14372.316042 ms and 536157 Constructing StaticLayout slices totaling 11049.010378 ms, while baseline has zero of both.

The `baseline` trace: 1 row.

```sql
SELECT
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Compose:recompose' THEN 1 ELSE 0 END) AS recompose_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'Compose:recompose' THEN s.dur ELSE 0 END) / 1e6 AS recompose_ms
FROM slice s
JOIN thread_track tt ON tt.id = s.track_id
JOIN thread t ON t.utid = tt.utid
JOIN process p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
```

The `current` trace: 3 rows.

```sql
SELECT t.name AS thread_name, s.name AS slice_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s
JOIN thread_track tt ON tt.id = s.track_id
JOIN thread t ON t.utid = tt.utid
JOIN process p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
  AND s.name IN ('TextLayout:initLayout', 'Constructing StaticLayout', 'Compose:recompose')
GROUP BY t.name, s.name
ORDER BY total_ms DESC
```

The `current` trace: 1 row.

```sql
SELECT
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Compose:recompose' THEN 1 ELSE 0 END) AS recompose_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'Compose:recompose' THEN s.dur ELSE 0 END) / 1e6 AS recompose_ms
FROM slice s
JOIN thread_track tt ON tt.id = s.track_id
JOIN thread t ON t.utid = tt.utid
JOIN process p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
```

### c3. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 changes PostCards.kt's PostTitle implementation to use BoxWithConstraints and a while-loop calling rememberTextMeasurer().measure, and also adds an always-running row animation. These changes account for the new repeated text-layout and recomposition workload.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `current` trace: 3 rows.

```sql
SELECT t.name AS thread_name, s.name AS slice_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s
JOIN thread_track tt ON tt.id = s.track_id
JOIN thread t ON t.utid = tt.utid
JOIN process p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
  AND s.name IN ('TextLayout:initLayout', 'Constructing StaticLayout', 'Compose:recompose')
GROUP BY t.name, s.name
ORDER BY total_ms DESC
```

### c4. The regression is directly attributed to e15d633e79d2608f074e9c50a18f3064e15830d7 because the trace shows the new text-layout workload in the app thread and the commit introduced the corresponding PostTitle measurement loop.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `baseline` trace: 1 row.

```sql
SELECT
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Compose:recompose' THEN 1 ELSE 0 END) AS recompose_slices,
  sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices,
  sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms,
  sum(CASE WHEN s.name = 'Compose:recompose' THEN s.dur ELSE 0 END) / 1e6 AS recompose_ms
FROM slice s
JOIN thread_track tt ON tt.id = s.track_id
JOIN thread t ON t.utid = tt.utid
JOIN process p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
```

The `current` trace: 3 rows.

```sql
SELECT t.name AS thread_name, s.name AS slice_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s
JOIN thread_track tt ON tt.id = s.track_id
JOIN thread t ON t.utid = tt.utid
JOIN process p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews'
  AND s.name IN ('TextLayout:initLayout', 'Constructing StaticLayout', 'Compose:recompose')
GROUP BY t.name, s.name
ORDER BY total_ms DESC
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so run-to-run noise is not quantified; the observed change is nevertheless much larger than a small-noise comparison.
- The current metadata identifies a debuggable debug build running on the sdk_gphone64_arm64 emulator, so the result may not represent a release build on physical hardware.
- Baseline build metadata was not recorded.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 44 tool calls, $0.0272, 362 s.
Tokens: 27 input, 130,555 cache read, 30,465 cache write, 14,102 output.
