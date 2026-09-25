# Regression

- **Metric:** `frame_p95_ms` +16.1 ms (19.91 → 36.01 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 19.91 | 36.01 | +16.1 |

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

### c1. The app window-frame p95 increased from 19.914166 ms in the baseline to 36.011542 ms in the current trace, a +16.097375999999997 ms delta.

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

### c2. The affected frame population is com.example.jetnews on its example.jetnews UI thread: the baseline has 75 frames with one App Deadline Missed frame, while current has 77 frames with five.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
)
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, count(*) AS frame_count,
  sum(w.dur) / 1e6 AS total_frame_ms,
  avg(w.dur) / 1e6 AS avg_frame_ms,
  max(w.dur) / 1e6 AS max_frame_ms,
  sum(w.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames AS w
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = w.ui_thread_utid
GROUP BY p.name, p.pid, t.name
ORDER BY frame_count DESC;
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
)
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, count(*) AS frame_count,
  sum(w.dur) / 1e6 AS total_frame_ms,
  avg(w.dur) / 1e6 AS avg_frame_ms,
  max(w.dur) / 1e6 AS max_frame_ms,
  sum(w.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames AS w
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = w.ui_thread_utid
GROUP BY p.name, p.pid, t.name
ORDER BY frame_count DESC;
```

### c3. The slowdown is localized to UI-thread traversal and input/layout work: traversal rose from 115.213079 ms to 171.379503 ms, postAndWait from 63.531836 ms to 117.467704 ms, measure/layout from 12.682457 ms to 15.584209 ms, and onTouch from 23.862459 ms to 28.993002 ms.

The `baseline` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM mt) AND s.name IN ('traversal','postAndWait','AndroidOwner:measureAndLayout','AndroidOwner:onTouch','Recomposer:recompose','Compose:recompose')
GROUP BY s.name ORDER BY s.name;
```

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM mt) AND s.name IN ('traversal','postAndWait','AndroidOwner:measureAndLayout','AndroidOwner:onTouch','Recomposer:recompose','Compose:recompose')
GROUP BY s.name ORDER BY s.name;
```

### c4. The strongest range correlation is ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1, which changes SelectTopicButton's geometry from 36 dp to 40 dp; blame assigns the changed size line to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so run-to-run variance cannot be ruled out completely.
- The captures are from a debuggable build on an emulator, and the trace does not provide a source-level stack frame directly connecting the generic Compose traversal slices to SelectTopicButton.

## Run

`gpt-5.6-luna` on openai, effort high: 49 tool calls, $0.0224, 105 s.
Tokens: 36 input, 178,071 cache read, 26,643 cache write, 10,180 output.
