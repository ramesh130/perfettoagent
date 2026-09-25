# Inconclusive

- **Metric:** `frame_p99_ms` +4.24 ms (66.91 → 71.15 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 14 of 14 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p99_ms` | ms | 66.91 | 71.15 | +4.24 |

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

## Claims

### c1. Both captures localize the measured window frames to com.example.jetnews and its main thread, example.jetnews. The baseline has 2,107 frames with an 81.049 ms maximum, while current has 2,061 frames with an 82.93 ms maximum.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT p.pid, p.name AS process_name, t.tid, t.name AS thread_name,
       count(*) AS frame_count, round(avg(dur) / 1e6, 3) AS avg_frame_ms,
       round(max(dur) / 1e6, 3) AS max_frame_ms
FROM frames
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = frames.ui_thread_utid
GROUP BY p.pid, p.name, t.tid, t.name
ORDER BY frame_count DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT p.pid, p.name AS process_name, t.tid, t.name AS thread_name,
       count(*) AS frame_count, round(avg(dur) / 1e6, 3) AS avg_frame_ms,
       round(max(dur) / 1e6, 3) AS max_frame_ms
FROM frames
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = frames.ui_thread_utid
GROUP BY p.pid, p.name, t.tid, t.name
ORDER BY frame_count DESC
```

### c2. The presented-frame p99 increased from 66.911833 ms to 71.153583 ms, a 4.24175 ms worsening in the selected metric.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

### c3. The corresponding UI-thread doFrame p99 moved in the opposite direction, from 33.387042 ms to 32.4155 ms; the measured app-deadline-missed jank share also fell from 12.719506407214% to 12.2270742358079%.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0 GROUP BY f.upid ORDER BY count(*) DESC, f.upid LIMIT 1
), frames AS (
  SELECT DISTINCT f.frame_id FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0 AND f.upid=(SELECT upid FROM app)
), durs AS (
  SELECT s.dur, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
  FROM frames AS f JOIN android_frames_choreographer_do_frame AS d ON d.frame_id=f.frame_id JOIN slice AS s ON s.id=d.id
)
SELECT n AS do_frames,
       (SELECT dur/1e6 FROM durs WHERE rank=(n*95+99)/100) AS p95_ms,
       (SELECT dur/1e6 FROM durs WHERE rank=(n*99+99)/100) AS p99_ms,
       max(dur)/1e6 AS max_ms
FROM durs LIMIT 1
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app AS (
  SELECT f.upid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0 GROUP BY f.upid ORDER BY count(*) DESC, f.upid LIMIT 1
), frames AS (
  SELECT DISTINCT f.frame_id FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0 AND f.upid=(SELECT upid FROM app)
), durs AS (
  SELECT s.dur, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
  FROM frames AS f JOIN android_frames_choreographer_do_frame AS d ON d.frame_id=f.frame_id JOIN slice AS s ON s.id=d.id
)
SELECT n AS do_frames,
       (SELECT dur/1e6 FROM durs WHERE rank=(n*95+99)/100) AS p95_ms,
       (SELECT dur/1e6 FROM durs WHERE rank=(n*99+99)/100) AS p99_ms,
       max(dur)/1e6 AS max_ms
FROM durs LIMIT 1
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
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
  )
SELECT 100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS value
FROM frames
```

### c4. At the range head, blame assigns the Interests-row thumbnail size line to 91eb564a995b5f47ac2de9f35636027304e2d356 and the topic-selection button size line to 8cc4be474ff991ddc6a1a01e6e2af962039a8f85.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
8cc4be474ff991ddc6a1a01e6e2af962039a8f85
```

### c5. Because the adverse change is confined to the presented-frame tail while matched UI-thread tail work and app-deadline jank improved, the traces do not establish a range-caused regression or support assigning either UI commit as the culprit.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
8cc4be474ff991ddc6a1a01e6e2af962039a8f85
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- frame_p99_ms is sensitive to a small number of tail frames; one capture per side cannot distinguish run-to-run noise from a real tail regression.
- The current trace metadata identifies a debuggable debug build running on the sdk_gphone64_arm64 emulator.
- The traces did not expose source-level stack samples usable for direct attribution.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 67 tool calls, $0.0460, 240 s.
Tokens: 48 input, 369,550 cache read, 53,274 cache write, 21,056 output.
