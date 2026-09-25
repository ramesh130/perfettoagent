# Regression

- **Metric:** `frame_ui_time_p95_ms` +3.54 ms (8.47 → 12 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
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

### c1. The app's UI-thread frame p95 increased from 8.4665 ms in the baseline trace to 12.004708 ms in the current trace, a delta of 3.538208 ms.

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

### c2. The slow slices are concentrated in com.example.jetnews's RenderThread in both traces; current capture includes DrawFrames slices lasting 24.608333 ms and 24.541125 ms.

The `current` trace: 20 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name, s.dur / 1e6 AS dur_ms, s.ts / 1e6 AS ts_ms FROM slice s JOIN thread_track tt ON s.track_id = tt.id JOIN thread t ON tt.utid = t.utid JOIN process p ON t.upid = p.upid WHERE s.dur > 5000000 ORDER BY s.dur DESC LIMIT 20
```

The `baseline` trace: 20 rows.

```sql
SELECT p.name AS process_name, t.name AS thread_name, s.name, s.dur / 1e6 AS dur_ms, s.ts / 1e6 AS ts_ms FROM slice s JOIN thread_track tt ON s.track_id = tt.id JOIN thread t ON tt.utid = t.utid JOIN process p ON t.upid = p.upid WHERE s.dur > 5000000 ORDER BY s.dur DESC LIMIT 20
```

### c3. The range contains a UI change that increases SelectTopicButton from 36 dp to 40 dp.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

### c4. The changed 40 dp size line is attributed by blame to ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one capture per side, so the 3.538208 ms change may include run-to-run noise.
- The culprit attribution is correlated rather than direct: the trace localizes the cost to RenderThread drawing, but does not identify the SelectTopicButton code path.
- The current build is debuggable and ran on an Android emulator (sdk_gphone64_arm64, SDK 36).

## Run

`gpt-5.6-luna` on openai, effort low: 16 tool calls, $0.0058, 25 s.
Tokens: 18 input, 40,877 cache read, 7,373 cache write, 2,617 output.
