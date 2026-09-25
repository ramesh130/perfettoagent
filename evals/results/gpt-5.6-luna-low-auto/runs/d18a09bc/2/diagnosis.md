# Regression

- **Metric:** `frame_ui_time_p95_ms` +3.54 ms (8.47 → 12 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

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

### c1. The app UI thread's 95th-percentile frame time increased from 8.4665 ms to 12.004708 ms, a 3.538208 ms increase.

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

### c2. The trace localization shows more time in UI-related traversal and drawing slices in the current trace: traversal totaled 173.592044 ms versus 123.55962 ms in baseline, and draw-VRI[MainActivity] totaled 169.546207 ms versus 113.522377 ms.

The `baseline` trace: 30 rows.

```sql
SELECT name, COUNT(*) AS count, MAX(dur)/1e6 AS max_ms, SUM(dur)/1e6 AS total_ms FROM slice WHERE dur > 0 GROUP BY name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

```sql
SELECT name, COUNT(*) AS count, MAX(dur)/1e6 AS max_ms, SUM(dur)/1e6 AS total_ms FROM slice WHERE dur > 0 GROUP BY name ORDER BY total_ms DESC LIMIT 30
```

### c3. Commit ef58dc9 changed SelectTopicButton from a 36 dp by 36 dp size to 40 dp by 40 dp; the modified line is attributed to that commit by blame.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

### c4. The size change is the strongest correlated candidate in the range because it directly changes a composable used by InterestsScreen, while the trace evidence identifies increased UI traversal and drawing rather than a backend or build-time change.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

The `current` trace: 30 rows.

```sql
SELECT name, COUNT(*) AS count, MAX(dur)/1e6 AS max_ms, SUM(dur)/1e6 AS total_ms FROM slice WHERE dur > 0 GROUP BY name ORDER BY total_ms DESC LIMIT 30
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so some of the increase may be run-to-run noise.
- The captures were made on an Android emulator (sdk_gphone64_arm64, SDK 36) using a debuggable debug build.
- The trace does not directly connect the traversal slices to SelectTopicButton, so the culprit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort low: 14 tool calls, $0.0063, 31 s.
Tokens: 21 input, 45,125 cache read, 8,580 cache write, 2,680 output.
