# Regression

- **Metric:** `frame_ui_time_p95_ms` +22.31 ms (37.95 → 60.26 ms)
- **Culprit:** `60be8b69bd69` (correlated); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The app's UI-time p95 increased from 37.952167 ms in the baseline to 60.2595 ms in the current trace, a 22.307333 ms increase.

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

### c2. The regression is concentrated in the app's UI drawing path. In com.superplayer.demo doFrame slices, AndroidOwner:draw rose from 249.954786 ms total and a 52.69375 ms maximum in the baseline to 6800.699007 ms total and an 83.931625 ms maximum in the current trace; Record View#draw() and draw-VRI[MainActivity] also increased substantially.

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH df AS (SELECT d.upid, s.ts, s.dur, s.track_id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id) WHERE d.upid = (SELECT upid FROM process WHERE name = 'com.superplayer.demo' LIMIT 1)) SELECT c.name, COUNT(*) AS occurrences, SUM(c.dur) / 1e6 AS total_ms, MAX(c.dur) / 1e6 AS max_ms FROM df JOIN slice AS c ON c.track_id = df.track_id AND c.ts >= df.ts AND c.ts + c.dur <= df.ts + df.dur WHERE c.name IN ('AndroidOwner:draw', 'Record View#draw()', 'draw-VRI[MainActivity]') GROUP BY c.name ORDER BY c.name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH df AS (SELECT d.upid, s.ts, s.dur, s.track_id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id) WHERE d.upid = (SELECT upid FROM process WHERE name = 'com.superplayer.demo' LIMIT 1)) SELECT c.name, COUNT(*) AS occurrences, SUM(c.dur) / 1e6 AS total_ms, MAX(c.dur) / 1e6 AS max_ms FROM df JOIN slice AS c ON c.track_id = df.track_id AND c.ts >= df.ts AND c.ts + c.dur <= df.ts + df.dur WHERE c.name IN ('AndroidOwner:draw', 'Record View#draw()', 'draw-VRI[MainActivity]') GROUP BY c.name ORDER BY c.name
```

### c3. Commit 60be8b69bd6967b234ecb466b5cd1312df2c9854 added a scrolling FeedScreen drawWithContent effect that creates a list of 1,000,000 random values and draws a grain overlay while scrolling. The head-of-range blame assigns these grain-related lines to that commit.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

### c4. The likely culprit is 60be8b69bd6967b234ecb466b5cd1312df2c9854: its per-scroll-frame FeedScreen drawing change matches the current trace's large increase in AndroidOwner:draw and is the strongest correlation in the range.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
60be8b69bd6967b234ecb466b5cd1312df2c9854
```

The `baseline` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH df AS (SELECT d.upid, s.ts, s.dur, s.track_id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id) WHERE d.upid = (SELECT upid FROM process WHERE name = 'com.superplayer.demo' LIMIT 1)) SELECT c.name, COUNT(*) AS occurrences, SUM(c.dur) / 1e6 AS total_ms, MAX(c.dur) / 1e6 AS max_ms FROM df JOIN slice AS c ON c.track_id = df.track_id AND c.ts >= df.ts AND c.ts + c.dur <= df.ts + df.dur WHERE c.name IN ('AndroidOwner:draw', 'Record View#draw()', 'draw-VRI[MainActivity]') GROUP BY c.name ORDER BY c.name
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH df AS (SELECT d.upid, s.ts, s.dur, s.track_id FROM android_frames_choreographer_do_frame AS d JOIN slice AS s USING (id) WHERE d.upid = (SELECT upid FROM process WHERE name = 'com.superplayer.demo' LIMIT 1)) SELECT c.name, COUNT(*) AS occurrences, SUM(c.dur) / 1e6 AS total_ms, MAX(c.dur) / 1e6 AS max_ms FROM df JOIN slice AS c ON c.track_id = df.track_id AND c.ts >= df.ts AND c.ts + c.dur <= df.ts + df.dur WHERE c.name IN ('AndroidOwner:draw', 'Record View#draw()', 'draw-VRI[MainActivity]') GROUP BY c.name ORDER BY c.name
```

## Caveats

- This conclusion is based on one capture per side, so ordinary run-to-run variation cannot be completely excluded.
- The traces were recorded on an Android emulator; the trace does not provide a direct application-level slice named for the grain allocation, so the commit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort high: 54 tool calls, $0.0285, 154 s.
Tokens: 60 input, 308,226 cache read, 36,774 cache write, 10,928 output.
