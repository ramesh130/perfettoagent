# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
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

### c1. The app UI-thread frame p95 increased from 37.952167 ms in baseline to 69.289541 ms in current, a delta of 31.337373999999997 ms.

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

### c2. The increased UI time is concentrated in Compose traversal: traversal rose from 5184.638413 ms across 605 slices in baseline to 20505.45679 ms across 851 slices in current.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT c.name, count(*) AS occurrences, sum(c.dur)/1e6 AS total_ms, max(c.dur)/1e6 AS max_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS p USING (id)
JOIN slice AS c ON c.parent_id = p.id
WHERE c.name IN ('traversal','animation')
GROUP BY c.name ORDER BY c.name
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT c.name, count(*) AS occurrences, sum(c.dur)/1e6 AS total_ms, max(c.dur)/1e6 AS max_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS p USING (id)
JOIN slice AS c ON c.parent_id = p.id
WHERE c.name IN ('traversal','animation')
GROUP BY c.name ORDER BY c.name
```

### c3. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 changed FeedScreen.kt to add an always-running row-breath animation and RowTitle text measurement; blame at the range head attributes those lines to this commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- This conclusion is based on one capture per side, so run-to-run variability cannot be excluded completely.
- The trace identifies the affected Compose traversal and the commit changes the corresponding FeedScreen composables, but it does not provide a direct source-level stack attribution; the culprit attribution is therefore correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort low: 12 tool calls, $0.0074, 66 s.
Tokens: 18 input, 37,608 cache read, 13,606 cache write, 2,676 output.
