# Regression

- **Metric:** `frame_p95_ms` +16.1 ms (19.91 → 36.01 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
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

### c1. The app's frame p95 increased from 19.914166 ms in the baseline trace to 36.011542 ms in the current trace, a 16.097375999999997 ms increase.

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

### c2. The slowdown is localized to the UI rendering path: current-trace traversal totals 171.38 ms across 78 slices with a 15.68 ms maximum, versus 115.21 ms across 76 slices with an 8.54 ms maximum in the baseline; current also has a 19.21 ms input-delivery slice.

The `baseline` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1), ui AS (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app)) SELECT s.name, count(*) AS n, round(sum(s.dur)/1e6,2) AS total_ms, round(max(s.dur)/1e6,2) AS max_ms FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT ui_thread_utid FROM ui) AND s.name NOT LIKE 'Choreographer#doFrame%' GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1), ui AS (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app)) SELECT s.name, count(*) AS n, round(sum(s.dur)/1e6,2) AS total_ms, round(max(s.dur)/1e6,2) AS max_ms FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT ui_thread_utid FROM ui) AND s.name NOT LIKE 'Choreographer#doFrame%' GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

### c3. The most plausible matching range commit is ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1, which changed the Interests topic-selection button from 36 dp to 40 dp and therefore can affect the Compose UI rendering workload.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side, so run-to-run variance cannot be ruled out.
- The current capture is a debuggable build on an Android emulator.
- The trace evidence does not directly identify SelectTopicButton.kt at runtime; the attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort low: 18 tool calls, $0.0080, 34 s.
Tokens: 21 input, 55,699 cache read, 11,429 cache write, 3,393 output.
