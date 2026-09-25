# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

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

### c1. The app UI thread's p95 frame time increased from 26.206625 ms to 54.169584 ms, a 27.962959 ms increase.

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

### c2. The increased UI time is concentrated in drawing: the main UI thread's total AndroidOwner:draw time rose from 180.432279 ms to 63894.08142 ms, while traversal and draw-VRI[MainActivity] also increased substantially.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT s.name, count(*) AS cnt, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id WHERE tt.utid IN (SELECT ui_thread_utid FROM android_frames_layers) AND s.name IN ('traversal','draw-VRI[MainActivity]','Record View#draw()','AndroidOwner:draw') GROUP BY s.name ORDER BY total_ms DESC
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT s.name, count(*) AS cnt, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id WHERE tt.utid IN (SELECT ui_thread_utid FROM android_frames_layers) AND s.name IN ('traversal','draw-VRI[MainActivity]','Record View#draw()','AndroidOwner:draw') GROUP BY s.name ORDER BY total_ms DESC
```

### c3. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 added a per-frame drawWithContent grain effect to PostCardSimple, including generation of a 6,000-element random list and a drawRect operation.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

### c4. The added grain-effect lines in PostCards.kt are attributed by blame to commit bcd3ba1e926293a8681b6246ecdd271b5beb1592, directly connecting the changed drawing code to the range commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one baseline and one current capture, so run-to-run noise cannot be independently estimated.
- The current run metadata identifies a debuggable build on an Android emulator (sdk_gphone64_arm64, SDK 36).

## Run

`gpt-5.6-luna` on openai, effort low: 19 tool calls, $0.0068, 42 s.
Tokens: 18 input, 40,586 cache read, 9,519 cache write, 2,993 output.
