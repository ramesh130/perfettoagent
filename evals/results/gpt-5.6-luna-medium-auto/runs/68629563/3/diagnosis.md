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

### c2. In the current trace, Jetnews input delivery contains six roughly 120 ms main-thread stalls, while the baseline has no such input events.

The `current` trace: 18 rows.

```sql
SELECT s.name, s.ts/1e6 AS ts_ms, s.dur/1e6 AS dur_ms, s.depth
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews' AND s.dur BETWEEN 100000000 AND 130000000
ORDER BY s.ts LIMIT 50
```

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS input_events, coalesce(sum(s.dur),0)/1e6 AS total_ms, coalesce(max(s.dur),0)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid WHERE p.name='com.example.jetnews' AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
```

### c3. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 added Thread.sleep(BOOKMARK_HOLD_MS) to the bookmark click handler and set BOOKMARK_HOLD_MS to 120 ms; blame assigns those lines to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

### c4. The repeated approximately 120 ms input-handler stalls match the 120 ms sleep introduced by that commit, making it the direct cause of the blocked-time regression.

The `current` trace: 18 rows.

```sql
SELECT s.name, s.ts/1e6 AS ts_ms, s.dur/1e6 AS dur_ms, s.depth
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews' AND s.dur BETWEEN 100000000 AND 130000000
ORDER BY s.ts LIMIT 50
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis compares one capture per side; unrelated run-to-run variation cannot be fully excluded.
- The traces were captured on an Android SDK 36 emulator using a debuggable debug build.

## Run

`gpt-5.6-luna` on openai, effort medium: 33 tool calls, $0.0139, 66 s.
Tokens: 30 input, 97,104 cache read, 14,803 cache write, 6,882 output.
