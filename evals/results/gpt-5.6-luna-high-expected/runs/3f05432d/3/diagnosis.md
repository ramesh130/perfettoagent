# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.3 | 103.76 | +77.46 |

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

### c1. The app UI-time p95 increased from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a delta of 77.462416 ms.

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

### c2. The affected UI work is on com.example.jetnews's example.jetnews thread: it accounts for 2305 doFrame slices in the baseline and 1825 in the current trace, with the maximum doFrame growing from 59.515916 ms to 268.590125 ms.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, d.ui_thread_utid, COUNT(*) AS do_frame_count, MAX(s.dur) / 1e6 AS max_do_frame_ms, AVG(s.dur) / 1e6 AS avg_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p USING (upid)
GROUP BY p.name, t.name, d.ui_thread_utid
ORDER BY do_frame_count DESC;
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, d.ui_thread_utid, COUNT(*) AS do_frame_count, MAX(s.dur) / 1e6 AS max_do_frame_ms, AVG(s.dur) / 1e6 AS avg_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p USING (upid)
GROUP BY p.name, t.name, d.ui_thread_utid
ORDER BY do_frame_count DESC;
```

### c3. In the app's doFrame slices, traversal was the dominant child slice. Its p95 duration increased from 22.509666 ms in the baseline to 91.09875 ms in the current trace; its total duration also increased despite fewer traversal occurrences.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH traversal AS (
  SELECT child.dur AS ns
  FROM android_frames_choreographer_do_frame AS d
  JOIN slice AS frame ON frame.id = d.id
  JOIN thread AS t ON t.utid = d.ui_thread_utid
  JOIN process AS p ON p.upid = t.upid
  JOIN slice AS child ON child.parent_id = frame.id
  WHERE p.name = 'com.example.jetnews' AND child.name = 'traversal' AND child.dur > 0
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n FROM traversal
)
SELECT COUNT(*) AS traversal_count, SUM(ns) / 1e6 AS traversal_total_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS traversal_p95_ms
FROM traversal;
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH traversal AS (
  SELECT child.dur AS ns
  FROM android_frames_choreographer_do_frame AS d
  JOIN slice AS frame ON frame.id = d.id
  JOIN thread AS t ON t.utid = d.ui_thread_utid
  JOIN process AS p ON p.upid = t.upid
  JOIN slice AS child ON child.parent_id = frame.id
  WHERE p.name = 'com.example.jetnews' AND child.name = 'traversal' AND child.dur > 0
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n FROM traversal
)
SELECT COUNT(*) AS traversal_count, SUM(ns) / 1e6 AS traversal_total_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS traversal_p95_ms
FROM traversal;
```

### c4. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 is the range commit that changed the home-feed UI file PostCards.kt. It is the likely correlated culprit for the traversal and frame-time regression.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH traversal AS (
  SELECT child.dur AS ns
  FROM android_frames_choreographer_do_frame AS d
  JOIN slice AS frame ON frame.id = d.id
  JOIN thread AS t ON t.utid = d.ui_thread_utid
  JOIN process AS p ON p.upid = t.upid
  JOIN slice AS child ON child.parent_id = frame.id
  WHERE p.name = 'com.example.jetnews' AND child.name = 'traversal' AND child.dur > 0
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n FROM traversal
)
SELECT COUNT(*) AS traversal_count, SUM(ns) / 1e6 AS traversal_total_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS traversal_p95_ms
FROM traversal;
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so run-to-run noise cannot be quantified.
- The captures are from a debuggable build on an Android SDK 36 emulator.
- No source-level stack sample was available to make the commit attribution direct; the culprit is therefore marked correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 49 tool calls, $0.0226, 209 s.
Tokens: 45 input, 184,977 cache read, 29,713 cache write, 9,560 output.
