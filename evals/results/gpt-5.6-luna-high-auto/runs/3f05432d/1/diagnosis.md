# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 11 of 11 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

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

### c1. The app's UI-thread p95 frame time increased from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a 77.462416 ms regression.

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

### c2. The slowdown is on the app UI thread: the baseline has 2,305 doFrame slices with a 26.299542 ms p95, while the current trace has 1,825 with a 103.761958 ms p95 and a 268.590125 ms maximum.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)), do_frames AS (SELECT s.dur FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)), ranked AS (SELECT dur / 1e6 AS ms, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n FROM do_frames) SELECT COUNT(*) AS do_frame_count, (SELECT ms FROM ranked WHERE rank = (n * 95 + 99) / 100) AS ui_p95_ms, AVG(ms) AS ui_avg_ms, MAX(ms) AS ui_max_ms FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)), do_frames AS (SELECT s.dur FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)), ranked AS (SELECT dur / 1e6 AS ms, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n FROM do_frames) SELECT COUNT(*) AS do_frame_count, (SELECT ms FROM ranked WHERE rank = (n * 95 + 99) / 100) AS ui_p95_ms, AVG(ms) AS ui_avg_ms, MAX(ms) AS ui_max_ms FROM ranked
```

### c3. The current trace introduced substantial text-layout and Compose work: TextLayout:initLayout has 536157 slices totaling 14372.316042 ms, versus no such slices in the baseline; AndroidOwner:measureAndLayout also rose from 964.653869 ms to 39896.66464 ms.

The `baseline` trace: 4 rows.

```sql
WITH names(name) AS (SELECT 'TextLayout:initLayout' UNION ALL SELECT 'AndroidOwner:measureAndLayout' UNION ALL SELECT 'Compose:recompose' UNION ALL SELECT 'Recomposer:animation'), agg AS (SELECT name, COUNT(*) AS slice_count, SUM(dur) / 1e6 AS total_ms, MAX(dur) / 1e6 AS max_ms FROM slice WHERE name IN (SELECT name FROM names) GROUP BY name) SELECT n.name, COALESCE(a.slice_count, 0) AS slice_count, COALESCE(a.total_ms, 0) AS total_ms, COALESCE(a.max_ms, 0) AS max_ms FROM names AS n LEFT JOIN agg AS a USING (name) ORDER BY n.name
```

The `current` trace: 4 rows.

```sql
WITH names(name) AS (SELECT 'TextLayout:initLayout' UNION ALL SELECT 'AndroidOwner:measureAndLayout' UNION ALL SELECT 'Compose:recompose' UNION ALL SELECT 'Recomposer:animation'), agg AS (SELECT name, COUNT(*) AS slice_count, SUM(dur) / 1e6 AS total_ms, MAX(dur) / 1e6 AS max_ms FROM slice WHERE name IN (SELECT name FROM names) GROUP BY name) SELECT n.name, COALESCE(a.slice_count, 0) AS slice_count, COALESCE(a.total_ms, 0) AS total_ms, COALESCE(a.max_ms, 0) AS max_ms FROM names AS n LEFT JOIN agg AS a USING (name) ORDER BY n.name
```

### c4. Garbage collection corroborates the UI regression: com.example.jetnews increased from 3 collections totaling 59.403749 ms to 184 collections totaling 4498.861341 ms.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, p.pid, COUNT(*) AS gc_count, SUM(e.gc_dur) / 1e6 AS gc_ms, MAX(e.gc_dur) / 1e6 AS max_gc_ms FROM android_garbage_collection_events AS e JOIN process AS p ON p.upid = e.upid GROUP BY p.upid, p.name, p.pid ORDER BY gc_ms DESC
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, p.pid, COUNT(*) AS gc_count, SUM(e.gc_dur) / 1e6 AS gc_ms, MAX(e.gc_dur) / 1e6 AS max_gc_ms FROM android_garbage_collection_events AS e JOIN process AS p ON p.upid = e.upid GROUP BY p.upid, p.name, p.pid ORDER BY gc_ms DESC
```

### c5. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 is the likely culprit: it is the range commit that changed PostCards.kt, matching the new text-measurement and continuously animated row behavior seen in the current trace.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `baseline` trace: 4 rows.

```sql
WITH names(name) AS (SELECT 'TextLayout:initLayout' UNION ALL SELECT 'AndroidOwner:measureAndLayout' UNION ALL SELECT 'Compose:recompose' UNION ALL SELECT 'Recomposer:animation'), agg AS (SELECT name, COUNT(*) AS slice_count, SUM(dur) / 1e6 AS total_ms, MAX(dur) / 1e6 AS max_ms FROM slice WHERE name IN (SELECT name FROM names) GROUP BY name) SELECT n.name, COALESCE(a.slice_count, 0) AS slice_count, COALESCE(a.total_ms, 0) AS total_ms, COALESCE(a.max_ms, 0) AS max_ms FROM names AS n LEFT JOIN agg AS a USING (name) ORDER BY n.name
```

The `current` trace: 4 rows.

```sql
WITH names(name) AS (SELECT 'TextLayout:initLayout' UNION ALL SELECT 'AndroidOwner:measureAndLayout' UNION ALL SELECT 'Compose:recompose' UNION ALL SELECT 'Recomposer:animation'), agg AS (SELECT name, COUNT(*) AS slice_count, SUM(dur) / 1e6 AS total_ms, MAX(dur) / 1e6 AS max_ms FROM slice WHERE name IN (SELECT name FROM names) GROUP BY name) SELECT n.name, COALESCE(a.slice_count, 0) AS slice_count, COALESCE(a.total_ms, 0) AS total_ms, COALESCE(a.max_ms, 0) AS max_ms FROM names AS n LEFT JOIN agg AS a USING (name) ORDER BY n.name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each build, so ordinary run-to-run variance cannot be completely excluded; the magnitude and multiple corroborating signals make noise an unlikely explanation.
- The current run metadata identifies a debuggable emulator build. Attribution is marked correlated because the trace exposes Compose/framework slices rather than an app source line directly.

## Run

`gpt-5.6-luna` on openai, effort high: 39 tool calls, $0.0244, 263 s.
Tokens: 27 input, 120,170 cache read, 34,814 cache write, 11,108 output.
