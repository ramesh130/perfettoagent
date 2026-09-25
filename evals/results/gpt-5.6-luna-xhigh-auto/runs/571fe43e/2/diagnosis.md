# Inconclusive

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 13 of 13 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttfd_ms` | ms | 2,077.31 | 2,282.74 | +205.43 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Claims

### c1. Median cold-start TTFD increased from 2077.310959 ms in baseline to 2282.739626 ms in current, a delta of 205.428667 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

### c2. Initial display was not slower: median TTID changed from 349.682708 ms to 345.470333 ms. The measured TTFD difference therefore occurs after initial display.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

### c3. The trace localizes the change to the app main thread's UI traversal and MainActivity draw path: across the cold starts, traversal totaled 6985.105894 ms baseline versus 9086.851044 ms current, while MainActivity draw totaled 4735.372619 ms versus 6804.722472 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH st AS (
  SELECT s.startup_id, s.ts, t.time_to_full_display AS ttfd, t.upid,
         (SELECT utid FROM thread WHERE upid = t.upid ORDER BY tid LIMIT 1) AS utid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS t USING (startup_id)
  WHERE s.startup_type = 'cold'
), x AS (
  SELECT st.startup_id, sl.ts - st.ts AS rel_ns, sl.dur, sl.name
  FROM st JOIN slice AS sl JOIN thread_track AS tt ON tt.id = sl.track_id
  WHERE tt.utid = st.utid AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttfd
)
SELECT count(DISTINCT startup_id) AS cold_starts,
       sum(CASE WHEN name = 'traversal' THEN dur ELSE 0 END) / 1e6 AS traversal_total_ms,
       sum(CASE WHEN name = 'draw-VRI[MainActivity]' THEN dur ELSE 0 END) / 1e6 AS draw_total_ms,
       sum(CASE WHEN name = 'postAndWait' THEN dur ELSE 0 END) / 1e6 AS post_and_wait_total_ms,
       max(CASE WHEN name = 'traversal' THEN dur ELSE NULL END) / 1e6 AS traversal_max_ms
FROM x
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH st AS (
  SELECT s.startup_id, s.ts, t.time_to_full_display AS ttfd, t.upid,
         (SELECT utid FROM thread WHERE upid = t.upid ORDER BY tid LIMIT 1) AS utid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS t USING (startup_id)
  WHERE s.startup_type = 'cold'
), x AS (
  SELECT st.startup_id, sl.ts - st.ts AS rel_ns, sl.dur, sl.name
  FROM st JOIN slice AS sl JOIN thread_track AS tt ON tt.id = sl.track_id
  WHERE tt.utid = st.utid AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttfd
)
SELECT count(DISTINCT startup_id) AS cold_starts,
       sum(CASE WHEN name = 'traversal' THEN dur ELSE 0 END) / 1e6 AS traversal_total_ms,
       sum(CASE WHEN name = 'draw-VRI[MainActivity]' THEN dur ELSE 0 END) / 1e6 AS draw_total_ms,
       sum(CASE WHEN name = 'postAndWait' THEN dur ELSE 0 END) / 1e6 AS post_and_wait_total_ms,
       max(CASE WHEN name = 'traversal' THEN dur ELSE NULL END) / 1e6 AS traversal_max_ms
FROM x
```

### c4. There is no broad steady-state frame-time regression: frame p95 improved from 105.286959 ms to 99.414625 ms, and UI-time p95 improved from 55.602959 ms to 49.831417 ms.

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

### c5. The range does not establish a direct culprit. Its MainActivity commit is a launch-content variable rename, while its layout change is in DownloadsScreen; the trace only identifies generic MainActivity traversal/draw work rather than either changed source operation.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MainActivity.kt`:

```text
3a78df0448d62ccd759276ff8bb3b8739be06e46
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DownloadsScreen.kt`:

```text
d3c08a36dc94946928b95e758595f66aa083b2cd
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH st AS (
  SELECT s.startup_id, s.ts, t.time_to_full_display AS ttfd, t.upid,
         (SELECT utid FROM thread WHERE upid = t.upid ORDER BY tid LIMIT 1) AS utid
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS t USING (startup_id)
  WHERE s.startup_type = 'cold'
), x AS (
  SELECT st.startup_id, sl.ts - st.ts AS rel_ns, sl.dur, sl.name
  FROM st JOIN slice AS sl JOIN thread_track AS tt ON tt.id = sl.track_id
  WHERE tt.utid = st.utid AND sl.ts >= st.ts AND sl.ts < st.ts + st.ttfd
)
SELECT count(DISTINCT startup_id) AS cold_starts,
       sum(CASE WHEN name = 'traversal' THEN dur ELSE 0 END) / 1e6 AS traversal_total_ms,
       sum(CASE WHEN name = 'draw-VRI[MainActivity]' THEN dur ELSE 0 END) / 1e6 AS draw_total_ms,
       sum(CASE WHEN name = 'postAndWait' THEN dur ELSE 0 END) / 1e6 AS post_and_wait_total_ms,
       max(CASE WHEN name = 'traversal' THEN dur ELSE NULL END) / 1e6 AS traversal_max_ms
FROM x
```

## Caveats

- Each side is one capture, so the TTFD shift can reflect run-to-run media, decoder, or emulator scheduling variance even though the traces contain repeated cold starts.
- The current run is a non-debuggable benchmark build on an SDK 36 sdk_gphone64_arm64 emulator; baseline build metadata was not recorded.
- The trace evidence is sufficient to localize the difference to startup/UI timing, but not to identify a changed source method, so attributing it to a range commit would be speculative.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 84 tool calls, $0.0941, 431 s.
Tokens: 66 input, 1,344,584 cache read, 142,357 cache write, 26,354 output.
