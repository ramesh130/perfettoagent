# Regression

- **Metric:** `main_thread_blocked_ms` +9.02 ms (19.16 → 28.18 ms)
- **Culprit:** `328304f8f108` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 1 dropped; 7 of 8 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `main_thread_blocked_ms` | ms | 19.16 | 28.18 | +9.02 |

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

### c1. Main-thread blocked time increased from 19.156252 ms in the baseline to 28.178959 ms in the current trace, a 9.022707 ms regression.

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

### c2. The added blocking is localized to contention with the SuperPlayer:PooledPlayback thread: the overlapping blocked time rose from 3.766668 ms to 17.008126 ms.

The `baseline` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)), main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames), work AS (SELECT s.ts, s.dur, s.name FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth = 0 AND s.dur > 0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts, dur FROM thread_state WHERE utid IN (SELECT utid FROM main_thread) AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')) SELECT w.name, count(*) AS overlaps, sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms FROM blocked b JOIN work w ON b.ts<w.ts+w.dur AND w.ts<b.ts+b.dur GROUP BY w.name ORDER BY blocked_ms DESC LIMIT 30
```

The `current` trace: 14 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)), main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM frames), work AS (SELECT s.ts, s.dur, s.name FROM slice AS s JOIN thread_track AS t ON t.id = s.track_id WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth = 0 AND s.dur > 0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts, dur FROM thread_state WHERE utid IN (SELECT utid FROM main_thread) AND dur > 0 AND state NOT IN ('Running', 'R', 'R+')) SELECT w.name, count(*) AS overlaps, sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms FROM blocked b JOIN work w ON b.ts<w.ts+w.dur AND w.ts<b.ts+b.dur GROUP BY w.name ORDER BY blocked_ms DESC LIMIT 30
```

### c3. Commit 328304f8 changes FeedScreen.kt in the range, at the feed's watched-row player-acquisition path; this correlates with the new PooledPlayback contention, but the trace does not provide direct source-line attribution.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
328304f8f1081e484f20030bb6518b1b1ee03c82
```

The `current` trace: 22 rows.

```sql
SELECT name,count(*) AS cnt,sum(dur)/1e6 AS total_ms,max(dur)/1e6 AS max_ms FROM slice WHERE name GLOB 'monitor contention with owner SuperPlayer:PooledPlayback*' GROUP BY name ORDER BY total_ms DESC
```

## Caveats

- This is one capture per side, so the whole-trace blocked-time delta may include run-to-run variability.
- The captures ran on an emulator; the current run was a non-debuggable benchmark build.
- Attribution is correlated rather than direct: the trace identifies PooledPlayback contention, but does not map that contention to a source line.

## Dropped claims

### c4. The frame-level p95 did not regress: it fell from 76.544292 ms to 73.255125 ms, so the observed regression is specifically in non-frame main-thread blocking rather than overall frame p95.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 20 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such table: frames

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 20 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such table: frames

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
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort high: 80 tool calls, $0.0464, 282 s.
Tokens: 45 input, 428,722 cache read, 70,108 cache write, 16,880 output.
