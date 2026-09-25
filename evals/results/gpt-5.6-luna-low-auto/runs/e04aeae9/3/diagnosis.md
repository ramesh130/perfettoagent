# Inconclusive

- **Metric:** `frame_p99_ms` +4.24 ms (66.91 → 71.15 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

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

### c1. The selected metric, UI frame p99, increased from 66.911833 ms in baseline to 71.153583 ms in current, a delta of 4.241749999999996 ms.

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

### c2. The slowest current frames are dominated by Buffer Stuffing and several include App Deadline Missed or SurfaceFlinger CPU Deadline Missed; the corresponding baseline tail shows the same jank categories.

The `current` trace: 15 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)) SELECT dur/1e6 AS frame_ms, jank_type FROM frames ORDER BY dur DESC LIMIT 15
```

The `baseline` trace: 15 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)) SELECT dur/1e6 AS frame_ms, jank_type FROM frames ORDER BY dur DESC LIMIT 15
```

### c3. The main-thread top-level work is largely Compose lazy prefetch in both traces; current totals are not higher for the main compose:lazy:prefetch:compose slice than baseline, so the trace does not directly identify a newly added expensive application operation.

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM wf WHERE upid=(SELECT upid FROM app)) SELECT s.name, count(*) AS n, sum(s.dur)/1e6 AS ms FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*' GROUP BY s.name ORDER BY ms DESC LIMIT 20
```

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC LIMIT 1), mt AS (SELECT DISTINCT ui_thread_utid utid FROM wf WHERE upid=(SELECT upid FROM app)) SELECT s.name, count(*) AS n, sum(s.dur)/1e6 AS ms FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM mt) AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*' GROUP BY s.name ORDER BY ms DESC LIMIT 20
```

### c4. The range contains a UI change that reduces Interests-row thumbnail size from 56 dp to 48 dp, but the trace evidence is insufficient to attribute the p99 tail to it.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side; p99 is particularly sensitive to outliers and run-to-run noise.
- The current run is a debuggable build on the sdk_gphone64_arm64 emulator.
- The range's other changes are predominantly comments, naming, padding, or UI sizing changes; no trace row directly names a changed method or class.

## Run

`gpt-5.6-luna` on openai, effort low: 19 tool calls, $0.0079, 58 s.
Tokens: 24 input, 59,160 cache read, 10,383 cache write, 3,409 output.
