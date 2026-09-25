# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.21 | 54.17 | +27.96 |

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

### c1. The requested UI-thread frame p95 increased from 26.206625 ms in the baseline to 54.169584 ms in the current trace, a 27.962959 ms increase.

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

### c2. The slowdown affects nearly the entire current capture: 1,378 of 1,379 UI frames exceeded 40 ms, compared with 1 of 2,286 baseline frames.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ranked AS (
  SELECT s.dur/1e6 AS ui_ms, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
  FROM android_frames_choreographer_do_frame d JOIN slice s USING(id)
  WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app))
)
SELECT count(*) AS total_frames, sum(CASE WHEN ui_ms > 16.667 THEN 1 ELSE 0 END) AS over_16_7ms, sum(CASE WHEN ui_ms > 40 THEN 1 ELSE 0 END) AS over_40ms, max(ui_ms) AS max_ms, (SELECT ui_ms FROM ranked WHERE rank=(n*95+99)/100) AS p95_ms
FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1), ranked AS (
  SELECT s.dur/1e6 AS ui_ms, row_number() OVER (ORDER BY s.dur) AS rank, count(*) OVER () AS n
  FROM android_frames_choreographer_do_frame d JOIN slice s USING(id)
  WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app))
)
SELECT count(*) AS total_frames, sum(CASE WHEN ui_ms > 16.667 THEN 1 ELSE 0 END) AS over_16_7ms, sum(CASE WHEN ui_ms > 40 THEN 1 ELSE 0 END) AS over_40ms, max(ui_ms) AS max_ms, (SELECT ui_ms FROM ranked WHERE rank=(n*95+99)/100) AS p95_ms
FROM ranked
```

### c3. The extra UI time is localized to Compose view drawing. In the longest current doFrame, AndroidOwner:draw took 92.985 ms inside a 93.675 ms frame; in the longest baseline doFrame, AndroidOwner:draw took only 0.107209 ms.

The `current` trace: 12 rows.

```sql
WITH RECURSIVE descendants AS (
  SELECT id, parent_id, name, dur, 0 AS depth FROM slice WHERE id = 205640
  UNION ALL
  SELECT s.id, s.parent_id, s.name, s.dur, d.depth + 1
  FROM slice s JOIN descendants d ON s.parent_id = d.id
)
SELECT depth, name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms
FROM descendants
GROUP BY depth, name
ORDER BY depth, total_ms DESC
LIMIT 100
```

The `baseline` trace: 15 rows.

```sql
WITH RECURSIVE descendants AS (
  SELECT id, parent_id, name, dur, 0 AS depth FROM slice WHERE id = 7717
  UNION ALL
  SELECT s.id, s.parent_id, s.name, s.dur, d.depth + 1
  FROM slice s JOIN descendants d ON s.parent_id = d.id
)
SELECT depth, name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms
FROM descendants
GROUP BY depth, name
ORDER BY depth, total_ms DESC
LIMIT 100
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 adds a per-frame drawWithContent overlay to PostCardSimple, continuously invalidated with withFrameNanos and constructing 6,000 random grain values. That change is consistent with the current trace's draw-bound slowdown and is likely the regression cause.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

The `current` trace: 12 rows.

```sql
WITH RECURSIVE descendants AS (
  SELECT id, parent_id, name, dur, 0 AS depth FROM slice WHERE id = 205640
  UNION ALL
  SELECT s.id, s.parent_id, s.name, s.dur, d.depth + 1
  FROM slice s JOIN descendants d ON s.parent_id = d.id
)
SELECT depth, name, count(*) AS occurrences, sum(dur)/1e6 AS total_ms, max(dur)/1e6 AS max_ms
FROM descendants
GROUP BY depth, name
ORDER BY depth, total_ms DESC
LIMIT 100
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side has a single capture, so normal run-to-run variability is not quantified.
- The trace localizes the cost to Compose drawing but does not name PostCardSimple or provide a method-level stack attribution; the culprit is therefore correlated rather than direct.
- The captures use a debuggable emulator build, which may not represent release-build performance.

## Run

`gpt-5.6-luna` on openai, effort high: 24 tool calls, $0.0183, 95 s.
Tokens: 24 input, 78,974 cache read, 21,820 cache write, 9,374 output.
