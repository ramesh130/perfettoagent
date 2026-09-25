# No regression

- **Metric:** `gc_time_ms` +18.23 ms (32.61 → 50.84 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 6 of 6 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `gc_time_ms` | ms | 32.61 | 50.84 | +18.23 |

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

### c1. App GC time increased from 32.61125 ms in baseline to 50.839 ms in current, a delta of 18.22775 ms.

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

### c2. The baseline app had two young collections totaling 32.61125 ms, while current had one young collection totaling 31.45225 ms and one full collection totaling 19.38675 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS collections, sum(gc_dur) / 1e6 AS total_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY process_name, gc_type
ORDER BY gc_type
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS collections, sum(gc_dur) / 1e6 AS total_ms, sum(reclaimed_mb) AS reclaimed_mb
FROM android_garbage_collection_events
WHERE process_name = 'com.example.jetnews'
GROUP BY process_name, gc_type
ORDER BY gc_type
```

### c3. The range's runtime-looking changes include reducing Interests thumbnail size and changing the widget refresh interval; neither trace evidence localizes the GC increase to those changes.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one capture per side, so the GC difference may be run-to-run noise; the current trace includes a full collection that the baseline app trace does not.
- The current capture is from a debuggable build on an Android emulator, which can add variability.

## Run

`gpt-5.6-luna` on openai, effort medium: 26 tool calls, $0.0085, 64 s.
Tokens: 18 input, 41,405 cache read, 13,561 cache write, 3,545 output.
