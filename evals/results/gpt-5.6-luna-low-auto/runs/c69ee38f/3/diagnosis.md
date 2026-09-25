# No regression

- **Metric:** `frame_p95_ms` -4.6 ms (128.09 → 123.49 ms)
- **Culprit:** none attributed
- **Verified:** 2 claims kept, 0 dropped; 6 of 6 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 128.09 | 123.49 | -4.6 |

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

### c1. The app's frame-duration p95 decreased from 128.089417 ms in the baseline trace to 123.491875 ms in the current trace, a delta of -4.597542 ms; this is an improvement rather than a regression.

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

### c2. The commits in the supplied range are primarily renames, UI layout changes, logging changes, and build configuration changes; the evidence does not identify a commit responsible for a performance regression.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
d06e018fc738bebf0f5ccf2814efba445a6cfdfe
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
53c9f8712216924f1fe829a44e7db1f13caeb3c3
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
c48c1214737c4fc1f3983993d9812f958485b4d1
```

Commit, changing `gradle.properties`:

```text
a93860315b13a677a0835b60f6bba36ac2fa40f9
```

## Caveats

- Each side has only one capture, so the modest improvement may be affected by run-to-run noise.
- The current trace was recorded on an Android emulator (sdk_gphone64_arm64, SDK 36); emulator results may not represent physical-device performance.

## Run

`gpt-5.6-luna` on openai, effort low: 8 tool calls, $0.0028, 74 s.
Tokens: 9 input, 12,611 cache read, 2,791 cache write, 1,530 output.
