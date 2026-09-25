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

### c1. The app main thread's blocked time increased from 0.0 ms in the baseline to 729.712208 ms in the current trace.

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

### c2. In the current trace, the app process com.example.jetnews and thread example.jetnews contain repeated deliverInputEvent slices lasting about 121–125 ms, with AndroidOwner:onTouch accounting for about 125 ms inside one event.

The `current` trace: 10 rows.

```sql
SELECT s.id, s.name, s.ts, s.dur/1e6 AS dur_ms, t.utid, t.name AS thread_name, p.name AS process_name FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid WHERE s.name GLOB 'deliverInputEvent*' ORDER BY s.dur DESC LIMIT 10
```

The `current` trace: 30 rows.

```sql
SELECT name, dur/1e6 AS dur_ms, depth FROM slice WHERE ts>=2513573490239 AND ts<2513573490239+125174125 ORDER BY dur DESC LIMIT 30
```

### c3. The range contains a change in PostCards.kt that wraps the bookmark click handler with Thread.sleep(BOOKMARK_HOLD_MS), where BOOKMARK_HOLD_MS is 120 ms.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

### c4. The changed sleep and constant were introduced by commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87, and the current trace's roughly 120 ms input-handler stalls directly match that code path.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

The `current` trace: 30 rows.

```sql
SELECT name, dur/1e6 AS dur_ms, depth FROM slice WHERE ts>=2513573490239 AND ts<2513573490239+125174125 ORDER BY dur DESC LIMIT 30
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This comparison uses one capture per side, so smaller frame-metric changes may be noisy; the blocked-time increase is large and repeated in input events.
- The current run metadata identifies a debuggable debug build on an Android emulator (sdk_gphone64_arm64, SDK 36).

## Run

`gpt-5.6-luna` on openai, effort low: 16 tool calls, $0.0115, 34 s.
Tokens: 24 input, 62,169 cache read, 24,080 cache write, 3,518 output.
