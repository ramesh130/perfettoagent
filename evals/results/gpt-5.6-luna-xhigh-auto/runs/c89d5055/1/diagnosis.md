# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. The app UI-time p95 increased from 37.952167 ms in baseline to 69.289541 ms in current, a 31.337374 ms regression.

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

### c2. The regression localizes to com.superplayer.demo's UI thread. Depth-one traversal slices increased from 603 totaling 5160.408 ms in baseline to 849 totaling 20488.443 ms in current.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  main AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  do_frames AS (
    SELECT s.dur FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT utid FROM main)
  )
SELECT p.name AS process_name, th.name AS ui_thread_name,
       (SELECT count(*) FROM window_frames WHERE upid = (SELECT upid FROM app)) AS window_frames,
       (SELECT count(*) FROM do_frames) AS do_frames,
       round((SELECT dur FROM (SELECT dur, row_number() OVER (ORDER BY dur) AS r, count(*) OVER () AS n FROM do_frames) WHERE r=(n*95+99)/100)/1e6,3) AS do_frame_p95_ms,
       (SELECT count(*) FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main) AND s.depth=1 AND s.name='traversal') AS traversal_slices,
       round((SELECT sum(s.dur) FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main) AND s.depth=1 AND s.name='traversal')/1e6,3) AS traversal_total_ms
FROM process p JOIN thread th ON th.utid=(SELECT utid FROM main)
WHERE p.upid=(SELECT upid FROM app)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f
    JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
  ),
  app AS (
    SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
  ),
  main AS (
    SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  do_frames AS (
    SELECT s.dur FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT utid FROM main)
  )
SELECT p.name AS process_name, th.name AS ui_thread_name,
       (SELECT count(*) FROM window_frames WHERE upid = (SELECT upid FROM app)) AS window_frames,
       (SELECT count(*) FROM do_frames) AS do_frames,
       round((SELECT dur FROM (SELECT dur, row_number() OVER (ORDER BY dur) AS r, count(*) OVER () AS n FROM do_frames) WHERE r=(n*95+99)/100)/1e6,3) AS do_frame_p95_ms,
       (SELECT count(*) FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main) AND s.depth=1 AND s.name='traversal') AS traversal_slices,
       round((SELECT sum(s.dur) FROM slice s JOIN thread_track t ON t.id=s.track_id WHERE t.utid IN (SELECT utid FROM main) AND s.depth=1 AND s.name='traversal')/1e6,3) AS traversal_total_ms
FROM process p JOIN thread th ON th.utid=(SELECT utid FROM main)
WHERE p.upid=(SELECT upid FROM app)
```

### c3. The implicated range commit adds a per-row infinite "row breath" animation that changes horizontal padding, and replaces the ordinary row title with a BoxWithConstraints/text-measurement fitting loop in FeedScreen.kt.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c4. The trace/code correlation supports attributing the traversal regression to 18fab3f92d84e00498a5a6891125dd23bd063820: current has 849 depth-one animation slices versus 536 in baseline, while traversal averages 24.132 ms versus 8.558 ms.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,3) AS total_ms, round(avg(s.dur)/1e6,3) AS avg_ms, round(max(s.dur)/1e6,3) AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM main) AND s.depth=1 AND s.name IN ('traversal','AndroidOwner:measureAndLayout','animation') AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
    FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
    WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
  ), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), main AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,3) AS total_ms, round(avg(s.dur)/1e6,3) AS avg_ms, round(max(s.dur)/1e6,3) AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM main) AND s.depth=1 AND s.name IN ('traversal','AndroidOwner:measureAndLayout','animation') AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c5. Neither trace contains sampled stack_profile samples, so source-level attribution is correlated rather than direct.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS stack_sample_count FROM stack_sample
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS stack_sample_count FROM stack_sample
```

## Caveats

- There is one capture per side, so percentile metrics can include run-to-run noise.
- The current run metadata describes a non-debuggable benchmark build on an emulator; the attribution should be validated with a repeat capture or sampled callstack data.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 52 tool calls, $0.0357, 316 s.
Tokens: 45 input, 255,572 cache read, 39,505 cache write, 17,270 output.
