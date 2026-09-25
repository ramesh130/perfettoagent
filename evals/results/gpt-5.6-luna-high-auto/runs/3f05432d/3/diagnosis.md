# Regression

- **Metric:** `gc_time_ms` +4,439.46 ms (59.4 → 4,498.86 ms)
- **Culprit:** `e15d633e79d2` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. App garbage-collection time increased from 59.403749 ms in the baseline to 4498.861341 ms in the current trace, a delta of 4439.457592 ms.

The `baseline` trace: 1 row.

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

The `current` trace: 1 row.

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

### c2. The GC increase is concentrated in com.example.jetnews: its HeapTaskDaemon recorded 3 collections totaling 59.403749 ms in baseline versus 184 collections totaling 4498.861341 ms currently.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
LEFT JOIN process AS p USING (upid)
LEFT JOIN thread AS t USING (utid)
GROUP BY p.name, t.name
ORDER BY gc_ms DESC
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms, max(g.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS g
LEFT JOIN process AS p USING (upid)
LEFT JOIN thread AS t USING (utid)
GROUP BY p.name, t.name
ORDER BY gc_ms DESC
```

### c3. The current trace also shows substantial new text-layout and animation work in the app process: 536157 TextLayout:initLayout slices totaling 14372.316042 ms and 1825 animation slices totaling 5036.788245 ms, while the baseline has no TextLayout:initLayout rows and has 2224 animation slices totaling 2626.393501 ms.

The `baseline` trace: 6 rows.

```sql
SELECT s.name AS slice_name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice AS s JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid JOIN process AS p ON p.upid=t.upid WHERE p.name='com.example.jetnews' AND s.name IN ('TextLayout:initLayout','Constructing StaticLayout','TextStringSimpleNode::measure','AtlasTextOp','animation','Recomposer:animation','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY s.name ORDER BY s.name
```

The `current` trace: 8 rows.

```sql
SELECT s.name AS slice_name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice AS s JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid JOIN process AS p ON p.upid=t.upid WHERE p.name='com.example.jetnews' AND s.name IN ('TextLayout:initLayout','Constructing StaticLayout','TextStringSimpleNode::measure','AtlasTextOp','animation','Recomposer:animation','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY s.name ORDER BY s.name
```

### c4. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 added adaptive repeated text measurement and an infinite row-breath animation in PostCards.kt, matching the current trace's new text-layout and animation activity.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `current` trace: 8 rows.

```sql
SELECT s.name AS slice_name, count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice AS s JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid JOIN process AS p ON p.upid=t.upid WHERE p.name='com.example.jetnews' AND s.name IN ('TextLayout:initLayout','Constructing StaticLayout','TextStringSimpleNode::measure','AtlasTextOp','animation','Recomposer:animation','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY s.name ORDER BY s.name
```

### c5. Blame at the range head assigns the added PostTitle measurement and rowBreath animation code to e15d633e79d2608f074e9c50a18f3064e15830d7.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion uses one capture per side, so smaller changes could be affected by run-to-run noise; the observed GC and UI-work increases are large.
- The current capture was a debuggable build on an Android emulator (sdk_gphone64_arm64, SDK 36).
- gc_time_ms measures ART collector wall time, not the amount or source of allocated memory.

## Run

`gpt-5.6-luna` on openai, effort high: 41 tool calls, $0.0282, 238 s.
Tokens: 24 input, 124,301 cache read, 68,132 cache write, 7,246 output.
