# No regression

- **Metric:** `frame_p95_ms` -9.2 ms (81.5 → 72.3 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 11 of 11 citations passed
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

### c1. The selected frame p95 metric improved: baseline was 81.499417 ms and current was 72.295959 ms.

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
  ),
  ui_ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT
  count(*) AS frame_count,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS frame_p95_ms,
  (SELECT ns / 1e6 FROM ui_ranked WHERE rank = (n * 95 + 99) / 100) AS frame_ui_time_p95_ms,
  100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS jank_pct
FROM frames
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
  ),
  ui_ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT
  count(*) AS frame_count,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS frame_p95_ms,
  (SELECT ns / 1e6 FROM ui_ranked WHERE rank = (n * 95 + 99) / 100) AS frame_ui_time_p95_ms,
  100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS jank_pct
FROM frames
```

### c2. The improvement is localized to the same app process and UI thread in both captures; the frame sample counts were 676 baseline and 730 current.

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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_rows
FROM window_frames f
JOIN app ON app.upid = f.upid
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
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
SELECT p.upid, p.name AS process_name, t.utid, t.name AS thread_name, count(*) AS frame_rows
FROM window_frames f
JOIN app ON app.upid = f.upid
JOIN process p ON p.upid = f.upid
JOIN thread t ON t.utid = f.ui_thread_utid
GROUP BY p.upid, p.name, t.utid, t.name
```

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
  ),
  ui_ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT
  count(*) AS frame_count,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS frame_p95_ms,
  (SELECT ns / 1e6 FROM ui_ranked WHERE rank = (n * 95 + 99) / 100) AS frame_ui_time_p95_ms,
  100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS jank_pct
FROM frames
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
  ),
  ui_ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT
  count(*) AS frame_count,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS frame_p95_ms,
  (SELECT ns / 1e6 FROM ui_ranked WHERE rank = (n * 95 + 99) / 100) AS frame_ui_time_p95_ms,
  100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS jank_pct
FROM frames
```

### c3. The corroborating UI metrics also improved: UI-thread p95 fell from 37.952167 ms to 36.63375 ms, and app-deadline jank fell from 54.7337278106509% to 42.1917808219178%.

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
  ),
  ui_ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT
  count(*) AS frame_count,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS frame_p95_ms,
  (SELECT ns / 1e6 FROM ui_ranked WHERE rank = (n * 95 + 99) / 100) AS frame_ui_time_p95_ms,
  100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS jank_pct
FROM frames
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
  ),
  ui_ranked AS (
    SELECT s.dur AS ns, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT
  count(*) AS frame_count,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS frame_p95_ms,
  (SELECT ns / 1e6 FROM ui_ranked WHERE rank = (n * 95 + 99) / 100) AS frame_ui_time_p95_ms,
  100.0 * sum(jank_type GLOB '*App Deadline Missed*') / count(*) AS jank_pct
FROM frames
```

### c4. The range does not yield a directly attributable frame-performance culprit. The runtime-affecting candidates identified at the range head are the MoQ logging interval change, the Downloads row-padding change, and the TV-controls timeout change; none is directly identified by the frame rows.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
6ef4e8aa95bcd45752e1fd3e907d8febdc5cb921
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
2cd54b6fd57035346e6095e8daf08afce3a1c475
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
82cde0d4acda1b40a0044ed8a118b168410d3aee
```

## Caveats

- This is one capture per side, so percentile and jank differences can include run-to-run noise.
- The current capture metadata identifies an sdk_gphone64_arm64 Android 36 emulator and a non-debuggable benchmark build.
- No culprit is assigned because the observed change is an improvement rather than a range-explained regression.

## Run

`gpt-5.6-luna` on openai, effort high: 48 tool calls, $0.0276, 221 s.
Tokens: 30 input, 144,007 cache read, 32,740 cache write, 13,784 output.
