# No regression

- **Metric:** `frame_p95_ms` -9.2 ms (81.5 → 72.3 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The selected frame_p95_ms metric improved from 81.499417 ms in baseline to 72.295959 ms in current, a delta of -9.203458 ms.

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

### c2. The window-frame workload is attributed to com.superplayer.demo on its UI thread; the trace contains 676 app frame rows in baseline and 730 in current.

The `baseline` trace: 2 rows.

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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_count
FROM window_frames f
JOIN process p USING (upid)
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
```

The `current` trace: 2 rows.

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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_count
FROM window_frames f
JOIN process p USING (upid)
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
```

### c3. On that UI thread, ImageButton slices total 68.522465 ms across 648 slices in baseline and 18.858164 ms across 660 slices in current, consistent with less expensive UI work rather than a frame-time regression.

The `baseline` trace: 6 rows.

```sql
SELECT s.name, t.name AS thread_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND s.name IN ('ImageButton','compose:lazy:prefetch:compose','compose:lazy:prefetch:idle_frame','compose:lazy:prefetch:measure','input','AndroidOwner:onTouch')
GROUP BY s.name,t.name ORDER BY s.name,t.name
```

The `current` trace: 6 rows.

```sql
SELECT s.name, t.name AS thread_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND s.name IN ('ImageButton','compose:lazy:prefetch:compose','compose:lazy:prefetch:idle_frame','compose:lazy:prefetch:measure','input','AndroidOwner:onTouch')
GROUP BY s.name,t.name ORDER BY s.name,t.name
```

### c4. The range head includes a TV-controls behavior change in TvScreen.kt, titled “Hide the TV controls four seconds after the last press.” It is a correlation with the observed UI change, not a regression culprit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
82cde0d4acda1b40a0044ed8a118b168410d3aee
```

The `baseline` trace: 6 rows.

```sql
SELECT s.name, t.name AS thread_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND s.name IN ('ImageButton','compose:lazy:prefetch:compose','compose:lazy:prefetch:idle_frame','compose:lazy:prefetch:measure','input','AndroidOwner:onTouch')
GROUP BY s.name,t.name ORDER BY s.name,t.name
```

The `current` trace: 6 rows.

```sql
SELECT s.name, t.name AS thread_name, count(*) AS slices, sum(s.dur) / 1e6 AS total_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.superplayer.demo' AND s.name IN ('ImageButton','compose:lazy:prefetch:compose','compose:lazy:prefetch:idle_frame','compose:lazy:prefetch:measure','input','AndroidOwner:onTouch')
GROUP BY s.name,t.name ORDER BY s.name,t.name
```

## Caveats

- Only one capture was available per side, so run-to-run noise cannot be ruled out.
- The current run metadata identifies a non-debuggable benchmark build on an emulator; frame_p95_ms includes the display pipeline and SurfaceFlinger queueing, so source-level attribution remains indirect.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 61 tool calls, $0.0415, 232 s.
Tokens: 45 input, 435,535 cache read, 55,230 cache write, 15,793 output.
