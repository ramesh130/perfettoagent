# Regression

- **Metric:** `main_thread_blocked_ms` +729.71 ms (0 → 729.71 ms)
- **Culprit:** `9d695fef3c75` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 6 claims kept, 0 dropped; 11 of 11 citations passed
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

### c1. Main-thread blocked time increased from 0.0 ms in the baseline to 729.712208 ms in the current trace.

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

### c2. The selected application is com.example.jetnews in both captures, and the affected thread is its UI thread.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid, ui_thread_utid FROM window_frames GROUP BY upid, ui_thread_utid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.upid, p.pid, p.name AS process_name, t.utid, t.tid, t.name AS thread_name, (SELECT count(*) FROM window_frames w WHERE w.upid=p.upid) AS window_frame_rows
FROM app JOIN process p USING (upid) JOIN thread t ON t.utid=app.ui_thread_utid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid, ui_thread_utid FROM window_frames GROUP BY upid, ui_thread_utid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.upid, p.pid, p.name AS process_name, t.utid, t.tid, t.name AS thread_name, (SELECT count(*) FROM window_frames w WHERE w.upid=p.upid) AS window_frame_rows
FROM app JOIN process p USING (upid) JOIN thread t ON t.utid=app.ui_thread_utid
```

### c3. The current trace has six input-dispatch events lasting at least 100 ms, totaling 737.008876 ms, with 729.695041 ms overlapping blocked time. The baseline has only sub-100-ms input events, with 23.099792 ms total and no blocked overlap.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC,upid LIMIT 1), mt AS (SELECT ui_thread_utid AS utid FROM app), inputs AS (
  SELECT s.ts,s.dur,s.name FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
), blocked AS (SELECT ts,dur,state FROM thread_state WHERE utid IN (SELECT utid FROM mt) AND dur>0 AND state NOT IN ('Running','R','R+'))
SELECT CASE WHEN i.dur>=100000000 THEN '>=100ms' ELSE '<100ms' END AS input_duration, count(*) AS events, sum(i.dur)/1e6 AS input_total_ms, sum((SELECT coalesce(sum(min(b.ts+b.dur,i.ts+i.dur)-max(b.ts,i.ts)),0) FROM blocked b WHERE b.ts<i.ts+i.dur AND i.ts<b.ts+b.dur))/1e6 AS blocked_overlap_ms, max(i.dur)/1e6 AS max_event_ms FROM inputs i GROUP BY input_duration ORDER BY input_duration
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC,upid LIMIT 1), mt AS (SELECT ui_thread_utid AS utid FROM app), inputs AS (
  SELECT s.ts,s.dur,s.name FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
), blocked AS (SELECT ts,dur,state FROM thread_state WHERE utid IN (SELECT utid FROM mt) AND dur>0 AND state NOT IN ('Running','R','+'))
SELECT CASE WHEN i.dur>=100000000 THEN '>=100ms' ELSE '<100ms' END AS input_duration, count(*) AS events, sum(i.dur)/1e6 AS input_total_ms, sum((SELECT coalesce(sum(min(b.ts+b.dur,i.ts+i.dur)-max(b.ts,i.ts)),0) FROM blocked b WHERE b.ts<i.ts+i.dur AND i.ts<b.ts+i.dur))/1e6 AS blocked_overlap_ms, max(i.dur)/1e6 AS max_event_ms FROM inputs i GROUP BY input_duration ORDER BY input_duration
```

### c4. The UI-time p95 also worsened, from 8.3585 ms to 13.957625 ms, a 5.599125 ms increase.

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

### c5. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 adds a synchronous Thread.sleep(BOOKMARK_HOLD_MS) to the bookmark click handler and sets BOOKMARK_HOLD_MS to 120 ms in PostCards.kt.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

### c6. At the range head, blame assigns both the Thread.sleep line and the 120L hold constant to commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87; the roughly 120-ms input waits therefore correlate with this commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid,ui_thread_utid FROM window_frames GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC,upid LIMIT 1), mt AS (SELECT ui_thread_utid AS utid FROM app), inputs AS (
  SELECT s.ts,s.dur,s.name FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.name GLOB 'deliverInputEvent*'
), blocked AS (SELECT ts,dur,state FROM thread_state WHERE utid IN (SELECT utid FROM mt) AND dur>0 AND state NOT IN ('Running','R','+'))
SELECT CASE WHEN i.dur>=100000000 THEN '>=100ms' ELSE '<100ms' END AS input_duration, count(*) AS events, sum(i.dur)/1e6 AS input_total_ms, sum((SELECT coalesce(sum(min(b.ts+b.dur,i.ts+i.dur)-max(b.ts,i.ts)),0) FROM blocked b WHERE b.ts<i.ts+i.dur AND i.ts<b.ts+i.dur))/1e6 AS blocked_overlap_ms, max(i.dur)/1e6 AS max_event_ms FROM inputs i GROUP BY input_duration ORDER BY input_duration
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so small deltas could be affected by run-to-run noise; the 729.7 ms increase and repeated roughly 120-ms waits are much larger and more specific than a small percentile fluctuation.
- The attribution is timing/code correlation rather than a source-line stack attribution; the traces localize the blocked UI-thread input dispatch, while the changed source supplies the matching synchronous hold.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 60 tool calls, $0.0380, 177 s.
Tokens: 48 input, 304,187 cache read, 34,671 cache write, 19,340 output.
