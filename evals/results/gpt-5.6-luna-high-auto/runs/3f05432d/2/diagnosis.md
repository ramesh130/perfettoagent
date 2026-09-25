# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The app UI-time p95 increased from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a 77.462416 ms regression.

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

### c2. The measured app is com.example.jetnews, and its UI thread is example.jetnews; the traces contain 2138 baseline frames and 1823 current frames for that thread.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)) SELECT p.name AS process_name, p.pid, t.name AS ui_thread, t.tid, count(*) AS frame_count FROM frames JOIN process AS p USING (upid) JOIN thread AS t ON t.utid = frames.ui_thread_utid GROUP BY p.name, p.pid, t.name, t.tid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)) SELECT p.name AS process_name, p.pid, t.name AS ui_thread, t.tid, count(*) AS frame_count FROM frames JOIN process AS p USING (upid) JOIN thread AS t ON t.utid = frames.ui_thread_utid GROUP BY p.name, p.pid, t.name, t.tid
```

### c3. Text layout work is absent in the baseline but dominates the current UI thread: current has 536157 TextLayout:initLayout slices taking 14372.316042 ms, plus the same number of Constructing StaticLayout slices taking 11049.010378 ms; baseline has zero of both.

The `baseline` trace: 1 row.

```sql
SELECT sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices, sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms, sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices, sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id JOIN thread AS t ON t.utid = tt.utid WHERE t.name = 'example.jetnews' AND s.dur > 0
```

The `current` trace: 1 row.

```sql
SELECT sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices, sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms, sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices, sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id JOIN thread AS t ON t.utid = tt.utid WHERE t.name = 'example.jetnews' AND s.dur > 0
```

### c4. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 added the PostCards.kt title-fitting implementation, including repeated text measurement; this directly matches the new text-layout work and is the attributed cause of the regression.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

The `current` trace: 1 row.

```sql
SELECT sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN 1 ELSE 0 END) AS text_layout_slices, sum(CASE WHEN s.name = 'TextLayout:initLayout' THEN s.dur ELSE 0 END) / 1e6 AS text_layout_ms, sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN 1 ELSE 0 END) AS static_layout_slices, sum(CASE WHEN s.name = 'Constructing StaticLayout' THEN s.dur ELSE 0 END) / 1e6 AS static_layout_ms FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id JOIN thread AS t ON t.utid = tt.utid WHERE t.name = 'example.jetnews' AND s.dur > 0
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, and the traces contain different numbers of UI frames, so repeated captures would be needed to quantify run-to-run variability.

## Run

`gpt-5.6-luna` on openai, effort high: 48 tool calls, $0.0237, 282 s.
Tokens: 33 input, 156,405 cache read, 35,598 cache write, 9,712 output.
