# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 5 of 5 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 37.95 | 69.29 | +31.34 |

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

### c1. The app UI thread's p95 frame time increased from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a 31.337374 ms regression.

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

### c2. The current UI thread recorded 1,859,699 TextLayout:initLayout slices totaling 7,192.994 ms, along with 1,643 animation slices totaling 5,156.704 ms.

The `current` trace: 40 rows.

```sql
SELECT s.name, count(*) AS slices, round(sum(s.dur)/1e6,3) AS total_ms, round(max(s.dur)/1e6,3) AS max_ms FROM slice s JOIN thread_track tr ON tr.id=s.track_id WHERE tr.utid=2 AND s.dur>0 GROUP BY s.name ORDER BY total_ms DESC LIMIT 40
```

### c3. Commit 18fab3f adds an infinite per-row breathing animation and replaces the plain row title with RowTitle, which repeatedly measures text while searching font sizes.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c4. The lines implementing the breathing animation and RowTitle text measurement are blamed to commit 18fab3f92d84e00498a5a6891125dd23bd063820.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- Only one capture is available for each side, so run-to-run noise cannot be quantified.
- The traces were captured on an Android emulator, and the current build was a non-debuggable benchmark build.

## Run

`gpt-5.6-luna` on openai, effort medium: 43 tool calls, $0.0178, 207 s.
Tokens: 33 input, 135,341 cache read, 29,074 cache write, 6,504 output.
