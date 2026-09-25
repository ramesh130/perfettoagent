# Regression

- **Metric:** `frame_p95_ms` +11.24 ms (81.5 → 92.74 ms)
- **Culprit:** `18fab3f92d84` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 81.5 | 92.74 | +11.24 |

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

### c1. The UI frame p95 increased from 81.499417 ms in the baseline to 92.735583 ms in the current trace, a 11.236166 ms regression.

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

### c2. The regression is localized to the app UI thread: current execution shows 1,859,699 TextLayout:initLayout slices totaling 7,192.994 ms, versus 288 slices totaling 69.199 ms in baseline; AndroidOwner:measureAndLayout also increased from 1,092.851 ms to 32,699.27 ms.

The `baseline` trace: 4 rows.

```sql
WITH app AS (SELECT utid FROM thread WHERE name LIKE '%uperplayer%' ORDER BY utid LIMIT 1)
SELECT s.name,count(*) AS occurrences,round(sum(s.dur)/1e6,3) AS total_ms,round(max(s.dur)/1e6,3) AS max_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN app ON tt.utid=app.utid
WHERE s.name IN ('TextLayout:initLayout','animation','Recomposer:recompose','AndroidOwner:measureAndLayout') AND s.dur>0
GROUP BY s.name ORDER BY s.name
```

The `current` trace: 4 rows.

```sql
WITH app AS (SELECT utid FROM thread WHERE name LIKE '%uperplayer%' ORDER BY utid LIMIT 1)
SELECT s.name,count(*) AS occurrences,round(sum(s.dur)/1e6,3) AS total_ms,round(max(s.dur)/1e6,3) AS max_ms
FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN app ON tt.utid=app.utid
WHERE s.name IN ('TextLayout:initLayout','animation','Recomposer:recompose','AndroidOwner:measureAndLayout') AND s.dur>0
GROUP BY s.name ORDER BY s.name
```

### c3. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 added FeedScreen row breathing animation and RowTitle text measurement, matching the new animation, layout, and text-layout work in the current trace.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c4. The changed FeedScreen lines were introduced by commit 18fab3f92d84e00498a5a6891125dd23bd063820, including rememberInfiniteTransition, RowTitle, and repeated text measurement.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- This diagnosis compares one capture per side, so smaller changes could be affected by run-to-run noise.
- The traces were captured on an Android emulator; the current build was a non-debuggable benchmark build.

## Run

`gpt-5.6-luna` on openai, effort medium: 21 tool calls, $0.0129, 102 s.
Tokens: 27 input, 94,185 cache read, 17,377 cache write, 5,596 output.
