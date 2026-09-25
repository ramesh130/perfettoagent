# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 6 claims kept, 0 dropped; 12 of 12 citations passed
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

### c1. The app's UI-thread frame-time p95 increased from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a delta of 31.337373999999997 ms.

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

### c2. The changed work is on com.superplayer.demo's UI thread: tid 14487 in the baseline and tid 26057 in the current trace.

The `baseline` trace: 5 rows.

```sql
SELECT p.upid, p.pid, p.name, t.utid, t.tid, t.name AS thread_name, count(*) AS frame_count
FROM process AS p
JOIN thread AS t USING (upid)
JOIN thread_track AS tt USING (utid)
JOIN slice AS s ON s.track_id = tt.id
WHERE s.name GLOB 'Choreographer#doFrame*'
GROUP BY p.upid, p.pid, p.name, t.utid, t.tid, t.name
ORDER BY frame_count DESC
```

The `current` trace: 4 rows.

```sql
SELECT p.upid, p.pid, p.name, t.utid, t.tid, t.name AS thread_name, count(*) AS frame_count
FROM process AS p
JOIN thread AS t USING (upid)
JOIN thread_track AS tt USING (utid)
JOIN slice AS s ON s.track_id = tt.id
WHERE s.name GLOB 'Choreographer#doFrame*'
GROUP BY p.upid, p.pid, p.name, t.utid, t.tid, t.name
ORDER BY frame_count DESC
```

### c3. On that UI thread, TextLayout:initLayout grew from 288 occurrences totaling 69.199128 ms to 1,859,699 occurrences totaling 7,192.994139 ms.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, p.upid, t.tid, t.name AS thread_name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id=s.track_id
JOIN thread AS t ON t.utid=tt.utid
JOIN process AS p ON p.upid=t.upid
WHERE s.name='TextLayout:initLayout'
GROUP BY p.name,p.upid,t.tid,t.name
ORDER BY total_ms DESC
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, p.upid, t.tid, t.name AS thread_name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id=s.track_id
JOIN thread AS t ON t.utid=tt.utid
JOIN process AS p ON p.upid=t.upid
WHERE s.name='TextLayout:initLayout'
GROUP BY p.name,p.upid,t.tid,t.name
ORDER BY total_ms DESC
```

### c4. The allocation and collection signature also worsened in the app: garbage collection increased from 7 events totaling 258.575876 ms to 203 events totaling 13,632.500926 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, upid, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, min(gc_ts)/1e9 AS first_gc_s, max(gc_ts + gc_dur)/1e9 AS last_gc_s
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name, upid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, upid, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, min(gc_ts)/1e9 AS first_gc_s, max(gc_ts + gc_dur)/1e9 AS last_gc_s
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name, upid
```

### c5. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 changed FeedScreen.kt to replace a plain row title with RowTitle, which repeatedly measures text in fine-grained font-size steps, and added an infinite per-row breathing animation.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c6. The new text-layout activity and collection pressure make commit 18fab3f92d84e00498a5a6891125dd23bd063820 the likely correlated cause of the UI-time regression.

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, p.upid, t.tid, t.name AS thread_name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id=s.track_id
JOIN thread AS t ON t.utid=tt.utid
JOIN process AS p ON p.upid=t.upid
WHERE s.name='TextLayout:initLayout'
GROUP BY p.name,p.upid,t.tid,t.name
ORDER BY total_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT process_name, upid, count(*) AS gc_count, sum(gc_dur)/1e6 AS gc_ms, sum(reclaimed_mb) AS reclaimed_mb, min(gc_ts)/1e9 AS first_gc_s, max(gc_ts + gc_dur)/1e9 AS last_gc_s
FROM android_garbage_collection_events
WHERE process_name = 'com.superplayer.demo'
GROUP BY process_name, upid
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- Only one capture per side is available, so p95 and garbage-collection totals can include run-to-run noise.
- No stack-profile samples were available for direct symbolization; the culprit attribution is therefore correlated rather than direct.
- The captures use a non-debuggable benchmark build on an SDK 36 emulator.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 62 tool calls, $0.0302, 269 s.
Tokens: 33 input, 213,252 cache read, 43,784 cache write, 12,462 output.
