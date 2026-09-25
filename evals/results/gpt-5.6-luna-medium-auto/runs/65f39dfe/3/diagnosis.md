# Regression

- **Metric:** `frame_ui_time_p95_ms` +2.65 ms (32.53 → 35.18 ms)
- **Culprit:** `1d113d755374` (correlated); `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 32.53 | 35.18 | +2.65 |

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

### c1. The app UI-thread 95th-percentile frame time increased from 32.532333 ms to 35.181834 ms, a 2.649501 ms regression.

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

### c2. The localized work is on the main UI thread of com.superplayer.demo, especially traversal, draw-VRI[MainActivity], postAndWait, animation, and Recomposer:recompose slices. Their aggregate durations are higher in the current trace despite fewer occurrences.

The `baseline` trace: 25 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT al.upid,al.ui_thread_utid FROM android_frames_layers al WHERE al.layer_name NOT GLOB '*SurfaceView*'), a AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC LIMIT 1), u AS (SELECT ui_thread_utid FROM w JOIN a ON a.upid=w.upid) SELECT s.name,count(*) n,sum(s.dur)/1e6 total_ms,max(s.dur)/1e6 max_ms FROM slice s JOIN track tr ON tr.id=s.track_id JOIN thread_track tt ON tt.id=tr.id WHERE tt.utid IN (SELECT ui_thread_utid FROM u) GROUP BY s.name ORDER BY total_ms DESC LIMIT 25
```

The `current` trace: 25 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT al.upid,al.ui_thread_utid FROM android_frames_layers al WHERE al.layer_name NOT GLOB '*SurfaceView*'), a AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC LIMIT 1), u AS (SELECT ui_thread_utid FROM w JOIN a ON a.upid=w.upid) SELECT s.name,count(*) n,sum(s.dur)/1e6 total_ms,max(s.dur)/1e6 max_ms FROM slice s JOIN track tr ON tr.id=s.track_id JOIN thread_track tt ON tt.id=tr.id WHERE tt.utid IN (SELECT ui_thread_utid FROM u) GROUP BY s.name ORDER BY total_ms DESC LIMIT 25
```

### c3. The strongest range correlation is commit 1d113d755374a5a53047db5fbdb3d18385c0aa3f, which changed TvScreen's control-hide timeout from five seconds to four seconds; the current trace also shows more Compose animation and recomposition work. This is a correlation rather than a direct code-to-stack attribution.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
1d113d755374a5a53047db5fbdb3d18385c0aa3f
```

The `baseline` trace: 25 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT al.upid,al.ui_thread_utid FROM android_frames_layers al WHERE al.layer_name NOT GLOB '*SurfaceView*'), a AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC LIMIT 1), u AS (SELECT ui_thread_utid FROM w JOIN a ON a.upid=w.upid) SELECT s.name,count(*) n,sum(s.dur)/1e6 total_ms,max(s.dur)/1e6 max_ms FROM slice s JOIN track tr ON tr.id=s.track_id JOIN thread_track tt ON tt.id=tr.id WHERE tt.utid IN (SELECT ui_thread_utid FROM u) GROUP BY s.name ORDER BY total_ms DESC LIMIT 25
```

The `current` trace: 25 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT al.upid,al.ui_thread_utid FROM android_frames_layers al WHERE al.layer_name NOT GLOB '*SurfaceView*'), a AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC LIMIT 1), u AS (SELECT ui_thread_utid FROM w JOIN a ON a.upid=w.upid) SELECT s.name,count(*) n,sum(s.dur)/1e6 total_ms,max(s.dur)/1e6 max_ms FROM slice s JOIN track tr ON tr.id=s.track_id JOIN thread_track tt ON tt.id=tr.id WHERE tt.utid IN (SELECT ui_thread_utid FROM u) GROUP BY s.name ORDER BY total_ms DESC LIMIT 25
```

### c4. The blamed TvScreen timeout line was introduced by the attributed commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
1d113d755374a5a53047db5fbdb3d18385c0aa3f
```

## Caveats

- Only one capture is available for each build, so run-to-run variation cannot be ruled out.
- The traces were captured on an Android emulator, and the build was non-debuggable benchmark software.
- The trace evidence identifies Compose/UI-thread work but does not contain a source-level stack frame proving that the timeout change itself caused the extra work.

## Run

`gpt-5.6-luna` on openai, effort medium: 36 tool calls, $0.0147, 106 s.
Tokens: 39 input, 122,829 cache read, 15,541 cache write, 6,961 output.
