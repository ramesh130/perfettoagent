# Regression

- **Metric:** `frame_ui_time_p95_ms` +3.54 ms (8.47 → 12 ms)
- **Culprit:** `ef58dc9dfbf9` (correlated); `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_ui_time_p95_ms` | ms | 8.47 | 12 | +3.54 |

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

### c1. The app UI-thread p95 frame time increased from 8.4665 ms in the baseline to 12.004708 ms in the current trace.

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

### c2. The regression is localized to the com.example.jetnews UI thread: its average Choreographer#doFrame duration rose from 2.066 ms to 2.796 ms, and the maximum rose from 13.859 ms to 16.207 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, t.name AS thread_name, t.utid, count(*) AS frame_count,
       round(avg(s.dur)/1e6,3) AS avg_do_frame_ms, round(max(s.dur)/1e6,3) AS max_do_frame_ms
FROM android_frames_choreographer_do_frame d
JOIN slice s USING (id)
JOIN thread t ON t.utid=d.ui_thread_utid
JOIN process p ON p.upid=t.upid
WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app))
GROUP BY p.name,t.name,t.utid
ORDER BY frame_count DESC
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.dur, a.jank_type
  FROM android_frames_layers AS f
  JOIN actual_frame_timeline_slice AS a ON a.id = f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur > 0
), app AS (
  SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1
)
SELECT p.name AS process_name, t.name AS thread_name, t.utid, count(*) AS frame_count,
       round(avg(s.dur)/1e6,3) AS avg_do_frame_ms, round(max(s.dur)/1e6,3) AS max_do_frame_ms
FROM android_frames_choreographer_do_frame d
JOIN slice s USING (id)
JOIN thread t ON t.utid=d.ui_thread_utid
JOIN process p ON p.upid=t.upid
WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app))
GROUP BY p.name,t.name,t.utid
ORDER BY frame_count DESC
```

### c3. Within UI frames, traversal time increased from 115.213 ms across 76 slices in the baseline to 171.38 ms across 78 slices in the current trace; the maximum traversal slice increased from 8.543 ms to 15.681 ms.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), df AS (SELECT d.id FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app)))
SELECT c.name,count(*) AS n,round(sum(c.dur)/1e6,3) AS total_ms,round(max(c.dur)/1e6,3) AS max_ms FROM slice c JOIN df ON c.parent_id=df.id GROUP BY c.name ORDER BY total_ms DESC LIMIT 30
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH window_frames AS (SELECT DISTINCT f.upid,f.ui_thread_utid,a.id,a.dur FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM window_frames GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), df AS (SELECT d.id FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM window_frames WHERE upid=(SELECT upid FROM app)))
SELECT c.name,count(*) AS n,round(sum(c.dur)/1e6,3) AS total_ms,round(max(c.dur)/1e6,3) AS max_ms FROM slice c JOIN df ON c.parent_id=df.id GROUP BY c.name ORDER BY total_ms DESC LIMIT 30
```

### c4. The attributed commit changes SelectTopicButton from a 36 dp size to a 40 dp size; blame assigns the changed size line to ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
ef58dc9dfbf9f06155d11669df2e9ef7040e4ce1
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so the frame-time delta may include run-to-run noise.
- The current trace metadata identifies an emulator (sdk_gphone64_arm64, SDK 36) and a debuggable debug build.
- The trace does not directly connect the increased traversal slices to SelectTopicButton, so the culprit attribution is correlated rather than direct.

## Run

`gpt-5.6-luna` on openai, effort medium: 31 tool calls, $0.0163, 66 s.
Tokens: 33 input, 136,081 cache read, 18,806 cache write, 7,363 output.
