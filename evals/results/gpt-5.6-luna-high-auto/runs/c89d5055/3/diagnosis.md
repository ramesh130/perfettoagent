# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. The selected UI-frame metric regressed from 37.952167 ms at baseline to 69.289541 ms currently, a 31.337374 ms increase.

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

### c2. The current trace has substantially more Compose layout and recomposition work: AndroidOwner:measureAndLayout totals 32699.269763 ms across 1759 slices and Compose:recompose totals 31391.888631 ms across 9267 slices, versus 1092.850761 ms across 796 slices and 670.121745 ms across 768 slices at baseline.

The `baseline` trace: 5 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('TextLayout:initLayout','TextStringSimpleNode::measure','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY name ORDER BY total_ms DESC
```

The `current` trace: 5 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('TextLayout:initLayout','TextStringSimpleNode::measure','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY name ORDER BY total_ms DESC
```

### c3. Text measurement is a major new component of the current workload: TextLayout:initLayout appears 1,859,699 times for 7192.994139 ms currently, compared with 288 times for 69.199128 ms at baseline.

The `baseline` trace: 5 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('TextLayout:initLayout','TextStringSimpleNode::measure','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY name ORDER BY total_ms DESC
```

The `current` trace: 5 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('TextLayout:initLayout','TextStringSimpleNode::measure','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY name ORDER BY total_ms DESC
```

### c4. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 changes FeedScreen.kt by adding the animated row padding and RowTitle's fine-grained rememberTextMeasurer.measure loop; the current trace's large increase in text measurement and Compose layout work directly matches that changed code.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

The `current` trace: 5 rows.

```sql
SELECT name, count(*) AS slices, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms FROM slice WHERE name IN ('TextLayout:initLayout','TextStringSimpleNode::measure','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY name ORDER BY total_ms DESC
```

### c5. Garbage-collection work also increased sharply: baseline had 4 full collections totaling 170.514875 ms and 3 young collections totaling 88.061001 ms, while current had 99 full collections totaling 7713.607132 ms and 104 young collections totaling 5918.893794 ms.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT process_name, gc_type, count(*) AS events, sum(gc_dur)/1e6 AS total_ms, avg(gc_dur)/1e6 AS avg_ms, sum(reclaimed_mb) AS reclaimed_mb FROM android_garbage_collection_events WHERE upid=(SELECT upid FROM app) GROUP BY process_name,gc_type ORDER BY total_ms DESC
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (
 SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT process_name, gc_type, count(*) AS events, sum(gc_dur)/1e6 AS total_ms, avg(gc_dur)/1e6 AS avg_ms, sum(reclaimed_mb) AS reclaimed_mb FROM android_garbage_collection_events WHERE upid=(SELECT upid FROM app) GROUP BY process_name,gc_type ORDER BY total_ms DESC
```

## Caveats

- This comparison uses one capture per side, so smaller changes could be run-to-run noise; the observed UI-time, text-layout, and GC changes are large.
- The captures were made on an emulator benchmark device, so absolute timings may not generalize to physical devices.

## Run

`gpt-5.6-luna` on openai, effort high: 44 tool calls, $0.0252, 257 s.
Tokens: 30 input, 183,023 cache read, 43,262 cache write, 8,942 output.
