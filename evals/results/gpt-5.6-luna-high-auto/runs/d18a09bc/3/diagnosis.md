# Regression

- **Metric:** `frame_p95_ms` +16.1 ms (19.91 → 36.01 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The app's UI-frame p95 increased from 19.914166 ms in the baseline to 36.011542 ms in the current trace, a delta of 16.097376 ms.

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

### c2. The affected process is com.example.jetnews on its example.jetnews UI thread; the trace contains 75 app frames in the baseline and 77 in the current trace, with App Deadline Missed frames increasing from 1 to 5.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, t.tid,
       count(*) AS frame_count, sum(fr.dur)/1e6 AS total_frame_ms,
       avg(fr.dur)/1e6 AS avg_frame_ms,
       max(fr.dur)/1e6 AS max_frame_ms,
       sum(fr.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames fr
JOIN app ON app.upid = fr.upid
JOIN process p ON p.upid = fr.upid
JOIN thread t ON t.utid = fr.ui_thread_utid
GROUP BY p.name, p.pid, t.name, t.tid
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
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, p.pid, t.name AS ui_thread_name, t.tid,
       count(*) AS frame_count, sum(fr.dur)/1e6 AS total_frame_ms,
       avg(fr.dur)/1e6 AS avg_frame_ms,
       max(fr.dur)/1e6 AS max_frame_ms,
       sum(fr.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames fr
JOIN app ON app.upid = fr.upid
JOIN process p ON p.upid = fr.upid
JOIN thread t ON t.utid = fr.ui_thread_utid
GROUP BY p.name, p.pid, t.name, t.tid
```

### c3. The UI-thread traversal work increased substantially: traversal rose from 115.213079 ms to 171.379503 ms in total, and postAndWait rose from 63.531836 ms to 117.467704 ms.

The `baseline` trace: 50 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ui AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT CASE
  WHEN s.name GLOB 'Choreographer#doFrame *' THEN 'Choreographer#doFrame'
  WHEN s.name GLOB 'deliverInputEvent *' THEN 'deliverInputEvent'
  ELSE s.name END AS slice_name,
  count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM ui) AND s.dur>0
GROUP BY slice_name ORDER BY total_ms DESC LIMIT 50
```

The `current` trace: 50 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ui AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT CASE
  WHEN s.name GLOB 'Choreographer#doFrame *' THEN 'Choreographer#doFrame'
  WHEN s.name GLOB 'deliverInputEvent *' THEN 'deliverInputEvent'
  ELSE s.name END AS slice_name,
  count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM ui) AND s.dur>0
GROUP BY slice_name ORDER BY total_ms DESC LIMIT 50
```

### c4. Commit ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1 changed SelectTopicButton from 36 dp to 40 dp. Blame at the range head attributes the new size line to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

### c5. The trace localizes the change to generic UI-thread traversal and rendering slices rather than to a source-level SelectTopicButton frame, so ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1 is a likely correlated culprit, not a direct trace attribution.

The `current` trace: 50 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ui AS (SELECT DISTINCT ui_thread_utid utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT CASE
  WHEN s.name GLOB 'Choreographer#doFrame *' THEN 'Choreographer#doFrame'
  WHEN s.name GLOB 'deliverInputEvent *' THEN 'deliverInputEvent'
  ELSE s.name END AS slice_name,
  count(*) AS slice_count, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid IN (SELECT utid FROM ui) AND s.dur>0
GROUP BY slice_name ORDER BY total_ms DESC LIMIT 50
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available; frame p95 is sensitive to a small number of frames, so the magnitude should be treated as directional.
- The source attribution is correlated because the trace contains generic Compose/View traversal slices rather than a source-level frame naming SelectTopicButton.

## Run

`gpt-5.6-luna` on openai, effort high: 51 tool calls, $0.0255, 119 s.
Tokens: 42 input, 240,407 cache read, 28,402 cache write, 11,303 output.
