# Regression

- **Metric:** `frame_ui_time_p95_ms` +22.31 ms (37.95 → 60.26 ms)
- **Culprit:** `60be8b69bd69` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 37.95 | 60.26 | +22.31 |

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank,
      count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Claims

### c1. The app UI-time p95 increased from 37.952167 ms in the baseline to 60.2595 ms in the current trace, a 22.307333 ms increase.

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

### c2. The frame-owning process is com.superplayer.demo in both captures, so the change is in the app's UI work rather than a different measured application.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, p.pid, p.name AS process_name, f.ui_thread_utid, t.tid, t.name AS thread_name, f.layer_name, count(*) AS rows, min(a.dur)/1e6 AS min_frame_ms, max(a.dur)/1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
LEFT JOIN process AS p ON p.upid = f.upid
LEFT JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, p.pid, p.name, f.ui_thread_utid, t.tid, t.name, f.layer_name
ORDER BY rows DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, p.pid, p.name AS process_name, f.ui_thread_utid, t.tid, t.name AS thread_name, f.layer_name, count(*) AS rows, min(a.dur)/1e6 AS min_frame_ms, max(a.dur)/1e6 AS max_frame_ms
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
LEFT JOIN process AS p ON p.upid = f.upid
LEFT JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, p.pid, p.name, f.ui_thread_utid, t.tid, t.name, f.layer_name
ORDER BY rows DESC
```

### c3. The main-thread traversal became draw-dominated: average AndroidOwner:draw time rose from 0.2450467 ms to 11.3906385 ms, and average Record View#draw() time rose from 1.0752295 ms to 11.9664804 ms.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), doframes AS (
  SELECT s.id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
  WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid = (SELECT upid FROM app))
), roots AS (
  SELECT c.id FROM doframes AS d JOIN slice AS c ON c.parent_id = d.id WHERE c.name = 'traversal'
), descendants(id, name, dur, depth) AS (
  SELECT s.id, s.name, s.dur, 0 FROM roots AS r JOIN slice AS s ON s.id = r.id
  UNION ALL
  SELECT s.id, s.name, s.dur, d.depth + 1 FROM slice AS s JOIN descendants AS d ON s.parent_id = d.id WHERE d.depth < 8
)
SELECT name, count(*) AS occurrences, sum(dur) / 1e6 AS total_ms, avg(dur) / 1e6 AS avg_ms
FROM descendants
WHERE name IN ('traversal', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY name ORDER BY name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), doframes AS (
  SELECT s.id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
  WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid = (SELECT upid FROM app))
), roots AS (
  SELECT c.id FROM doframes AS d JOIN slice AS c ON c.parent_id = d.id WHERE c.name = 'traversal'
), descendants(id, name, dur, depth) AS (
  SELECT s.id, s.name, s.dur, 0 FROM roots AS r JOIN slice AS s ON s.id = r.id
  UNION ALL
  SELECT s.id, s.name, s.dur, d.depth + 1 FROM slice AS s JOIN descendants AS d ON s.parent_id = d.id WHERE d.depth < 8
)
SELECT name, count(*) AS occurrences, sum(dur) / 1e6 AS total_ms, avg(dur) / 1e6 AS avg_ms
FROM descendants
WHERE name IN ('traversal', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY name ORDER BY name
```

### c4. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 adds a scrolling FeedScreen drawWithContent path that creates List(GRAIN_SPECKS) with Random.nextFloat() on each active frame; the introduced constant is GRAIN_SPECKS = 1_000_000.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c5. The trace's large increase in Compose drawing time corresponds directly to the FeedScreen drawing change, making commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 the attributed regression commit rather than the other commits in the range.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), doframes AS (
  SELECT s.id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
  WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid = (SELECT upid FROM app))
), roots AS (
  SELECT c.id FROM doframes AS d JOIN slice AS c ON c.parent_id = d.id WHERE c.name = 'traversal'
), descendants(id, name, dur, depth) AS (
  SELECT s.id, s.name, s.dur, 0 FROM roots AS r JOIN slice AS s ON s.id = r.id
  UNION ALL
  SELECT s.id, s.name, s.dur, d.depth + 1 FROM slice AS s JOIN descendants AS d ON s.parent_id = d.id WHERE d.depth < 8
)
SELECT name, count(*) AS occurrences, sum(dur) / 1e6 AS total_ms, avg(dur) / 1e6 AS avg_ms
FROM descendants
WHERE name IN ('traversal', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY name ORDER BY name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), doframes AS (
  SELECT s.id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
  WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid = (SELECT upid FROM app))
), roots AS (
  SELECT c.id FROM doframes AS d JOIN slice AS c ON c.parent_id = d.id WHERE c.name = 'traversal'
), descendants(id, name, dur, depth) AS (
  SELECT s.id, s.name, s.dur, 0 FROM roots AS r JOIN slice AS s ON s.id = r.id
  UNION ALL
  SELECT s.id, s.name, s.dur, d.depth + 1 FROM slice AS s JOIN descendants AS d ON s.parent_id = d.id WHERE d.depth < 8
)
SELECT name, count(*) AS occurrences, sum(dur) / 1e6 AS total_ms, avg(dur) / 1e6 AS avg_ms
FROM descendants
WHERE name IN ('traversal', 'Record View#draw()', 'AndroidOwner:draw')
GROUP BY name ORDER BY name
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

## Caveats

- Only one capture is available for each build, so run-to-run variance cannot be quantified.
- The traces are emulator captures, and the trace localizes the cost to Compose drawing/traversal rather than providing a source-level stack frame for the exact Kotlin call.

## Run

`gpt-5.6-luna` on openai, effort high: 34 tool calls, $0.0265, 133 s.
Tokens: 36 input, 151,430 cache read, 32,660 cache write, 12,752 output.
