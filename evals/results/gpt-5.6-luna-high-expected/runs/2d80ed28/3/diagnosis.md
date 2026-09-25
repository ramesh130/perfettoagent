# Regression

- **Metric:** `frame_ui_time_p95_ms` +27.96 ms (26.21 → 54.17 ms)
- **Culprit:** `bcd3ba1e9262` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c1. The 95th-percentile UI-thread frame time increased from 26.206625 ms in the baseline to 54.169584 ms in the current trace, a delta of 27.962959 ms.

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

### c2. The affected workload is the com.example.jetnews UI thread named example.jetnews. Its doFrame average rose from 8.276 ms in the baseline to 47.282 ms in the current trace, with the maximum rising from 51.815 ms to 93.675 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.name AS process, t.tid, t.name AS thread, count(*) AS do_frames, round(avg(s.dur)/1e6,3) AS avg_doframe_ms, round(max(s.dur)/1e6,3) AS max_doframe_ms
FROM android_frames_choreographer_do_frame d JOIN slice s USING(id)
JOIN thread t ON t.utid=d.ui_thread_utid JOIN process p ON p.upid=t.upid
WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM wf WHERE upid=(SELECT upid FROM app))
GROUP BY p.name,t.tid,t.name
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH wf AS (
  SELECT DISTINCT f.upid, f.ui_thread_utid, a.id
  FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
  WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC, upid LIMIT 1)
SELECT p.name AS process, t.tid, t.name AS thread, count(*) AS do_frames, round(avg(s.dur)/1e6,3) AS avg_doframe_ms, round(max(s.dur)/1e6,3) AS max_doframe_ms
FROM android_frames_choreographer_do_frame d JOIN slice s USING(id)
JOIN thread t ON t.utid=d.ui_thread_utid JOIN process p ON p.upid=t.upid
WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM wf WHERE upid=(SELECT upid FROM app))
GROUP BY p.name,t.tid,t.name
```

### c3. The current trace localizes the added cost to Compose drawing: AndroidOwner:draw averages 46.334 ms over 1,379 doFrames, whereas the corresponding baseline report has only 0.612 ms average Record View#draw() and 0.450 ms average postAndWait across four occurrences each.

The `baseline` trace: 2 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH RECURSIVE wf AS (
 SELECT DISTINCT f.upid,f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), roots AS (SELECT s.id FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM wf WHERE upid=(SELECT upid FROM app))), ds(id) AS (SELECT id FROM roots UNION ALL SELECT s.id FROM slice s JOIN ds ON s.parent_id=ds.id)
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,2) AS total_ms, round(avg(s.dur)/1e6,3) AS avg_ms, round(max(s.dur)/1e6,3) AS max_ms
FROM ds JOIN slice s USING(id)
WHERE s.name IN ('AndroidOwner:draw','Record View#draw()','draw-VRI[MainActivity]','postAndWait')
GROUP BY s.name ORDER BY s.name
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH RECURSIVE wf AS (
 SELECT DISTINCT f.upid,f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), roots AS (SELECT s.id FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM wf WHERE upid=(SELECT upid FROM app))), ds(id) AS (SELECT id FROM roots UNION ALL SELECT s.id FROM slice s JOIN ds ON s.parent_id=ds.id)
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,2) AS total_ms, round(avg(s.dur)/1e6,3) AS avg_ms, round(max(s.dur)/1e6,3) AS max_ms
FROM ds JOIN slice s USING(id)
WHERE s.name IN ('AndroidOwner:draw','Record View#draw()','draw-VRI[MainActivity]','postAndWait')
GROUP BY s.name ORDER BY s.name
```

### c4. Commit bcd3ba1e926293a8681b6246ecdd271b5beb1592 adds a per-frame drawWithContent effect to PostCardSimple, including a 6,000-element random grain list and drawRect overlay; the changed lines are attributed to this commit at the range head. This directly matches the increased Compose draw cost.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
bcd3ba1e926293a8681b6246ecdd271b5beb1592
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH RECURSIVE wf AS (
 SELECT DISTINCT f.upid,f.ui_thread_utid FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), app AS (SELECT upid FROM wf GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), roots AS (SELECT s.id FROM android_frames_choreographer_do_frame d JOIN slice s USING(id) WHERE d.ui_thread_utid IN (SELECT ui_thread_utid FROM wf WHERE upid=(SELECT upid FROM app))), ds(id) AS (SELECT id FROM roots UNION ALL SELECT s.id FROM slice s JOIN ds ON s.parent_id=ds.id)
SELECT s.name, count(*) AS occurrences, round(sum(s.dur)/1e6,2) AS total_ms, round(avg(s.dur)/1e6,3) AS avg_ms, round(max(s.dur)/1e6,3) AS max_ms
FROM ds JOIN slice s USING(id)
WHERE s.name IN ('AndroidOwner:draw','Record View#draw()','draw-VRI[MainActivity]','postAndWait')
GROUP BY s.name ORDER BY s.name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis compares one capture per side, so ordinary run-to-run variance cannot be fully excluded; the observed increase is nevertheless large and the trace localization matches the changed code.
- The current run metadata identifies a debuggable debug build on an Android SDK 36 emulator, so absolute timings may not represent production hardware.

## Run

`gpt-5.6-luna` on openai, effort high: 33 tool calls, $0.0222, 114 s.
Tokens: 30 input, 112,102 cache read, 25,300 cache write, 11,376 output.
