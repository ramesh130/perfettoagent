# Regression

- **Metric:** `frame_ui_time_p95_ms` +31.34 ms (37.95 → 69.29 ms)
- **Culprit:** `18fab3f92d84` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. The app UI frame-time p95 increased from 37.952167 ms in the baseline to 69.289541 ms in the current trace, a 31.337373999999997 ms increase.

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

### c2. The change is localized to the app's main thread: baseline traversal contained 713 occurrences totaling 6903.427833 ms, while current traversal contained 1643 occurrences totaling 45613.873327 ms. The corresponding draw-VRI[MainActivity] work also rose from 713 occurrences and 6583.587289 ms to 1643 occurrences and 44880.388054 ms.

The `baseline` trace: 10 rows.

```sql
SELECT s.name, t.utid, th.tid, th.name AS thread_name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms, avg(s.dur) / 1e6 AS avg_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
JOIN thread AS th ON th.utid = t.utid
WHERE s.name IN ('traversal', 'draw-VRI[MainActivity]', 'animation', 'measure', 'layout')
GROUP BY s.name, t.utid, th.tid, th.name
ORDER BY total_ms DESC
```

The `current` trace: 9 rows.

```sql
SELECT s.name, t.utid, th.tid, th.name AS thread_name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms, avg(s.dur) / 1e6 AS avg_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
JOIN thread AS th ON th.utid = t.utid
WHERE s.name IN ('traversal', 'draw-VRI[MainActivity]', 'animation', 'measure', 'layout')
GROUP BY s.name, t.utid, th.tid, th.name
ORDER BY total_ms DESC
```

### c3. Commit 18fab3f92d84e00498a5a6891125dd23bd063820 changed FeedScreen.kt by adding a per-row infinite breathing animation and the RowTitle composable, which repeatedly measures text while composing feed rows.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

### c4. The trace's increased Compose traversal on the app UI thread is consistent with the FeedScreen changes in commit 18fab3f92d84e00498a5a6891125dd23bd063820, making it the strongest correlated culprit in the supplied range.

The `current` trace: 9 rows.

```sql
SELECT s.name, t.utid, th.tid, th.name AS thread_name, count(*) AS occurrences, sum(s.dur) / 1e6 AS total_ms, max(s.dur) / 1e6 AS max_ms, avg(s.dur) / 1e6 AS avg_ms
FROM slice AS s
JOIN thread_track AS t ON t.id = s.track_id
JOIN thread AS th ON th.utid = t.utid
WHERE s.name IN ('traversal', 'draw-VRI[MainActivity]', 'animation', 'measure', 'layout')
GROUP BY s.name, t.utid, th.tid, th.name
ORDER BY total_ms DESC
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
18fab3f92d84e00498a5a6891125dd23bd063820
```

## Caveats

- This conclusion is based on one capture per side, so smaller effects could be run-to-run noise; the observed p95 increase is large but still lacks repeated runs for statistical confirmation.
- The current run metadata identifies an emulator benchmark build, so absolute timings may not represent physical-device performance.

## Run

`gpt-5.6-luna` on openai, effort high: 34 tool calls, $0.0182, 122 s.
Tokens: 33 input, 148,330 cache read, 25,012 cache write, 7,478 output.
