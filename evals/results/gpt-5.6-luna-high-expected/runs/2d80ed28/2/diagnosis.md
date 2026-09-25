# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (correlated); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 8 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.21 | 54.17 | +27.96 |

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

### c1. The requested UI-time p95 increased from 26.206625 ms to 54.169584 ms, a 27.962959 ms regression.

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

### c2. The affected thread is the Jetnews UI thread: its doFrame p95 was 26.1930105 ms in baseline and 54.114459 ms in current.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  t.utid,
  t.name AS thread_name,
  p.upid,
  p.name AS process_name,
  COUNT(*) AS do_frame_count,
  MAX(s.dur) / 1e6 AS max_do_frame_ms,
  percentile(s.dur, 95) / 1e6 AS p95_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p USING (upid)
GROUP BY t.utid, t.name, p.upid, p.name
ORDER BY do_frame_count DESC;
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT
  t.utid,
  t.name AS thread_name,
  p.upid,
  p.name AS process_name,
  COUNT(*) AS do_frame_count,
  MAX(s.dur) / 1e6 AS max_do_frame_ms,
  percentile(s.dur, 95) / 1e6 AS p95_do_frame_ms
FROM android_frames_choreographer_do_frame AS d
JOIN slice AS s USING (id)
JOIN thread AS t ON t.utid = d.ui_thread_utid
JOIN process AS p USING (upid)
GROUP BY t.utid, t.name, p.upid, p.name
ORDER BY do_frame_count DESC;
```

### c3. The increase is concentrated in drawing: current Record View#draw() totals 64046.734836 ms with a 53.2343663 ms p95, versus 991.11459 ms total and a 0.9321836 ms p95 in baseline.

The `baseline` trace: 40 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH do_frames AS (
  SELECT d.id, s.ts, s.dur, s.track_id, d.ui_thread_utid
  FROM android_frames_choreographer_do_frame AS d
  JOIN slice AS s USING (id)
), nested AS (
  SELECT child.name, child.dur
  FROM do_frames AS d
  JOIN thread_track AS tt ON tt.id = d.track_id AND tt.utid = d.ui_thread_utid
  JOIN slice AS child ON child.track_id = d.track_id
    AND child.ts >= d.ts
    AND child.ts + child.dur <= d.ts + d.dur
    AND child.id != d.id
)
SELECT name, COUNT(*) AS occurrences, SUM(dur)/1e6 AS total_ms,
  MAX(dur)/1e6 AS max_ms, percentile(dur, 95)/1e6 AS p95_ms
FROM nested
WHERE name IS NOT NULL
GROUP BY name
ORDER BY total_ms DESC
LIMIT 40;
```

The `current` trace: 40 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH do_frames AS (
  SELECT d.id, s.ts, s.dur, s.track_id, d.ui_thread_utid
  FROM android_frames_choreographer_do_frame AS d
  JOIN slice AS s USING (id)
), nested AS (
  SELECT child.name, child.dur
  FROM do_frames AS d
  JOIN thread_track AS tt ON tt.id = d.track_id AND tt.utid = d.ui_thread_utid
  JOIN slice AS child ON child.track_id = d.track_id
    AND child.ts >= d.ts
    AND child.ts + child.dur <= d.ts + d.dur
    AND child.id != d.id
)
SELECT name, COUNT(*) AS occurrences, SUM(dur)/1e6 AS total_ms,
  MAX(dur)/1e6 AS max_ms, percentile(dur, 95)/1e6 AS p95_ms
FROM nested
WHERE name IS NOT NULL
GROUP BY name
ORDER BY total_ms DESC
LIMIT 40;
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 changed PostCards.kt to add a per-frame grain overlay in PostCardSimple, including drawWithContent and generation of 6,000 random values before drawing the overlay.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

### c5. The added grain-overlay lines in PostCards.kt are attributed by blame to commit bcd3ba1e926293a8681b6246ecdd271b5beb1592.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one capture per side, so ordinary run-to-run noise cannot be estimated; the size and concentration of the drawing increase make noise an unlikely explanation.
- The current run metadata describes a debuggable debug build on an Android emulator; results may differ from a release build or physical device.

## Run

`gpt-5.6-luna` on openai, effort high: 28 tool calls, $0.0171, 98 s.
Tokens: 33 input, 136,550 cache read, 23,186 cache write, 7,143 output.
