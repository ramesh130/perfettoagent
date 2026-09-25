# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The requested UI-time p95 regressed from 37.952167 ms in baseline to 69.289541 ms in current, a delta of 31.337373999999997 ms.

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

### c2. The affected work is the app UI thread of com.superplayer.demo: the baseline has 873 doFrame slices on thread uperplayer.demo, while current has 1644.

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
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  doframes AS (
    SELECT s.id, s.ts, s.dur, d.ui_thread_utid
    FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT p.name AS process_name, t.name AS thread_name, t.utid,
       count(*) AS doframe_count, max(dur)/1e6 AS max_ms,
       (SELECT dur/1e6 FROM (SELECT dur, row_number() OVER (ORDER BY dur) AS r, count(*) OVER () AS n FROM doframes) WHERE r=(n*95+99)/100) AS p95_ms
FROM doframes JOIN thread t ON t.utid=doframes.ui_thread_utid JOIN process p ON p.upid=t.upid
GROUP BY p.name, t.name, t.utid
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
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  doframes AS (
    SELECT s.id, s.ts, s.dur, d.ui_thread_utid
    FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT p.name AS process_name, t.name AS thread_name, t.utid,
       count(*) AS doframe_count, max(dur)/1e6 AS max_ms,
       (SELECT dur/1e6 FROM (SELECT dur, row_number() OVER (ORDER BY dur) AS r, count(*) OVER () AS n FROM doframes) WHERE r=(n*95+99)/100) AS p95_ms
FROM doframes JOIN thread t ON t.utid=doframes.ui_thread_utid JOIN process p ON p.upid=t.upid
GROUP BY p.name, t.name, t.utid
```

### c3. Compose work inside the UI frames increased substantially: AndroidOwner:measureAndLayout totals 1051.919013 ms in baseline versus 31466.314722 ms in current, and Compose:recompose totals 261.103158 ms versus 29899.462092 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1),
frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
doframes AS (SELECT s.id,s.ts,s.dur FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames))
SELECT count(DISTINCT d.id) AS doframes,
       sum(CASE WHEN s.name='AndroidOwner:measureAndLayout' THEN s.dur ELSE 0 END)/1e6 AS measure_layout_ms,
       sum(CASE WHEN s.name='Compose:recompose' THEN s.dur ELSE 0 END)/1e6 AS recompose_ms,
       sum(CASE WHEN s.name='TextStringSimpleNode::measure' THEN s.dur ELSE 0 END)/1e6 AS text_measure_ms
FROM doframes d JOIN slice s ON s.ts>=d.ts AND s.ts+s.dur<=d.ts+d.dur
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1),
frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
doframes AS (SELECT s.id,s.ts,s.dur FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames))
SELECT count(DISTINCT d.id) AS doframes,
       sum(CASE WHEN s.name='AndroidOwner:measureAndLayout' THEN s.dur ELSE 0 END)/1e6 AS measure_layout_ms,
       sum(CASE WHEN s.name='Compose:recompose' THEN s.dur ELSE 0 END)/1e6 AS recompose_ms,
       sum(CASE WHEN s.name='TextStringSimpleNode::measure' THEN s.dur ELSE 0 END)/1e6 AS text_measure_ms
FROM doframes d JOIN slice s ON s.ts>=d.ts AND s.ts+s.dur<=d.ts+d.dur
```

### c4. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 is the strongest range candidate: it changes FeedScreen.kt, where the added per-row infinite animation and RowTitle text-measurement logic provide a plausible source for the increased Compose animation, recomposition, and layout work.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1),
frames AS (SELECT * FROM window_frames WHERE upid=(SELECT upid FROM app)),
doframes AS (SELECT s.id,s.ts,s.dur FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames))
SELECT count(DISTINCT d.id) AS doframes,
       sum(CASE WHEN s.name='AndroidOwner:measureAndLayout' THEN s.dur ELSE 0 END)/1e6 AS measure_layout_ms,
       sum(CASE WHEN s.name='Compose:recompose' THEN s.dur ELSE 0 END)/1e6 AS recompose_ms,
       sum(CASE WHEN s.name='TextStringSimpleNode::measure' THEN s.dur ELSE 0 END)/1e6 AS text_measure_ms
FROM doframes d JOIN slice s ON s.ts>=d.ts AND s.ts+s.dur<=d.ts+d.dur
```

## Caveats

- This is one capture per side, so run-to-run noise cannot be estimated independently.
- The current run metadata identifies an sdk_gphone64_arm64 emulator and a benchmark build; the result is strong but should ideally be confirmed with repeated captures.

## Run

`gpt-5.6-luna` on openai, effort high: 28 tool calls, $0.0240, 281 s.
Tokens: 36 input, 207,456 cache read, 29,080 cache write, 10,479 output.
