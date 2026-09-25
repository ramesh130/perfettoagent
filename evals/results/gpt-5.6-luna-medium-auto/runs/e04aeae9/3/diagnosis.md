# No regression

- **Metric:** `frame_p95_ms` -0.47 ms (59.13 → 58.65 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

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

### c1. The selected frame p95 metric improved slightly, from 59.127166 ms in the baseline to 58.652709 ms in the current trace, a delta of -0.474457000000001 ms; this is not evidence of a performance regression.

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

### c2. The main-thread blocked-time metric increased from 0.000584 ms to 1.431957 ms, but the current trace attributes the dominant new overlap to the MSG_CHECK_INVALIDATION_IDLE slice rather than to a changed application method.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)), work AS (SELECT s.id,s.name,s.ts,s.dur FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts,dur FROM thread_state WHERE utid IN (SELECT utid FROM main_thread) AND dur>0 AND state NOT IN ('Running','R','+')) SELECT w.name, sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms, count(*) AS overlaps FROM blocked b JOIN work w ON b.ts<w.ts+w.dur AND w.ts<b.ts+b.dur GROUP BY w.name ORDER BY blocked_ms DESC LIMIT 20
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)), work AS (SELECT s.id,s.name,s.ts,s.dur FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts,dur,state FROM thread_state WHERE utid IN (SELECT utid FROM main_thread) AND dur>0 AND state NOT IN ('Running','R','+')) SELECT w.name, sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms, count(*) AS overlaps FROM blocked b JOIN work w ON b.ts<w.ts+w.dur AND w.ts<b.ts+b.dur GROUP BY w.name ORDER BY blocked_ms DESC LIMIT 20
```

### c3. The range contains no trace-backed culprit: the only localized blocked slice newly observed is a runtime invalidation-idle event, and the frame p95 moved in the favorable direction.

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main_thread AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)), work AS (SELECT s.id,s.name,s.ts,s.dur FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main_thread) AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*'), blocked AS (SELECT ts,dur,state FROM thread_state WHERE utid IN (SELECT utid FROM main_thread) AND dur>0 AND state NOT IN ('Running','R','+')) SELECT w.name, sum(min(b.ts+b.dur,w.ts+w.dur)-max(b.ts,w.ts))/1e6 AS blocked_ms, count(*) AS overlaps FROM blocked b JOIN work w ON b.ts<w.ts+w.dur AND w.ts<b.ts+b.dur GROUP BY w.name ORDER BY blocked_ms DESC LIMIT 20
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture was available for each side, so the small frame-p95 difference may be run-to-run noise.
- The traces were captured on an Android emulator (sdk_gphone64_arm64, SDK 36) using a debuggable debug build.
- Startup and heap metrics had no data in either trace.

## Run

`gpt-5.6-luna` on openai, effort medium: 30 tool calls, $0.0127, 76 s.
Tokens: 21 input, 66,692 cache read, 18,334 cache write, 5,635 output.
