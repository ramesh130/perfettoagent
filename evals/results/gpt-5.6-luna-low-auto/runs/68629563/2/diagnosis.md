# Regression

- **Metric:** `frame_ui_time_p95_ms` +5.6 ms (8.36 → 13.96 ms)
- **Culprit:** `9d695fef3c75` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 8.36 | 13.96 | +5.6 |

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

### c1. The app UI frame-time p95 increased from 8.3585 ms in the baseline trace to 13.957625 ms in the current trace, a 5.599125 ms regression.

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

### c2. The increased work is localized to the com.example.jetnews UI thread: its doFrame total rose from 176.159422 ms across 83 frames to 235.114998 ms across 84 frames.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, COUNT(*) AS frames, MAX(s.dur)/1e6 AS max_ms, SUM(s.dur)/1e6 AS total_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p ON p.upid = t.upid
GROUP BY p.name, t.name
ORDER BY total_ms DESC
LIMIT 20
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.name AS process_name, t.name AS thread_name, COUNT(*) AS frames, MAX(s.dur)/1e6 AS max_ms, SUM(s.dur)/1e6 AS total_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p ON p.upid = t.upid
GROUP BY p.name, t.name
ORDER BY total_ms DESC
LIMIT 20
```

### c3. The current trace contains 12 AndroidOwner:onTouch slices totaling 754.221709 ms, whereas the baseline contains 12 totaling 21.103667 ms.

The `baseline` trace: 20 rows.

```sql
SELECT s.name, COUNT(*) AS n, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid
WHERE t.name='example.jetnews' AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

The `current` trace: 20 rows.

```sql
SELECT s.name, COUNT(*) AS n, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid
WHERE t.name='example.jetnews' AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

### c4. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 changed the bookmark click handler in PostCards.kt to call Thread.sleep(BOOKMARK_HOLD_MS), matching the current trace's large input/onTouch delay and making it the likely cause.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

The `current` trace: 20 rows.

```sql
SELECT s.name, COUNT(*) AS n, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid
WHERE t.name='example.jetnews' AND s.dur>0
GROUP BY s.name ORDER BY total_ms DESC LIMIT 20
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture was available for each side, so run-to-run variation cannot be fully separated from the regression.
- The current build metadata identifies a debuggable build running on an Android emulator (sdk_gphone64_arm64, SDK 36).

## Run

`gpt-5.6-luna` on openai, effort low: 11 tool calls, $0.0098, 27 s.
Tokens: 18 input, 31,348 cache read, 22,905 cache write, 2,890 output.
