# Regression

- **Metric:** `frame_ui_time_p95_ms` +22.31 ms (37.95 → 60.26 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 37.95 | 60.26 | +22.31 |

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

### c1. The app UI-frame p95 increased from 37.952167 ms to 60.2595 ms, a 22.307333 ms increase.

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

### c2. The current trace has substantially more expensive UI drawing activity: its aggregate draw-VRI[MainActivity] time is 8037.182882 ms versus 6489.080457 ms in the baseline.

The `current` trace: 40 rows.

```sql
SELECT s.name, count(*) AS n, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s WHERE s.dur > 1000000 GROUP BY s.name ORDER BY total_ms DESC LIMIT 40
```

The `baseline` trace: 40 rows.

```sql
SELECT s.name, count(*) AS n, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s WHERE s.dur > 1000000 GROUP BY s.name ORDER BY total_ms DESC LIMIT 40
```

### c3. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 added per-frame feed grain generation using a list of 1,000,000 random values while scrolling, making it the strongest correlated explanation for increased UI work.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c4. The changed grain code is attributed by blame to commit 60be8b69bd6967b234ecb466b5cd1312df2c9854, including the per-frame update and drawWithContent implementation.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

## Caveats

- This conclusion is based on one baseline capture and one current capture, so run-to-run noise cannot be ruled out.
- The current build metadata identifies an emulator (sdk_gphone64_arm64, SDK 36), and the build is non-debuggable benchmark type.
- The trace does not expose a uniquely named grain slice, so the culprit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort low: 19 tool calls, $0.0087, 64 s.
Tokens: 18 input, 38,981 cache read, 16,840 cache write, 3,056 output.
