# Regression

- **Metric:** `frame_ui_time_p95_ms` +2.65 ms (32.53 → 35.18 ms)
- **Culprit:** `7fd362610713` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 3 claims kept, 0 dropped; 5 of 5 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 32.53 | 35.18 | +2.65 |

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

### c1. The app UI-thread frame-time p95 increased from 32.532333 ms in the baseline to 35.181834 ms in the current trace, a delta of 2.649501 ms.

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

### c2. Within UI frames, binder transaction time increased from 12,577.631963 ms over 15,357 slices in the baseline to 14,163.774261 ms over 15,984 slices in the current trace; traversal and draw-VRI[MainActivity] also increased in total time.

The `baseline` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT c.name, count(*) AS n, sum(c.dur)/1e6 AS total_ms, max(c.dur)/1e6 AS max_ms
FROM android_frames_choreographer_do_frame d JOIN slice p ON p.id=d.id JOIN slice c ON c.ts>=p.ts AND c.ts+c.dur<=p.ts+p.dur AND c.id!=p.id
WHERE c.dur>0 GROUP BY c.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT c.name, count(*) AS n, sum(c.dur)/1e6 AS total_ms, max(c.dur)/1e6 AS max_ms
FROM android_frames_choreographer_do_frame d JOIN slice p ON p.id=d.id JOIN slice c ON c.ts>=p.ts AND c.ts+c.dur<=p.ts+p.dur AND c.id!=p.id
WHERE c.dur>0 GROUP BY c.name ORDER BY total_ms DESC LIMIT 30
```

### c3. The strongest range correlation is commit 7fd3626107135436b97973da12915e1e13f76255, which changed FeedScreen.kt's watched-row player acquisition from an if/else to takeIf/let; blame at the range head attributes the changed acquisition lines to that commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
7fd3626107135436b97973da12915e1e13f76255
```

## Caveats

- Only one capture per side is available, so the 2.649501 ms increase may include run-to-run variance; confidence is low.
- The current trace was captured on an Android emulator (sdk_gphone64_arm64, SDK 36), and the trace build was non-debuggable benchmark type.
- The trace evidence localizes the change to heavier UI-frame work and binder activity but does not directly prove that the FeedScreen commit caused those runtime differences.

## Run

`gpt-5.6-luna` on openai, effort low: 16 tool calls, $0.0075, 143 s.
Tokens: 24 input, 59,790 cache read, 11,025 cache write, 2,925 output.
