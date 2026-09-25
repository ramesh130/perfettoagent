# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The requested UI-frame metric regressed: frame_ui_time_p95_ms increased from 26.299542 ms in baseline to 103.761958 ms in current, a delta of 77.462416 ms.

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

### c2. The affected process is com.example.jetnews on its example.jetnews UI thread. Its maximum doFrame duration increased from 59.515916 ms in baseline to 268.590125 ms in current, and total doFrame time also increased substantially.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  p.name AS process_name,
  t.name AS thread_name,
  t.tid,
  COUNT(*) AS do_frame_count,
  MAX(s.dur) / 1e6 AS max_do_frame_ms,
  SUM(s.dur) / 1e6 AS total_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
GROUP BY p.name, t.name, t.tid
ORDER BY total_do_frame_ms DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  p.name AS process_name,
  t.name AS thread_name,
  t.tid,
  COUNT(*) AS do_frame_count,
  MAX(s.dur) / 1e6 AS max_do_frame_ms,
  SUM(s.dur) / 1e6 AS total_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
GROUP BY p.name, t.name, t.tid
ORDER BY total_do_frame_ms DESC
```

### c3. On the app's UI thread, traversal time increased from 15,897.080876 ms across 2,221 slices in baseline to 51,181.976438 ms across 1,826 slices in current; animation time also increased from 2,626.393501 ms to 5,036.788245 ms.

The `baseline` trace: 5 rows.

```sql
SELECT
  p.name AS process_name,
  t.name AS thread_name,
  s.name,
  COUNT(*) AS occurrences,
  SUM(s.dur) / 1e6 AS total_ms,
  MAX(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
WHERE s.name IN ('traversal', 'animation')
GROUP BY p.name, t.name, s.name
ORDER BY s.name, total_ms DESC
```

The `current` trace: 5 rows.

```sql
SELECT
  p.name AS process_name,
  t.name AS thread_name,
  s.name,
  COUNT(*) AS occurrences,
  SUM(s.dur) / 1e6 AS total_ms,
  MAX(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
WHERE s.name IN ('traversal', 'animation')
GROUP BY p.name, t.name, s.name
ORDER BY s.name, total_ms DESC
```

### c4. The likely culprit is commit e15d633e79d2608f074e9c50a18f3064e15830d7. It changes PostCards.kt by adding repeated text measurement in PostTitle and an infinite row-breath animation, matching the increased traversal and animation work observed in the current trace.

The `current` trace: 5 rows.

```sql
SELECT
  p.name AS process_name,
  t.name AS thread_name,
  s.name,
  COUNT(*) AS occurrences,
  SUM(s.dur) / 1e6 AS total_ms,
  MAX(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t USING (utid)
JOIN process AS p USING (upid)
WHERE s.name IN ('traversal', 'animation')
GROUP BY p.name, t.name, s.name
ORDER BY s.name, total_ms DESC
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

### c5. Blame at the range head assigns the new PostTitle measurement loop and rowBreath animation code to e15d633e79d2608f074e9c50a18f3064e15830d7.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available, so run-to-run variability cannot be estimated.
- The captures are from a debuggable debug build on an emulator.
- The trace slices are generic Compose traversal and animation spans rather than direct source-level PostCards symbols, so the culprit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 28 tool calls, $0.0159, 127 s.
Tokens: 30 input, 104,473 cache read, 18,249 cache write, 7,731 output.
