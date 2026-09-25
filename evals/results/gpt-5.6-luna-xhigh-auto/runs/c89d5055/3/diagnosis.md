# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 14 of 14 citations passed
- **Model's confidence:** high (never scored)

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

### c1. The app's UI-thread frame p95 worsened from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a delta of 31.337374 ms.

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

### c2. The regression localizes to com.superplayer.demo's main thread: TextLayout:initLayout occurred 288 times for 69.199128 ms in baseline, versus 1,859,699 times for 7,192.994139 ms in current.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, th.name AS thread_name, s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND th.name = 'uperplayer.demo' AND s.name = 'TextLayout:initLayout'
GROUP BY p.name, th.name, s.name
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, th.name AS thread_name, s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND th.name = 'uperplayer.demo' AND s.name = 'TextLayout:initLayout'
GROUP BY p.name, th.name, s.name
```

### c3. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 is the direct culprit: it changes FeedScreen.kt to use RowTitle with rememberTextMeasurer and a repeated measurer.measure sizing loop, matching the new TextLayout hotspot.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, th.name AS thread_name, s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND th.name = 'uperplayer.demo' AND s.name = 'TextLayout:initLayout'
GROUP BY p.name, th.name, s.name
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, th.name AS thread_name, s.name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS th ON th.utid = tt.utid
JOIN process AS p ON p.upid = th.upid
WHERE p.name = 'com.superplayer.demo' AND th.name = 'uperplayer.demo' AND s.name = 'TextLayout:initLayout'
GROUP BY p.name, th.name, s.name
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c4. GC activity corroborates allocation pressure from the same change: the app had 7 collections totaling 258.575876 ms in baseline, versus 203 collections totaling 13,632.500926 ms in current.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, p.pid, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
GROUP BY p.upid, p.name, p.pid
ORDER BY gc_ms DESC
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, p.pid, count(*) AS gc_count, sum(g.gc_dur) / 1e6 AS gc_ms
FROM android_garbage_collection_events AS g
JOIN process AS p USING (upid)
GROUP BY p.upid, p.name, p.pid
ORDER BY gc_ms DESC
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c5. The traces are similar in duration, but the current app produced 1,640 window frames versus 676 in the baseline, consistent with the added continuously animated feed rows and a reason to treat whole-trace GC totals as corroborating rather than the primary metric.

The `baseline` trace: 1 row.

```sql
SELECT (end_ts - start_ts) / 1e9 AS trace_duration_s, start_ts, end_ts
FROM trace_bounds
```

The `current` trace: 1 row.

```sql
SELECT (end_ts - start_ts) / 1e9 AS trace_duration_s, start_ts, end_ts
FROM trace_bounds
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, p.pid, t.name AS main_thread, count(*) AS frame_count
FROM window_frames AS f
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.upid = (SELECT upid FROM app)
GROUP BY p.name, p.pid, t.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, p.pid, t.name AS main_thread, count(*) AS frame_count
FROM window_frames AS f
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.upid = (SELECT upid FROM app)
GROUP BY p.name, p.pid, t.name
```

## Caveats

- This diagnosis compares one capture per side, so ordinary run-to-run noise cannot be ruled out; the large frame-time and TextLayout differences make a small-noise explanation unlikely.
- Both captures are emulator benchmark runs on sdk_gphone64_arm64 / SDK 36, and the recorded build is non-debuggable.
- The current capture has substantially more rendered frames, so absolute whole-trace GC time is supporting evidence rather than the primary regression metric.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 50 tool calls, $0.0290, 408 s.
Tokens: 36 input, 160,612 cache read, 35,522 cache write, 14,112 output.
