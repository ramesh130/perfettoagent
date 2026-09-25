# Regression

- **Metric:** `main_thread_blocked_ms` +729.71 ms (0 → 729.71 ms)
- **Culprit:** `9d695fef3c75` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `main_thread_blocked_ms` | ms | 0 | 729.71 | +729.71 |

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
```

## Claims

### c1. main_thread_blocked_ms increased from 0.0 ms in the baseline to 729.712208 ms in the current trace, a delta of 729.712208 ms.

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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
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
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM frames
  ),
  work AS (
    SELECT s.ts, s.dur
    FROM slice AS s
    JOIN thread_track AS t ON t.id = s.track_id
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name NOT GLOB 'Choreographer#doFrame*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT
  CASE
    WHEN NOT EXISTS (
      SELECT 1 FROM thread_state WHERE utid IN (SELECT utid FROM main_thread)
    ) THEN NULL
    ELSE coalesce((
      SELECT sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts))
      FROM blocked AS b
      JOIN work AS w ON b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur
    ), 0) / 1e6
  END AS value
```

### c2. The affected work is on com.example.jetnews's main thread, example.jetnews. Baseline input handling accounts for 23.099792 ms with 0.0 ms blocked, while current input handling accounts for 757.542626 ms with 729.695041 ms blocked.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  work AS (
    SELECT s.ts, s.dur, s.name, p.name AS process_name, t.name AS thread_name
    FROM slice AS s
    JOIN thread_track AS tt ON tt.id = s.track_id
    JOIN thread AS t ON t.utid = tt.utid
    JOIN process AS p ON p.upid = t.upid
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name GLOB 'deliverInputEvent*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT max(process_name) AS process_name,
       max(thread_name) AS thread_name,
       count(*) AS input_slice_count,
       sum(dur) / 1e6 AS input_slice_ms,
       coalesce(sum((SELECT coalesce(sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts)), 0)
                     FROM blocked AS b
                     WHERE b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur)), 0) / 1e6 AS input_blocked_ms
FROM work AS w;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  main_thread AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  work AS (
    SELECT s.ts, s.dur, s.name, p.name AS process_name, t.name AS thread_name
    FROM slice AS s
    JOIN thread_track AS tt ON tt.id = s.track_id
    JOIN thread AS t ON t.utid = tt.utid
    JOIN process AS p ON p.upid = t.upid
    WHERE t.utid IN (SELECT utid FROM main_thread)
      AND s.depth = 0 AND s.dur > 0
      AND s.name GLOB 'deliverInputEvent*'
  ),
  blocked AS (
    SELECT ts, dur
    FROM thread_state
    WHERE utid IN (SELECT utid FROM main_thread)
      AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')
  )
SELECT max(process_name) AS process_name,
       max(thread_name) AS thread_name,
       count(*) AS input_slice_count,
       sum(dur) / 1e6 AS input_slice_ms,
       coalesce(sum((SELECT coalesce(sum(min(b.ts + b.dur, w.ts + w.dur) - max(b.ts, w.ts)), 0)
                     FROM blocked AS b
                     WHERE b.ts < w.ts + w.dur AND w.ts < b.ts + b.dur)), 0) / 1e6 AS input_blocked_ms
FROM work AS w;
```

### c3. The current trace localizes the added delay to long AndroidOwner:onTouch work inside ViewPostImeInputStage: it contains six roughly 121–125 ms onTouch slices, whereas the corresponding short input slices are only a few milliseconds.

The `current` trace: 13 rows.

```sql
SELECT s.id, s.parent_id, s.ts, s.dur, s.depth, s.name
FROM slice AS s
WHERE s.track_id IN (SELECT id FROM thread_track WHERE utid = 369)
  AND s.name IN ('AndroidOwner:onTouch', 'ViewPostImeInputStage id=0xec823de7')
ORDER BY s.ts;
```

### c4. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 changed PostCardSimple's bookmark onClick handler to call Thread.sleep(BOOKMARK_HOLD_MS), with BOOKMARK_HOLD_MS set to 120L; git blame at the range head attributes those lines to this commit. The trace's repeated roughly 120 ms blocked onTouch intervals directly match that change.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

The `current` trace: 13 rows.

```sql
SELECT s.id, s.parent_id, s.ts, s.dur, s.depth, s.name
FROM slice AS s
WHERE s.track_id IN (SELECT id FROM thread_track WHERE utid = 369)
  AND s.name IN ('AndroidOwner:onTouch', 'ViewPostImeInputStage id=0xec823de7')
ORDER BY s.ts;
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so unrelated run-to-run variation cannot be fully measured.
- The current capture is from a debuggable debug build on the sdk_gphone64_arm64 emulator.

## Run

`gpt-5.6-luna` on openai, effort high: 27 tool calls, $0.0263, 81 s.
Tokens: 33 input, 149,759 cache read, 31,591 cache write, 12,844 output.
