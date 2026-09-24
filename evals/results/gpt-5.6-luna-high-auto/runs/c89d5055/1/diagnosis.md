# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 1 dropped; 7 of 8 citations passed
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

### c2. The change is localized to com.superplayer.demo's UI thread: TextLayout:initLayout grew from 288 occurrences, or 0.426036 per frame, to 1,859,699 occurrences, or 1,133.962805 per frame; its total duration grew from 69.199128 ms to 7,192.994139 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), frames AS (SELECT count(*) AS n FROM window_frames WHERE upid=(SELECT upid FROM app)), text_layout AS (
  SELECT count(*) AS n, sum(s.dur)/1e6 AS total_ms
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  WHERE t.utid IN (SELECT utid FROM ui) AND s.name='TextLayout:initLayout'
)
SELECT frames.n AS frame_count, text_layout.n AS text_layout_count, text_layout.total_ms, 1.0*text_layout.n/frames.n AS text_layout_per_frame
FROM frames CROSS JOIN text_layout
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), frames AS (SELECT count(*) AS n FROM window_frames WHERE upid=(SELECT upid FROM app)), text_layout AS (
  SELECT count(*) AS n, sum(s.dur)/1e6 AS total_ms
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  WHERE t.utid IN (SELECT utid FROM ui) AND s.name='TextLayout:initLayout'
)
SELECT frames.n AS frame_count, text_layout.n AS text_layout_count, text_layout.total_ms, 1.0*text_layout.n/frames.n AS text_layout_per_frame
FROM frames CROSS JOIN text_layout
```

### c3. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 changed FeedScreen.kt to replace the ordinary row title with RowTitle, create a remembered text measurer, and repeatedly call measurer.measure while searching font sizes in 0.05sp steps. This directly accounts for the large increase in TextLayout:initLayout work on the UI thread.

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app))
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid IN (SELECT utid FROM ui) AND s.name IN ('TextLayout:initLayout','Constructing StaticLayout','Compose:recompose','AndroidOwner:measureAndLayout')
GROUP BY s.name ORDER BY s.name
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c4. The frame counts differ between captures—676 baseline frames versus 1,640 current frames—so the localization comparison uses per-frame rates; the UI-time percentile itself is already a per-frame metric.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), frames AS (SELECT count(*) AS n FROM window_frames WHERE upid=(SELECT upid FROM app)), text_layout AS (
  SELECT count(*) AS n, sum(s.dur)/1e6 AS total_ms
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  WHERE t.utid IN (SELECT utid FROM ui) AND s.name='TextLayout:initLayout'
)
SELECT frames.n AS frame_count, text_layout.n AS text_layout_count, text_layout.total_ms, 1.0*text_layout.n/frames.n AS text_layout_per_frame
FROM frames CROSS JOIN text_layout
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
), ui AS (
  SELECT DISTINCT ui_thread_utid AS utid FROM window_frames WHERE upid=(SELECT upid FROM app)
), frames AS (SELECT count(*) AS n FROM window_frames WHERE upid=(SELECT upid FROM app)), text_layout AS (
  SELECT count(*) AS n, sum(s.dur)/1e6 AS total_ms
  FROM slice s JOIN thread_track t ON t.id=s.track_id
  WHERE t.utid IN (SELECT utid FROM ui) AND s.name='TextLayout:initLayout'
)
SELECT frames.n AS frame_count, text_layout.n AS text_layout_count, text_layout.total_ms, 1.0*text_layout.n/frames.n AS text_layout_per_frame
FROM frames CROSS JOIN text_layout
```

## Caveats

- This is one capture per side, so run-to-run noise cannot be ruled out; however, the large per-frame increase in text-layout work and the matching code change make 18fab3f92d84e00498a5a6891125dd23bd063820 the direct attribution.

## Dropped claims

### c1. The app UI-time p95 increased from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a 31.337374 ms regression.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
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

`gpt-5.6-luna` on openai, effort high: 46 tool calls, $0.0240, 275 s.
Tokens: 36 input, 206,402 cache read, 28,762 cache write, 10,599 output.
