# Regression

- **Metric:** `frame_ui_time_p95_ms` +77.46 ms (26.3 → 103.76 ms)
- **Culprit:** `e15d633e79d2` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 1 dropped; 7 of 8 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 26.3 | 103.76 | +77.46 |

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

### c2. The current trace's UI thread performed 536157 TextLayout:initLayout slices totaling 14372.316042 ms and 536157 Constructing StaticLayout slices totaling 11049.010378 ms; neither slice appears in the corresponding baseline query result.

The `baseline` trace: 2 rows.

```sql
SELECT t.name AS thread, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tr ON tr.id=s.track_id JOIN thread t ON t.utid=tr.utid JOIN process p ON p.upid=t.upid WHERE p.name='com.example.jetnews' AND s.name IN ('TextLayout:initLayout','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY t.name,s.name ORDER BY s.name,t.name
```

The `current` trace: 4 rows.

```sql
SELECT t.name AS thread, s.name, count(*) AS slices, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tr ON tr.id=s.track_id JOIN thread t ON t.utid=tr.utid JOIN process p ON p.upid=t.upid WHERE p.name='com.example.jetnews' AND s.name IN ('TextLayout:initLayout','Constructing StaticLayout','AndroidOwner:measureAndLayout','Compose:recompose') GROUP BY t.name,s.name ORDER BY s.name,t.name
```

### c3. Commit e15d633e79d2608f074e9c50a18f3064e15830d7 added repeated text measurement in PostTitle, including rememberTextMeasurer and a loop that measures the title at successive font sizes; blame attributes those lines to this commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
e15d633e79d2608f074e9c50a18f3064e15830d7
```

### c4. The same current trace also shows 184 garbage collections totaling 4498.861341 ms, compared with 3 collections totaling 59.403749 ms in the baseline, consistent with the additional UI work and allocations.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1) SELECT p.name AS process, p.upid, t.name AS main_thread, t.utid, count(*) AS gc_count, sum(g.gc_dur)/1e6 AS gc_ms FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid JOIN thread t ON t.utid=g.utid WHERE g.upid=(SELECT upid FROM app) GROUP BY p.name,p.upid,t.name,t.utid ORDER BY gc_ms DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
INCLUDE PERFETTO MODULE android.garbage_collection;
WITH window_frames AS (SELECT DISTINCT f.upid, f.ui_thread_utid, a.id FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC LIMIT 1) SELECT p.name AS process, p.upid, t.name AS main_thread, t.utid, count(*) AS gc_count, sum(g.gc_dur)/1e6 AS gc_ms FROM android_garbage_collection_events g JOIN process p ON p.upid=g.upid JOIN thread t ON t.utid=g.utid WHERE g.upid=(SELECT upid FROM app) GROUP BY p.name,p.upid,t.name,t.utid ORDER BY gc_ms DESC
```

### c5. The current run metadata identifies the build as commit 056ebc56e474567c92cdcb9b5fec04977a870845, which is the range head.

Commit:

```text
056ebc56e474567c92cdcb9b5fec04977a870845
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side has only one capture, so exact percentile values can include run-to-run noise; the change is nevertheless large and is accompanied by a new, dominant text-layout workload.
- The capture ran on an Android SDK 36 emulator in a debuggable build.

## Dropped claims

### c1. The app's UI-thread p95 frame time increased from 26.299542 ms in the baseline to 103.761958 ms in the current trace, a 77.462416 ms regression.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 23 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such column: s.dur

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 23 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ no such column: s.dur

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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
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
    SELECT s.dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM android_frames_choreographer_do_frame AS d
    JOIN slice AS s USING (id)
    WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM frames)
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort medium: 32 tool calls, $0.0127, 236 s.
Tokens: 21 input, 63,823 cache read, 20,120 cache write, 5,289 output.
