# Inconclusive

- **Metric:** `frame_ui_time_p95_ms` +0.34 ms (26.21 → 26.55 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 12 of 12 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.21 | 26.55 | +0.34 |

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

### c1. The app UI frame p95 increased from 26.206625 ms in the baseline to 26.550666 ms in the current trace, a 0.344041 ms delta.

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

### c2. The frame-producing process is com.example.jetnews on the example.jetnews UI thread in both traces; it supplied 2120 baseline frames and 2107 current frames.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, p.name AS process_name, f.ui_thread_utid, t.name AS ui_thread_name, count(*) AS frame_count
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, p.name, f.ui_thread_utid, t.name
ORDER BY frame_count DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT f.upid, p.name AS process_name, f.ui_thread_utid, t.name AS ui_thread_name, count(*) AS frame_count
FROM android_frames_layers AS f
JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
JOIN process AS p USING (upid)
JOIN thread AS t ON t.utid = f.ui_thread_utid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
GROUP BY f.upid, p.name, f.ui_thread_utid, t.name
ORDER BY frame_count DESC
```

### c3. Image-related work is mixed rather than a uniform slowdown: ImageDecoder_nDecodeBitmap decreased from 27 calls totaling 37.729918 ms to 24 calls totaling 24.689539 ms, while Bitmap#prepareToDraw 63x63 remained at 210 calls and rose from 23.20842 ms to 26.952114 ms.

The `baseline` trace: 3 rows.

```sql
SELECT s.name, count(*) AS count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND (s.name = 'ImageDecoder_nDecodeBitmap' OR s.name = 'Bitmap#prepareToDraw 63x63' OR s.name = 'Atlas full')
GROUP BY s.name ORDER BY s.name
```

The `current` trace: 3 rows.

```sql
SELECT s.name, count(*) AS count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND (s.name = 'ImageDecoder_nDecodeBitmap' OR s.name = 'Bitmap#prepareToDraw 63x63' OR s.name = 'Atlas full')
GROUP BY s.name ORDER BY s.name
```

### c4. The only range commit tied to this localized UI image path changes the Interests TopicItem thumbnail from 56.dp to 48.dp and adjusts the divider inset from 72.dp to 64.dp.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

### c5. Given the small p95 shift in a single capture per side and the mixed image-work results, the traces do not establish a performance regression or attribute one to a commit in the range.

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

The `baseline` trace: 3 rows.

```sql
SELECT s.name, count(*) AS count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND (s.name = 'ImageDecoder_nDecodeBitmap' OR s.name = 'Bitmap#prepareToDraw 63x63' OR s.name = 'Atlas full')
GROUP BY s.name ORDER BY s.name
```

The `current` trace: 3 rows.

```sql
SELECT s.name, count(*) AS count, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE p.name = 'com.example.jetnews' AND (s.name = 'ImageDecoder_nDecodeBitmap' OR s.name = 'Bitmap#prepareToDraw 63x63' OR s.name = 'Atlas full')
GROUP BY s.name ORDER BY s.name
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so the 0.344041 ms p95 difference may be run-to-run noise.
- The current run is a debuggable debug build on an sdk_gphone64_arm64 emulator; baseline build metadata was not recorded.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 60 tool calls, $0.0366, 202 s.
Tokens: 42 input, 270,546 cache read, 42,480 cache write, 17,093 output.
