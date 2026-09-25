# Regression

- **Metric:** `frame_ui_time_p95_ms` +22.31 ms (37.95 → 60.26 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 5 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. The app UI-time p95 increased from 37.952167 ms in baseline to 60.2595 ms in current, a delta of 22.307333 ms.

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

### c2. The change is concentrated in UI drawing: AndroidOwner:draw accounts for 249.95 ms across 676 slices in baseline versus 6800.7 ms across 427 slices in current; draw-VRI[MainActivity] similarly rises from 6583.59 ms to 8073.2 ms.

The `baseline` trace: 7 rows.

```sql
SELECT name, count(*) AS occurrences, round(sum(dur)/1e6,2) AS total_ms, round(max(dur)/1e6,2) AS max_ms FROM slice WHERE name IN ('draw-VRI[MainActivity]','Record View#draw()','AndroidOwner:draw','Recomposer:recompose','Compose:onForgotten','AndroidOwner:measureAndLayout','postAndWait') GROUP BY name ORDER BY name
```

The `current` trace: 7 rows.

```sql
SELECT name, count(*) AS occurrences, round(sum(dur)/1e6,2) AS total_ms, round(max(dur)/1e6,2) AS max_ms FROM slice WHERE name IN ('draw-VRI[MainActivity]','Record View#draw()','AndroidOwner:draw','Recomposer:recompose','Compose:onForgotten','AndroidOwner:measureAndLayout','postAndWait') GROUP BY name ORDER BY name
```

### c3. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 adds a scrolling FeedScreen drawWithContent path that creates a one-million-element random grain list and draws an overlay each frame.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c4. At the range head, the FeedScreen drawWithContent and grain-generation lines are attributed by blame to commit 60be8b69bd6967b234ecb466b5cd1312df2c9854.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c5. The current trace contains FeedScreen JIT slices, confirming that the localized UI activity includes the feed screen in the captured scenario.

The `current` trace: 4 rows.

```sql
SELECT name, count(*) AS occurrences, round(sum(dur)/1e6,2) AS total_ms FROM slice WHERE name GLOB '*FeedScreen*' GROUP BY name ORDER BY total_ms DESC
```

## Caveats

- This conclusion uses one capture per side, so run-to-run variance cannot be ruled out.
- The trace exposes generic Compose draw slices rather than a source-level stack pointing directly to the grain code; therefore the commit attribution is correlated, not direct.
- The captures were made on an Android emulator.

## Run

`gpt-5.6-luna` on openai, effort high: 42 tool calls, $0.0231, 121 s.
Tokens: 36 input, 170,999 cache read, 32,898 cache write, 9,532 output.
