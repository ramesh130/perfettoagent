# Regression

- **Metric:** `frame_p95_ms` +16.1 ms (19.91 → 36.01 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 3 claims kept, 1 dropped; 7 of 8 citations passed
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

### c2. The regression is localized to com.example.jetnews's traversal and postAndWait path: traversal rose from 115.213079 ms over 76 slices to 171.379503 ms over 78 slices, while postAndWait rose from 63.531836 ms to 117.467704 ms.

The `baseline` trace: 8 rows.

```sql
SELECT th.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid
WHERE s.name IN ('postAndWait','FillRectOp','flush commands','traversal','draw-VRI[MainActivity]')
GROUP BY th.name, s.name ORDER BY total_ms DESC;
```

The `current` trace: 8 rows.

```sql
SELECT th.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid
WHERE s.name IN ('postAndWait','FillRectOp','flush commands','traversal','draw-VRI[MainActivity]')
GROUP BY th.name, s.name ORDER BY total_ms DESC;
```

### c3. The frame timeline marked one baseline frame versus five current frames as App Deadline Missed, consistent with worse frame delivery in the current capture.

The `baseline` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (
 SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT coalesce(jank_type,'(none)') AS jank_type, count(*) AS frames, sum(dur)/1e6 AS total_frame_ms, max(dur)/1e6 AS max_frame_ms
FROM window_frames WHERE upid=(SELECT upid FROM app) GROUP BY jank_type ORDER BY frames DESC;
```

The `current` trace: 8 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
 WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (
 SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT coalesce(jank_type,'(none)') AS jank_type, count(*) AS frames, sum(dur)/1e6 AS total_frame_ms, max(dur)/1e6 AS max_frame_ms
FROM window_frames WHERE upid=(SELECT upid FROM app) GROUP BY jank_type ORDER BY frames DESC;
```

### c4. Commit ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1 changes the rendered SelectTopicButton size from 36 dp to 40 dp. Given the trace's rendering and traversal regression, this is the likely correlated culprit, but the trace does not contain a composable-level marker proving that this control caused the extra work.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

The `current` trace: 8 rows.

```sql
SELECT th.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread th ON th.utid=tt.utid
WHERE s.name IN ('postAndWait','FillRectOp','flush commands','traversal','draw-VRI[MainActivity]')
GROUP BY th.name, s.name ORDER BY total_ms DESC;
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so frame percentiles and jank counts remain subject to run-to-run noise.
- The current run metadata identifies a debuggable SDK 36 Android emulator; baseline build metadata is unavailable.
- The attribution is correlated rather than direct because the trace localizes generic traversal/render slices rather than the SelectTopicButton source method.

## Dropped claims

### c1. The app's frame p95 increased from 19.914166 ms in the baseline to 36.011542 ms in the current trace, a 16.097376 ms worsening.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
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

## Run

`gpt-5.6-luna` on openai, effort high: 73 tool calls, $0.0332, 152 s.
Tokens: 51 input, 337,666 cache read, 39,122 cache write, 13,864 output.
