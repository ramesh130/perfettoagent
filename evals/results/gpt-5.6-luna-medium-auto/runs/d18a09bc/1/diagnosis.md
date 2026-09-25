# Regression

- **Metric:** `frame_ui_time_p95_ms` +3.54 ms (8.47 → 12 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 8.47 | 12 | +3.54 |

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

### c1. The app UI-thread frame p95 increased from 8.4665 ms in the baseline to 12.004708 ms in the current trace, a delta of 3.538208 ms.

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

### c2. The localized work is in the com.example.jetnews UI thread: its current trace contains 84 doFrame slices totaling 234.90229 ms, versus 82 slices totaling 169.44596 ms in the baseline.

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT t.name AS thread_name, p.name AS process_name, COUNT(*) AS frames, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON tt.id=s.track_id
JOIN thread AS t ON t.utid=tt.utid
JOIN process AS p ON p.upid=t.upid
GROUP BY t.utid
ORDER BY total_ms DESC
```

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT t.name AS thread_name, p.name AS process_name, COUNT(*) AS frames, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON tt.id=s.track_id
JOIN thread AS t ON t.utid=tt.utid
JOIN process AS p ON p.upid=t.upid
GROUP BY t.utid
ORDER BY total_ms DESC
```

### c3. The current trace's slowest app doFrame slices reached 16.207208 ms and 15.953792 ms, while the baseline's slowest app doFrame reached 13.858792 ms.

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT s.name, s.dur / 1e6 AS dur_ms, t.name AS thread_name, p.name AS process_name
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
ORDER BY s.dur DESC
LIMIT 20
```

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT s.name, s.dur / 1e6 AS dur_ms, t.name AS thread_name, p.name AS process_name
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
ORDER BY s.dur DESC
LIMIT 20
```

### c4. The strongest range correlation is commit ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1, which changes the Compose SelectTopicButton layout from 36 dp to 40 dp; blame at the range head assigns the 40 dp line to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so the p95 difference may include run-to-run variability.
- The traces were recorded on an emulator (sdk_gphone64_arm64, SDK 36) using a debuggable debug build.
- The attribution is correlated rather than direct: the trace localizes the increase to Compose/UI-thread frame work but does not identify SelectTopicButton specifically.

## Run

`gpt-5.6-luna` on openai, effort medium: 31 tool calls, $0.0129, 53 s.
Tokens: 30 input, 83,361 cache read, 16,228 cache write, 5,978 output.
