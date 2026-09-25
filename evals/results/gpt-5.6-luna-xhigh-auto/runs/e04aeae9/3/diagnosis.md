# No regression

- **Metric:** `frame_p95_ms` -0.47 ms (59.13 → 58.65 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 59.13 | 58.65 | -0.47 |

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

### c1. The selected end-to-end frame p95 did not regress: it decreased from 59.127166 ms in baseline to 58.652709 ms in current, a delta of -0.474457 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ranked AS (
  SELECT dur, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
  FROM wf WHERE upid = (SELECT upid FROM app)
)
SELECT dur / 1e6 AS frame_p95_ms
FROM ranked WHERE rank = (n * 95 + 99) / 100
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ranked AS (
  SELECT dur, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
  FROM wf WHERE upid = (SELECT upid FROM app)
)
SELECT dur / 1e6 AS frame_p95_ms
FROM ranked WHERE rank = (n * 95 + 99) / 100
```

### c2. The frame-tail rows in both captures are dominated by Buffer Stuffing and Prediction Error labels, with App Deadline Missed also present; this points to frame-pipeline variability rather than a named application method.

The `baseline` trace: 10 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (
  SELECT DISTINCT f.upid, a.jank_type, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT jank_type, count(*) AS frames, max(dur) / 1e6 AS max_ms
FROM wf WHERE upid = (SELECT upid FROM app)
GROUP BY jank_type ORDER BY max_ms DESC LIMIT 10
```

The `current` trace: 10 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (
  SELECT DISTINCT f.upid, a.jank_type, a.dur
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT jank_type, count(*) AS frames, max(dur) / 1e6 AS max_ms
FROM wf WHERE upid = (SELECT upid FROM app)
GROUP BY jank_type ORDER BY max_ms DESC LIMIT 10
```

### c3. The concrete current-only blocking event examined is a Compose lazy-prefetch recompose waiting on a thread-suspend-count lock; the lock owner is the app's HeapTaskDaemon, which is running a young concurrent mark-compact GC.

The `current` trace: 3 rows.

```sql
SELECT s.id, s.ts, s.dur / 1e6 AS dur_ms, s.depth, s.name, s.parent_id,
       t.utid, t.name AS thread_name
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 365
  AND s.ts < 5252831270546 + 230916
  AND s.ts + s.dur > 5252831270546
ORDER BY s.ts, s.depth, s.dur DESC
```

The `current` trace: 1 row.

```sql
SELECT t.utid, t.tid, t.name, p.pid, p.name AS process_name
FROM thread AS t JOIN process AS p USING (upid)
WHERE t.tid = 32059
```

The `current` trace: 17 rows.

```sql
SELECT s.ts, s.dur / 1e6 AS dur_ms, s.depth, s.name, t.utid, t.tid, t.name AS thread_name
FROM slice AS s JOIN thread_track AS tt ON tt.id = s.track_id JOIN thread AS t ON t.utid = tt.utid
WHERE t.tid = 32059 AND s.ts < 5252833544879 + 1000000 AND s.ts + s.dur > 5252831270546 - 1000000
ORDER BY s.ts, s.depth
```

### c4. The range contains UI changes in InterestsScreen.kt and SelectTopicButton.kt, but the trace-localized adverse work is frame-pipeline and GC/lock activity rather than a directly identified changed source method; no commit is therefore attributed.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
8cc4be474ff991ddc6a1a01e6e2af962039a8f85
```

The `current` trace: 3 rows.

```sql
SELECT s.id, s.ts, s.dur / 1e6 AS dur_ms, s.depth, s.name, s.parent_id,
       t.utid, t.name AS thread_name
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
WHERE t.utid = 365
  AND s.ts < 5252831270546 + 230916
  AND s.ts + s.dur > 5252831270546
ORDER BY s.ts, s.depth, s.dur DESC
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- There is only one capture per side; the p95 change is small and should be treated as within run-to-run noise rather than a meaningful improvement.
- Frame p95 includes SurfaceFlinger queue and buffer-pipeline effects. The current run is a debuggable debug build on an Android emulator.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 76 tool calls, $0.0661, 315 s.
Tokens: 75 input, 916,096 cache read, 67,424 cache write, 25,755 output.
