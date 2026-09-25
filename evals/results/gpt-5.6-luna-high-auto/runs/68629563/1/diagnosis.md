# Regression

- **Metric:** `frame_ui_time_p95_ms` +5.6 ms (8.36 → 13.96 ms)
- **Culprit:** `9d695fef3c75` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. The app's UI-thread frame p95 increased from 8.3585 ms in the baseline to 13.957625 ms in the current trace, a 5.599125 ms regression.

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

### c2. The regression is localized to touch handling: AndroidOwner:onTouch took 754.221709 ms across 12 input events in the current trace, with a 125.045875 ms maximum, versus 21.103667 ms total and 3.013416 ms maximum in the baseline.

The `baseline` trace: 1 row.

```sql
SELECT child.name, count(*) AS occurrences, sum(child.dur)/1e6 AS total_ms, max(child.dur)/1e6 AS max_ms
FROM slice parent JOIN slice child ON child.ts>=parent.ts AND child.ts+child.dur<=parent.ts+parent.dur
WHERE parent.name='deliverInputEvent' AND child.id!=parent.id AND child.name='AndroidOwner:onTouch'
GROUP BY child.name
```

The `current` trace: 1 row.

```sql
SELECT child.name, count(*) AS occurrences, sum(child.dur)/1e6 AS total_ms, max(child.dur)/1e6 AS max_ms
FROM slice parent JOIN slice child ON child.ts>=parent.ts AND child.ts+child.dur<=parent.ts+parent.dur
WHERE parent.name='deliverInputEvent' AND child.id!=parent.id AND child.name='AndroidOwner:onTouch'
GROUP BY child.name
```

### c3. Commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 changed the bookmark button from a direct onToggleFavorite callback to a handler that calls onToggleFavorite and then Thread.sleep(BOOKMARK_HOLD_MS), with BOOKMARK_HOLD_MS set to 120 ms.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

### c4. The changed handler and 120 ms hold constant are attributed to commit 9d695fef3c759e53d1bb01327b328a5d5e30bb87 by blame at the range head, matching the approximately 120 ms touch-handler durations in the current trace.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9d695fef3c759e53d1bb01327b328a5d5e30bb87
```

The `current` trace: 1 row.

```sql
SELECT child.name, count(*) AS occurrences, sum(child.dur)/1e6 AS total_ms, max(child.dur)/1e6 AS max_ms
FROM slice parent JOIN slice child ON child.ts>=parent.ts AND child.ts+child.dur<=parent.ts+parent.dur
WHERE parent.name='deliverInputEvent' AND child.id!=parent.id AND child.name='AndroidOwner:onTouch'
GROUP BY child.name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis compares one capture per side, so absolute frame percentiles can contain run-to-run noise; the repeated approximately 120 ms touch-handler signature makes this change much larger and more specific than ordinary percentile noise.
- The selected metric measures UI-thread doFrame time and does not by itself measure RenderThread or display-pipeline time.

## Run

`gpt-5.6-luna` on openai, effort high: 48 tool calls, $0.0302, 114 s.
Tokens: 39 input, 270,897 cache read, 44,128 cache write, 11,490 output.
