# No regression

- **Metric:** `frame_p95_ms` -9.2 ms (81.5 → 72.3 ms)
- **Culprit:** none attributed
- **Verified:** 6 claims kept, 0 dropped; 15 of 15 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 81.5 | 72.3 | -9.2 |

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

### c1. The selected frame_p95_ms metric improved from 81.499417 ms in baseline to 72.295959 ms in current, a delta of -9.203457999999998 ms.

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

### c2. The measured workload is com.superplayer.demo on its UI thread; baseline has 676 window frames with 370 App Deadline Missed frames, while current has 730 frames with 308 missed frames.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, t.name AS ui_thread_name, t.utid,
       count(*) AS frame_count,
       sum(a.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames wf
JOIN actual_frame_timeline_slice a ON a.id=wf.id
JOIN process p ON p.upid=wf.upid
JOIN thread t ON t.utid=wf.ui_thread_utid
WHERE wf.upid=(SELECT upid FROM app)
GROUP BY p.name,t.name,t.utid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, t.name AS ui_thread_name, t.utid,
       count(*) AS frame_count,
       sum(a.jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed
FROM window_frames wf
JOIN actual_frame_timeline_slice a ON a.id=wf.id
JOIN process p ON p.upid=wf.upid
JOIN thread t ON t.utid=wf.ui_thread_utid
WHERE wf.upid=(SELECT upid FROM app)
GROUP BY p.name,t.name,t.utid
```

### c3. UI-thread Choreographer#doFrame work also decreased: average/max duration went from 14.764285/241.8275 ms in baseline to 13.2463794058824/184.794333 ms in current.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app) LIMIT 1
), doframes AS (
  SELECT s.dur FROM slice s JOIN thread_track tt ON tt.id=s.track_id
  WHERE tt.utid=(SELECT utid FROM ui) AND s.name GLOB 'Choreographer#doFrame *' AND s.dur>0
)
SELECT count(*) AS doframe_slices, sum(dur)/1e6 AS doframe_total_ms,
       avg(dur)/1e6 AS doframe_avg_ms, max(dur)/1e6 AS doframe_max_ms
FROM doframes
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app) LIMIT 1
), doframes AS (
  SELECT s.dur FROM slice s JOIN thread_track tt ON tt.id=s.track_id
  WHERE tt.utid=(SELECT utid FROM ui) AND s.name GLOB 'Choreographer#doFrame *' AND s.dur>0
)
SELECT count(*) AS doframe_slices, sum(dur)/1e6 AS doframe_total_ms,
       avg(dur)/1e6 AS doframe_avg_ms, max(dur)/1e6 AS doframe_max_ms
FROM doframes
```

### c4. The trace localizes the scenario to the Compose feed: baseline versus current lazy-prefetch composition totals were 437.405916 ms versus 303.598835 ms, and both traces contain FeedScreenKt activity.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app) LIMIT 1
)
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid=(SELECT utid FROM ui) AND s.name IN ('compose:lazy:prefetch:compose','compose:lazy:prefetch:idle_frame','compose:lazy:prefetch:apply')
GROUP BY s.name ORDER BY s.name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app) LIMIT 1
)
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id
WHERE tt.utid=(SELECT utid FROM ui) AND s.name IN ('compose:lazy:prefetch:compose','compose:lazy:prefetch:idle_frame','compose:lazy:prefetch:apply')
GROUP BY s.name ORDER BY s.name
```

The `baseline` trace: 2 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms
FROM slice
WHERE name GLOB '*com.superplayer.demo.FeedScreenKt*'
GROUP BY name ORDER BY total_ms DESC
```

The `current` trace: 2 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms
FROM slice
WHERE name GLOB '*com.superplayer.demo.FeedScreenKt*'
GROUP BY name ORDER BY total_ms DESC
```

### c5. The range contains three commits touching the localized FeedScreen file: b193e79f0e56772176eb487ba2b3872ec4ee8c10, c88d847da1b428721dc2f04acbf48447bb396876, and 2aabba6793e56620bbc60be6f996a6b54934af10.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
b193e79f0e56772176eb487ba2b3872ec4ee8c10
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
c88d847da1b428721dc2f04acbf48447bb396876
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
2aabba6793e56620bbc60be6f996a6b54934af10
```

### c6. A secondary aggregate moved in the opposite direction: synchronous UI-thread binder wait to SurfaceFlinger increased from 214.334244 ms across 336 transactions to 227.248289 ms across 352 transactions.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT server_process, aidl_name, count(*) AS txns, sum(client_dur)/1e6 AS wait_ms, max(client_dur)/1e6 AS max_wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0
  AND client_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY server_process, aidl_name
ORDER BY wait_ms DESC
LIMIT 30
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), frames AS (
  SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
)
SELECT server_process, aidl_name, count(*) AS txns, sum(client_dur)/1e6 AS wait_ms, max(client_dur)/1e6 AS max_wait_ms
FROM android_binder_txns
WHERE is_sync AND client_dur > 0
  AND client_utid IN (SELECT ui_thread_utid FROM frames)
GROUP BY server_process, aidl_name
ORDER BY wait_ms DESC
LIMIT 30
```

## Caveats

- Only one capture is available for each side, so the apparent improvement should be treated as directional rather than statistically conclusive.
- The selected frame metric includes RenderThread and SurfaceFlinger queueing; it localizes the outcome but does not by itself prove source-level causality.
- The opposite binder-wait movement means not every secondary signal improved, reinforcing the need for repeated captures before making a small-change claim.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 70 tool calls, $0.0432, 261 s.
Tokens: 42 input, 328,040 cache read, 52,939 cache write, 19,507 output.
