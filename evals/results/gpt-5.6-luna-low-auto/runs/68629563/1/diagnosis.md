# Regression

- **Metric:** `frame_ui_time_p95_ms` +5.6 ms (8.36 → 13.96 ms)
- **Culprit:** `9d695fef3c75` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 8.36 | 13.96 | +5.6 |

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

### c1. The app UI-thread frame p95 increased from 8.3585 ms in the baseline to 13.957625 ms in the current trace, a delta of 5.599125 ms.

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

### c2. The current UI-thread trace contains a 9.210417 ms Choreographer#doFrame, including a 2.551708 ms postAndWait slice; the corresponding baseline frame was 1.9065 ms with a 0.540041 ms postAndWait slice.

The `baseline` trace: 12 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid, ui_thread_utid FROM wf GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC LIMIT 1) SELECT s.name, count(*) AS n, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid=(SELECT ui_thread_utid FROM app) AND s.dur>0 GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

The `current` trace: 11 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid, ui_thread_utid FROM wf GROUP BY upid,ui_thread_utid ORDER BY count(*) DESC LIMIT 1) SELECT s.name, count(*) AS n, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid=(SELECT ui_thread_utid FROM app) AND s.dur>0 GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

### c3. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 added Thread.sleep(BOOKMARK_HOLD_MS) inside the bookmark onClick handler in PostCards.kt, and blame attributes that line to this commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side, so smaller frame changes can contain run-to-run noise.
- The current run metadata identifies a debuggable build on an Android SDK 36 emulator.

## Run

`gpt-5.6-luna` on openai, effort low: 18 tool calls, $0.0070, 33 s.
Tokens: 18 input, 40,092 cache read, 11,250 cache write, 2,816 output.
