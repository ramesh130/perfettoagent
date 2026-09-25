# Regression

- **Metric:** `frame_ui_time_p95_ms` +5.6 ms (8.36 → 13.96 ms)
- **Culprit:** `9d695fef3c75` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The app UI-time p95 increased from 8.3585 ms in the baseline to 13.957625 ms in the current trace, a 5.599125 ms regression.

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

### c2. The current trace contains six main-thread deliverInputEvent slices lasting 121.235375–125.174125 ms, whereas the baseline's corresponding input slices were only 0.702417–3.479166 ms.

The `current` trace: 6 rows.

```sql
SELECT s.name, s.dur/1e6 AS dur_ms, t.utid, t.name AS thread_name
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid
WHERE s.name LIKE 'deliverInputEvent%' AND s.dur > 100000000
ORDER BY s.dur DESC LIMIT 20
```

The `baseline` trace: 30 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers AS f JOIN actual_frame_timeline_slice AS a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (SELECT upid, ui_thread_utid FROM window_frames GROUP BY upid, ui_thread_utid ORDER BY count(*) DESC LIMIT 1)
SELECT s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track t ON t.id=s.track_id
WHERE t.utid=(SELECT ui_thread_utid FROM app) AND s.depth=0 AND s.dur>0 AND s.name NOT GLOB 'Choreographer#doFrame*'
GROUP BY s.name ORDER BY total_ms DESC LIMIT 30
```

### c3. Those long current input handlers spend approximately 120 ms each in the sleeping state, matching a deliberate UI-thread delay rather than ordinary frame-work variation.

The `current` trace: 20 rows.

```sql
SELECT s.name AS input_name, ts.state, sum(min(s.ts+s.dur,ts.ts+ts.dur)-max(s.ts,ts.ts))/1e6 AS overlap_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread_state ts ON ts.utid=tt.utid AND ts.ts < s.ts+s.dur AND s.ts < ts.ts+ts.dur
WHERE s.name LIKE 'deliverInputEvent%' AND s.dur > 100000000
GROUP BY s.name,ts.state ORDER BY overlap_ms DESC
```

### c4. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 added Thread.sleep(BOOKMARK_HOLD_MS) to the bookmark click handler and defined BOOKMARK_HOLD_MS as 120L; blame identifies that commit as the introducer of both lines.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

### c5. The exact 120 ms delay introduced by the commit is consistent with the approximately 120 ms sleeping intervals observed in the current input handlers, making this commit the likely cause.

The `current` trace: 20 rows.

```sql
SELECT s.name AS input_name, ts.state, sum(min(s.ts+s.dur,ts.ts+ts.dur)-max(s.ts,ts.ts))/1e6 AS overlap_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread_state ts ON ts.utid=tt.utid AND ts.ts < s.ts+s.dur AND s.ts < ts.ts+ts.dur
WHERE s.name LIKE 'deliverInputEvent%' AND s.dur > 100000000
GROUP BY s.name,ts.state ORDER BY overlap_ms DESC
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so smaller changes may contain run-to-run noise; the observed UI-thread delay is large relative to that limitation.
- The current run metadata identifies a debuggable build on an Android emulator, which may affect absolute timing.

## Run

`gpt-5.6-luna` on openai, effort medium: 30 tool calls, $0.0125, 58 s.
Tokens: 24 input, 87,768 cache read, 16,375 cache write, 5,572 output.
