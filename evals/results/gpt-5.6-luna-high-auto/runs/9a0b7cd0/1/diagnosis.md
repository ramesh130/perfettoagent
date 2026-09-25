# Inconclusive

- **Metric:** `frame_p99_ms` +2.5 ms (64.41 → 66.91 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 1 dropped; 16 of 17 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p99_ms` | ms | 64.41 | 66.91 | +2.5 |

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

## Claims

### c2. The frame data comes from com.example.jetnews on the example.jetnews UI thread. The traces contain 2120 versus 2107 frames and 267 versus 268 app-deadline-missed frames; median frame time was lower in the current trace, while only the p99 tail increased.

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
SELECT
  (SELECT name FROM process WHERE upid = (SELECT upid FROM app)) AS process_name,
  (SELECT name FROM thread WHERE utid = (SELECT ui_thread_utid FROM frames LIMIT 1)) AS ui_thread_name,
  count(*) AS frame_count,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS p50_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS p95_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS p99_ms
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
  )
SELECT
  (SELECT name FROM process WHERE upid = (SELECT upid FROM app)) AS process_name,
  (SELECT name FROM thread WHERE utid = (SELECT ui_thread_utid FROM frames LIMIT 1)) AS ui_thread_name,
  count(*) AS frame_count,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS p50_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS p95_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS p99_ms
FROM frames
```

### c3. A separate runtime difference is garbage collection: com.example.jetnews spent 32.61125 ms across two collections in the baseline and 50.839 ms across two collections in the current trace. The current trace includes a full collection, whereas both baseline collections are young collections.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, COUNT(*) AS gc_count, SUM(e.gc_dur) / 1e6 AS gc_ms, MIN(e.gc_dur) / 1e6 AS min_gc_ms, MAX(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
GROUP BY e.upid, p.name
ORDER BY gc_ms DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT p.name AS process_name, COUNT(*) AS gc_count, SUM(e.gc_dur) / 1e6 AS gc_ms, MIN(e.gc_dur) / 1e6 AS min_gc_ms, MAX(e.gc_dur) / 1e6 AS max_gc_ms
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
GROUP BY e.upid, p.name
ORDER BY gc_ms DESC
```

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT e.*, p.name AS process_name
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
WHERE p.name = 'com.example.jetnews'
```

The `current` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.garbage_collection;
SELECT e.*, p.name AS process_name
FROM android_garbage_collection_events AS e
JOIN process AS p USING (upid)
WHERE p.name = 'com.example.jetnews'
```

### c4. The only range commit that changes the localized Interests UI changes thumbnails from 56.dp to 48.dp, and the current trace does not show increased image-decoding work: ImageDecoder_nDecodeBitmap fell from 27 calls and 37.729918 ms to 24 calls and 24.689539 ms.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, COUNT(*) AS decode_count, SUM(s.dur) / 1e6 AS decode_ms, MAX(s.dur) / 1e6 AS max_decode_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE s.name = 'ImageDecoder_nDecodeBitmap'
GROUP BY p.name, t.name
ORDER BY decode_ms DESC
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, t.name AS thread_name, COUNT(*) AS decode_count, SUM(s.dur) / 1e6 AS decode_ms, MAX(s.dur) / 1e6 AS max_decode_ms
FROM slice AS s
JOIN thread_track AS tt ON tt.id = s.track_id
JOIN thread AS t ON t.utid = tt.utid
JOIN process AS p ON p.upid = t.upid
WHERE s.name = 'ImageDecoder_nDecodeBitmap'
GROUP BY p.name, t.name
ORDER BY decode_ms DESC
```

### c5. The other functional commit in the range changes the home-screen widget refresh resource from one hour to 30 minutes; the trace evidence does not connect that background resource change to the UI-frame tail.

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
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
SELECT
  (SELECT name FROM process WHERE upid = (SELECT upid FROM app)) AS process_name,
  (SELECT name FROM thread WHERE utid = (SELECT ui_thread_utid FROM frames LIMIT 1)) AS ui_thread_name,
  count(*) AS frame_count,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS p50_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS p95_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS p99_ms
FROM frames
```

### c6. The p99 increase is likely run-to-run noise rather than an established regression: it is a single-tail movement with nearly unchanged app-deadline misses, while the larger GC movement also changes collection mode between captures and is not tied to a changed application callsite by the available trace evidence.

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
SELECT
  (SELECT name FROM process WHERE upid = (SELECT upid FROM app)) AS process_name,
  (SELECT name FROM thread WHERE utid = (SELECT ui_thread_utid FROM frames LIMIT 1)) AS ui_thread_name,
  count(*) AS frame_count,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS p50_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS p95_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS p99_ms
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
  )
SELECT
  (SELECT name FROM process WHERE upid = (SELECT upid FROM app)) AS process_name,
  (SELECT name FROM thread WHERE utid = (SELECT ui_thread_utid FROM frames LIMIT 1)) AS ui_thread_name,
  count(*) AS frame_count,
  sum(jank_type GLOB '*App Deadline Missed*') AS app_deadline_missed,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS p50_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS p95_ms,
  (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS p99_ms
FROM frames
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
77a061c0c715ba071167b2104fcebb2c2be12c8d
```

Commit, changing `app/src/main/res/values/integers.xml`:

```text
75ac1f34f73c512b2314e138de1cf6f8b8faa012
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side; p99 is a tail-sensitive metric and GC duration is also sensitive to runtime state.
- The available evidence does not establish a direct commit-to-callsite attribution, so no culprit is assigned.

## Dropped claims

### c1. The selected UI-frame tail metric increased from 64.408708 ms in the baseline to 66.911833 ms in the current trace, a delta of 2.503125 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort high: 49 tool calls, $0.0285, 170 s.
Tokens: 36 input, 178,499 cache read, 27,433 cache write, 15,049 output.
