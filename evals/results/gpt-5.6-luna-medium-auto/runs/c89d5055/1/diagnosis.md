# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 1 dropped; 5 of 7 citations passed
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

### c2. The regression is concentrated on the app UI thread: current-trace traversal averaged 27.762552 ms per slice versus 9.682226 ms in baseline, while AndroidOwner:measureAndLayout averaged 18.589692 ms versus 1.372928 ms.

The `baseline` trace: 7 rows.

```sql
SELECT t.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid
WHERE t.name LIKE '%uperplayer.demo' AND s.name IN ('traversal','draw-VRI[MainActivity]','AndroidOwner:measureAndLayout','Compose:recompose','Record View#draw()','postAndWait','TextLayout:initLayout')
GROUP BY t.name,s.name ORDER BY total_ms DESC
```

The `current` trace: 7 rows.

```sql
SELECT t.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid
WHERE t.name LIKE '%uperplayer.demo' AND s.name IN ('traversal','draw-VRI[MainActivity]','AndroidOwner:measureAndLayout','Compose:recompose','Record View#draw()','postAndWait','TextLayout:initLayout')
GROUP BY t.name,s.name ORDER BY total_ms DESC
```

### c3. The current trace contains 1,859,699 TextLayout:initLayout slices totaling 7,192.994139 ms, compared with 288 slices totaling 69.199128 ms in the baseline.

The `baseline` trace: 7 rows.

```sql
SELECT t.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid
WHERE t.name LIKE '%uperplayer.demo' AND s.name IN ('traversal','draw-VRI[MainActivity]','AndroidOwner:measureAndLayout','Compose:recompose','Record View#draw()','postAndWait','TextLayout:initLayout')
GROUP BY t.name,s.name ORDER BY total_ms DESC
```

The `current` trace: 7 rows.

```sql
SELECT t.name AS thread_name, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, avg(s.dur)/1e6 AS avg_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid
WHERE t.name LIKE '%uperplayer.demo' AND s.name IN ('traversal','draw-VRI[MainActivity]','AndroidOwner:measureAndLayout','Compose:recompose','Record View#draw()','postAndWait','TextLayout:initLayout')
GROUP BY t.name,s.name ORDER BY total_ms DESC
```

### c4. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 added an infinite per-row animation and a RowTitle composable that repeatedly measures text in fine-grained font-size steps, matching the increased Compose layout and text-layout activity.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- This diagnosis uses one baseline capture and one current capture; run-to-run variability cannot be measured.
- Both captures were made on an emulator (sdk_gphone64_arm64, SDK 36).
- Startup TTID/TTFD and heap-graph metrics had no data in these traces.

## Dropped claims

### c1. The app's UI-frame p95 increased from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a delta of 31.337373999999997 ms.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 23 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such column: s.dur; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 23 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such column: s.dur

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 26 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT upid FROM window_frames GROUP BY count(*) ORDER BY count(*) DESC, upid LIMIT 1
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

## Run

`gpt-5.6-luna` on openai, effort medium: 27 tool calls, $0.0130, 196 s.
Tokens: 18 input, 50,632 cache read, 26,484 cache write, 4,474 output.
