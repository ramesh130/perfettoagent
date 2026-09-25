# No regression

- **Metric:** `frame_p95_ms` -1.41 ms (74.52 → 73.11 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p95_ms` | ms | 74.52 | 73.11 | -1.41 |

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

### c1. The selected UI-frame p95 improved from 74.524125 ms in baseline to 73.112917 ms in current, a delta of -1.411208 ms; this is not a regression.

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

### c2. The selected app's main Compose work also did not increase: total Compose:recompose, Compose:initializeView, and Compose:applyChanges durations were lower in current than baseline.

The `baseline` trace: 3 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tr ON tr.id=s.track_id
JOIN thread AS t ON t.utid=tr.utid
JOIN process AS p ON p.upid=t.upid
WHERE p.name='com.example.jetnews' AND s.name IN ('Compose:recompose','Compose:initializeView','Compose:applyChanges')
GROUP BY s.name ORDER BY s.name;
```

The `current` trace: 3 rows.

```sql
SELECT s.name, count(*) AS occurrences, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice AS s
JOIN thread_track AS tr ON tr.id=s.track_id
JOIN thread AS t ON t.utid=tr.utid
JOIN process AS p ON p.upid=t.upid
WHERE p.name='com.example.jetnews' AND s.name IN ('Compose:recompose','Compose:initializeView','Compose:applyChanges')
GROUP BY s.name ORDER BY s.name;
```

### c3. Both traces recorded 20 class-verification slices for com.example.jetnews.ui.interests.InterestsScreenKt, but neither trace shows an increase in that count.

The `baseline` trace: 1 row.

```sql
SELECT name, count(*) AS occurrences
FROM slice
WHERE name = 'VerifyClass com.example.jetnews.ui.interests.InterestsScreenKt'
GROUP BY name;
```

The `current` trace: 1 row.

```sql
SELECT name, count(*) AS occurrences
FROM slice
WHERE name = 'VerifyClass com.example.jetnews.ui.interests.InterestsScreenKt'
GROUP BY name;
```

### c4. The range's relevant UI changes are the smaller Interests-row thumbnail and divider in InterestsScreen.kt, introduced by cd4f22cbbddcc8efac9413ac2678b06e321492aa, and the 40 dp topic-selection button introduced by 3e2fdaf2216b048731671bb61bd0fe7d2f2372a8; neither is supported as a performance culprit by the measured frame data.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
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

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so small differences can be run-to-run noise.
- The current capture metadata identifies a debuggable build on an SDK 36 emulator.
- Startup TTID and binder-wait totals moved independently of the selected frame-p95 metric; they were not used to declare a frame-performance regression.

## Run

`gpt-5.6-luna` on openai, effort high: 63 tool calls, $0.0290, 302 s.
Tokens: 48 input, 336,743 cache read, 36,079 cache write, 11,060 output.
