# No regression

- **Metric:** `frame_p95_ms` +0.5 ms (58.63 → 59.13 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 58.63 | 59.13 | +0.5 |

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

### c1. The app's frame p95 increased nominally from 58.626583 ms in the baseline to 59.127166 ms in the current trace, a delta of 0.500583 ms.

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

### c2. The frame workload is in com.example.jetnews's UI thread; the baseline had 2286 doFrame slices totaling 18919.493771 ms, while the current trace had 2277 totaling 18037.067023 ms. This does not show a consistent worsening of the UI workload.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frames, sum(s.dur)/1e6 AS doframe_ms, max(s.dur)/1e6 AS max_doframe_ms FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING(id) JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid JOIN process AS p ON p.upid=t.upid WHERE p.name='com.example.jetnews' GROUP BY p.name,t.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frames, sum(s.dur)/1e6 AS doframe_ms, max(s.dur)/1e6 AS max_doframe_ms FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING(id) JOIN thread_track AS tt ON tt.id=s.track_id JOIN thread AS t ON t.utid=tt.utid JOIN process AS p ON p.upid=t.upid WHERE p.name='com.example.jetnews' GROUP BY p.name,t.name
```

### c3. Garbage-collection time increased from 32.61125 ms to 50.839 ms for the app, but the current trace's increase consists of one young collection and one full collection versus two young collections in the baseline; this is not evidence of a frame regression attributable to the commit range.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS collections, sum(gc_dur)/1e6 AS gc_ms, max(gc_dur)/1e6 AS max_gc_ms FROM android_garbage_collection_events WHERE process_name='com.example.jetnews' GROUP BY process_name,gc_type ORDER BY gc_type
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, gc_type, count(*) AS collections, sum(gc_dur)/1e6 AS gc_ms, max(gc_dur)/1e6 AS max_gc_ms FROM android_garbage_collection_events WHERE process_name='com.example.jetnews' GROUP BY process_name,gc_type ORDER BY gc_type
```

### c4. The only range commit with a directly observable UI-layout change in the inspected code changes Interests-row thumbnails from 56.dp to 48.dp and adjusts the divider inset; the blamed lines were introduced by commit 77a061c0c715ba071167b2104fcebb2c2be12c8d.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

### c5. The range head also changes the widget refresh interval from one hour to 30 minutes, in app/src/main/res/values/integers.xml; this does not identify a cause for the observed UI-frame variation.

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so the 0.500583 ms p95 difference is plausibly run-to-run noise rather than a confirmed regression.
- The current trace metadata identifies a debuggable build running on an Android emulator; emulator and debug-build variability further limit attribution.
- The heap, startup, native-allocation, and binder metrics did not provide usable deltas for this diagnosis.

## Run

`gpt-5.6-luna` on openai, effort medium: 33 tool calls, $0.0104, 85 s.
Tokens: 18 input, 46,638 cache read, 15,246 cache write, 4,712 output.
