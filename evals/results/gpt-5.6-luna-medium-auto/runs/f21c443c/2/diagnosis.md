# Regression

- **Metric:** `gc_time_ms` +10,097.52 ms (258.58 → 10,356.09 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 258.58 | 10,356.09 | +10,097.52 |

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

### c1. App GC time increased from 258.575876 ms in the baseline to 10356.094546 ms in the current trace, a 10097.51867 ms increase.

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

### c2. The current app process accounts for 149 GC events and 10356.094546 ms of GC, versus 7 events and 258.575876 ms for the baseline app process.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT upid, COUNT(*) AS gc_count, SUM(gc_dur) / 1e6 AS gc_ms, MAX(gc_dur) / 1e6 AS max_gc_ms FROM android_garbage_collection_events GROUP BY upid ORDER BY gc_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT upid, COUNT(*) AS gc_count, SUM(gc_dur) / 1e6 AS gc_ms, MAX(gc_dur) / 1e6 AS max_gc_ms FROM android_garbage_collection_events GROUP BY upid ORDER BY gc_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.upid, p.name, COUNT(*) AS gc_count, SUM(g.gc_dur) / 1e6 AS gc_ms FROM android_garbage_collection_events AS g JOIN process AS p USING (upid) GROUP BY p.upid, p.name ORDER BY gc_ms DESC
```

### c3. The current trace contains substantial app drawing activity alongside 149 garbage collections, including 427 AndroidOwner:draw slices totaling 6800.699007 ms and 448 draw-VRI[MainActivity] slices totaling 8073.198007 ms.

The `current` trace: 30 rows.

```sql
SELECT s.name, COUNT(*) AS slice_count, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice AS s JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid WHERE t.upid=370 GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

### c4. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 added a per-frame drawWithContent grain implementation in FeedScreen, including List(GRAIN_SPECKS) with GRAIN_SPECKS set to 1,000,000; blame assigns those lines to that commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c5. The allocation-heavy grain change is the likely cause of the GC regression because it was introduced in the range and coincides with the large increase in app GC during drawing.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

The `current` trace: 30 rows.

```sql
SELECT s.name, COUNT(*) AS slice_count, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice AS s JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid WHERE t.upid=370 GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.upid, p.name, COUNT(*) AS gc_count, SUM(g.gc_dur) / 1e6 AS gc_ms FROM android_garbage_collection_events AS g JOIN process AS p USING (upid) GROUP BY p.upid, p.name ORDER BY gc_ms DESC
```

## Caveats

- This conclusion compares one capture per side, so smaller changes could be affected by run-to-run variability; this GC increase is large relative to typical noise.
- The captures were made on an Android emulator (sdk_gphone64_arm64, SDK 36).
- The trace did not contain stack-profile tables, so the attribution is correlated rather than direct; the code change and trace-level GC/drawing evidence align, but no sampled frame directly names FeedScreen.

## Run

`gpt-5.6-luna` on openai, effort medium: 31 tool calls, $0.0139, 114 s.
Tokens: 30 input, 109,058 cache read, 25,226 cache write, 4,522 output.
