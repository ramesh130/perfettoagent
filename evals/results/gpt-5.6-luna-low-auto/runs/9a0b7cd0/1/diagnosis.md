# No regression

- **Metric:** `frame_ui_time_p95_ms` +0.34 ms (26.21 → 26.55 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.21 | 26.55 | +0.34 |

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

### c1. The selected UI-frame metric increased only slightly, from 26.206625 ms to 26.550666 ms, a delta of 0.344041 ms; this is too small to distinguish from single-capture run-to-run noise.

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

### c2. The measured UI work is concentrated in the app's main thread, named com.example.jetnews, in both captures.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT t.tid, t.name, p.pid, p.name AS process_name, count(*) AS do_frame_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING(id) JOIN thread AS t ON t.utid=d.ui_thread_utid JOIN process AS p ON p.upid=t.upid GROUP BY t.tid,t.name,p.pid,p.name ORDER BY total_ms DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT t.tid, t.name, p.pid, p.name AS process_name, count(*) AS do_frame_count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING(id) JOIN thread AS t ON t.utid=d.ui_thread_utid JOIN process AS p ON p.upid=t.upid GROUP BY t.tid,t.name,p.pid,p.name ORDER BY total_ms DESC
```

### c3. The range's commits are predominantly documentation/comment, resource, or small UI changes, and the traces do not provide evidence tying any of them to a measurable regression.

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/JetnewsApp.kt`:

```text
163301362edcab39cc39c8a7d32358d7d4f66f85
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/HomeScreens.kt`:

```text
1bc57bc0a107c1b2c8d6453d3689b26c5d00af37
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available per side, so small percentile changes are noisy.
- The current capture is a debuggable build on the sdk_gphone64_arm64 emulator; emulator and debug-build variability can affect frame timing.

## Run

`gpt-5.6-luna` on openai, effort low: 15 tool calls, $0.0060, 38 s.
Tokens: 18 input, 35,531 cache read, 7,791 cache write, 2,757 output.
