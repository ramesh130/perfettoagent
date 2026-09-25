# Inconclusive

- **Metric:** `binder_wait_ms` +60.5 ms (287.82 → 348.32 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `binder_wait_ms` | ms | 287.82 | 348.32 | +60.5 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.binder;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
```

## Claims

### c1. Synchronous binder wait on the app's UI thread increased from 287.81833 ms in the baseline trace to 348.319381 ms in the current trace, a delta of 60.501051 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.binder;
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
  )
SELECT
  CASE
    WHEN NOT EXISTS (SELECT 1 FROM frames)
      OR NOT EXISTS (SELECT 1 FROM android_binder_txns) THEN NULL
    ELSE coalesce((
      SELECT sum(client_dur) FROM android_binder_txns
      WHERE is_sync AND client_dur > 0
        AND client_utid IN (SELECT ui_thread_utid FROM frames)
    ), 0) / 1e6
  END AS value
```

### c2. The UI-frame metrics did not worsen: UI-time p95 fell from 39.433416 ms to 36.989875 ms.

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

### c3. The range contains UI changes such as the four-second TV-control timeout, increased download-row padding, and a FeedRow player-acquisition rewrite, but the trace evidence does not directly connect any of them to the additional binder wait.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/TvScreen.kt`:

```text
9d81a4cba849ddb0e129cd5ffe38d8cf06030d3f
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
d0741e3efa2bd7173eba2b7cc863467317f707aa
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
328304f8f1081e484f20030bb6518b1b1ee03c82
```

## Caveats

- Each side has only one capture, so the 60.501051 ms binder delta may include run-to-run variance.
- The current run is a non-debuggable benchmark build on an Android SDK 36 emulator.
- Startup TTID/TTFD could not be measured because both traces lacked the required startup data.

## Run

`gpt-5.6-luna` on openai, effort low: 24 tool calls, $0.0087, 85 s.
Tokens: 27 input, 74,882 cache read, 9,275 cache write, 4,053 output.
