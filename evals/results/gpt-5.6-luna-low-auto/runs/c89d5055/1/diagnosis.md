# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. The app's UI-frame p95 increased from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a delta of 31.337373999999997 ms.

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

### c2. The regression is concentrated in Compose work on the app's UI thread: current-trace Compose:recompose slices reach 95.158208 ms, versus 35.868 ms in the baseline.

The `current` trace: 20 rows.

```sql
SELECT thread.name AS thread_name, s.name, s.dur/1e6 AS dur_ms, s.ts/1e6 AS ts_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread USING(utid) WHERE s.name IN ('Choreographer#doFrame','Compose:recompose') ORDER BY s.dur DESC LIMIT 20
```

The `baseline` trace: 20 rows.

```sql
SELECT thread.name AS thread_name, s.name, s.dur/1e6 AS dur_ms, s.ts/1e6 AS ts_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread USING(utid) WHERE s.name IN ('Choreographer#doFrame','Compose:recompose') ORDER BY s.dur DESC LIMIT 20
```

### c3. The current trace records substantially more UI-thread TextLayout:initLayout work: 1,859,699 slices totaling 7,192.994139 ms, compared with 288 TextStringSimpleNode::measure slices totaling 217.619298 ms in the baseline.

The `current` trace: 20 rows.

```sql
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread USING(utid) WHERE thread.name='uperplayer.demo' GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

The `baseline` trace: 20 rows.

```sql
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread USING(utid) WHERE thread.name='uperplayer.demo' GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

### c4. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 added RowTitle text measurement with a fine-grained size loop and an always-running row-breath animation in FeedScreen.kt, matching the observed Compose and text-layout increase.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- Each side is a single capture, so run-to-run noise cannot be excluded completely.
- The captures were made on an Android SDK 36 emulator; the current build was a non-debuggable benchmark build.

## Run

`gpt-5.6-luna` on openai, effort low: 14 tool calls, $0.0076, 75 s.
Tokens: 15 input, 28,075 cache read, 15,716 cache write, 2,598 output.
