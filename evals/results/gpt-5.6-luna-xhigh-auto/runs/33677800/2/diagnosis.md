# No regression

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 5 claims kept, 0 dropped; 14 of 14 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 839.5 | 854.85 | +15.35 |

Measured by:

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

## Claims

### c1. The package-specific startup metric has 20 cold starts in each trace. Its median TTID increased from 839.504417 ms to 854.851167 ms, but the means increased only from 849.06890865 ms to 852.8640378 ms, indicating substantial run-to-run variation rather than a confirmed regression.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (SELECT d.time_to_initial_display AS ns FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id) WHERE s.package='com.example.jetnews' AND s.startup_type='cold' AND d.time_to_initial_display IS NOT NULL), ranked AS (SELECT ns,row_number() OVER(ORDER BY ns) AS r,count(*) OVER() AS n FROM cold)
SELECT count(*) AS cold_starts,avg(ns)/1e6 AS mean_ttid_ms,(SELECT ns/1e6 FROM ranked WHERE r=(n+1)/2) AS median_ttid_ms,min(ns)/1e6 AS min_ttid_ms,max(ns)/1e6 AS max_ttid_ms FROM cold
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (SELECT d.time_to_initial_display AS ns FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id) WHERE s.package='com.example.jetnews' AND s.startup_type='cold' AND d.time_to_initial_display IS NOT NULL), ranked AS (SELECT ns,row_number() OVER(ORDER BY ns) AS r,count(*) OVER() AS n FROM cold)
SELECT count(*) AS cold_starts,avg(ns)/1e6 AS mean_ttid_ms,(SELECT ns/1e6 FROM ranked WHERE r=(n+1)/2) AS median_ttid_ms,min(ns)/1e6 AS min_ttid_ms,max(ns)/1e6 AS max_ttid_ms FROM cold
```

### c2. The Jetnews UI frame distribution did not worsen: target-process frame p95 decreased from 248.582792 ms to 240.0765 ms, while UI doFrame p95 decreased from 233.890583 ms to 223.513583 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH frames AS (
 SELECT DISTINCT a.id,a.dur,a.jank_type,f.upid,f.ui_thread_utid
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id JOIN process p ON p.upid=f.upid
 WHERE p.name='com.example.jetnews' AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), ranked AS (SELECT dur/1e6 AS frame_ms,row_number() OVER(ORDER BY dur) AS r,count(*) OVER() AS n FROM frames)
SELECT count(*) AS frame_count,(SELECT frame_ms FROM ranked WHERE r=(n*50+99)/100) AS p50_ms,(SELECT frame_ms FROM ranked WHERE r=(n*95+99)/100) AS p95_ms,(SELECT frame_ms FROM ranked WHERE r=(n*99+99)/100) AS p99_ms,max(frame_ms) AS max_ms FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH frames AS (
 SELECT DISTINCT a.id,a.dur,a.jank_type,f.upid,f.ui_thread_utid
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id JOIN process p ON p.upid=f.upid
 WHERE p.name='com.example.jetnews' AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), ranked AS (SELECT dur/1e6 AS frame_ms,row_number() OVER(ORDER BY dur) AS r,count(*) OVER() AS n FROM frames)
SELECT count(*) AS frame_count,(SELECT frame_ms FROM ranked WHERE r=(n*50+99)/100) AS p50_ms,(SELECT frame_ms FROM ranked WHERE r=(n*95+99)/100) AS p95_ms,(SELECT frame_ms FROM ranked WHERE r=(n*99+99)/100) AS p99_ms,max(frame_ms) AS max_ms FROM ranked
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app_frames AS (
 SELECT DISTINCT f.ui_thread_utid,f.upid,a.id
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id JOIN process p ON p.upid=f.upid
 WHERE p.name='com.example.jetnews' AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), ranked AS (
 SELECT s.dur/1e6 AS ui_ms,row_number() OVER(ORDER BY s.dur) AS r,count(*) OVER() AS n
 FROM android_frames_choreographer_do_frame d JOIN slice s ON s.id=d.id
 WHERE (d.upid,d.ui_thread_utid) IN (SELECT upid,ui_thread_utid FROM app_frames)
)
SELECT count(*) AS do_frame_count,(SELECT ui_ms FROM ranked WHERE r=(n*50+99)/100) AS p50_ui_ms,(SELECT ui_ms FROM ranked WHERE r=(n*95+99)/100) AS p95_ui_ms,max(ui_ms) AS max_ui_ms FROM ranked
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH app_frames AS (
 SELECT DISTINCT f.ui_thread_utid,f.upid,a.id
 FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id JOIN process p ON p.upid=f.upid
 WHERE p.name='com.example.jetnews' AND f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
), ranked AS (
 SELECT s.dur/1e6 AS ui_ms,row_number() OVER(ORDER BY s.dur) AS r,count(*) OVER() AS n
 FROM android_frames_choreographer_do_frame d JOIN slice s ON s.id=d.id
 WHERE (d.upid,d.ui_thread_utid) IN (SELECT upid,ui_thread_utid FROM app_frames)
)
SELECT count(*) AS do_frame_count,(SELECT ui_ms FROM ranked WHERE r=(n*50+99)/100) AS p50_ui_ms,(SELECT ui_ms FROM ranked WHERE r=(n*95+99)/100) AS p95_ui_ms,max(ui_ms) AS max_ui_ms FROM ranked
```

### c3. The startup difference localizes to variable framework and rendering work, not to a source-named application slice: in representative startups, baseline had bindApplication at 352.332917 ms, Choreographer#doFrame at 319.893292 ms, and earlyPreloadGlContext at 42.907667 ms; current had bindApplication at 326.8875 ms, Choreographer#doFrame at 328.015542 ms, and earlyPreloadGlContext at 54.373334 ms.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT sl.name,count(*) AS count,sum(sl.dur)/1e6 AS total_ms
FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id) JOIN process p ON p.upid=d.upid JOIN thread th ON th.upid=p.upid JOIN thread_track tt ON tt.utid=th.utid JOIN slice sl ON sl.track_id=tt.id
WHERE s.startup_id=176 AND sl.ts>=s.ts AND sl.ts<s.ts_end AND sl.depth=0
  AND (sl.name='bindApplication' OR sl.name='earlyPreloadGlContext' OR sl.name GLOB 'Choreographer#doFrame *')
GROUP BY sl.name ORDER BY total_ms DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT sl.name,count(*) AS count,sum(sl.dur)/1e6 AS total_ms
FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id) JOIN process p ON p.upid=d.upid JOIN thread th ON th.upid=p.upid JOIN thread_track tt ON tt.utid=th.utid JOIN slice sl ON sl.track_id=tt.id
WHERE s.startup_id=235 AND sl.ts>=s.ts AND sl.ts<s.ts_end AND sl.depth=0
  AND (sl.name='bindApplication' OR sl.name='earlyPreloadGlContext' OR sl.name GLOB 'Choreographer#doFrame *')
GROUP BY sl.name ORDER BY total_ms DESC
```

### c4. The generic frame metric would select the launcher rather than Jetnews: the launcher has 2,851 baseline frames and 2,963 current frames, while the largest Jetnews process has only 30 frames in each trace. The package-specific startup metric is therefore the more relevant choice here.

The `baseline` trace: 22 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.upid,p.pid,p.name AS process_name,count(DISTINCT a.id) AS frame_rows
FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
JOIN process p ON p.upid=f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
GROUP BY p.upid,p.pid,p.name
ORDER BY frame_rows DESC
```

The `current` trace: 22 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
SELECT p.upid,p.pid,p.name AS process_name,count(DISTINCT a.id) AS frame_rows
FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id
JOIN process p ON p.upid=f.upid
WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0
GROUP BY p.upid,p.pid,p.name
ORDER BY frame_rows DESC
```

### c5. The range contains UI changes to the topic-selection button and Interests rows, but the trace does not identify either source path as the cause of the startup variation.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT sl.name,count(*) AS count,sum(sl.dur)/1e6 AS total_ms
FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id) JOIN process p ON p.upid=d.upid JOIN thread th ON th.upid=p.upid JOIN thread_track tt ON tt.utid=th.utid JOIN slice sl ON sl.track_id=tt.id
WHERE s.startup_id=176 AND sl.ts>=s.ts AND sl.ts<s.ts_end AND sl.depth=0
  AND (sl.name='bindApplication' OR sl.name='earlyPreloadGlContext' OR sl.name GLOB 'Choreographer#doFrame *')
GROUP BY sl.name ORDER BY total_ms DESC
```

The `current` trace: 3 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT sl.name,count(*) AS count,sum(sl.dur)/1e6 AS total_ms
FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id) JOIN process p ON p.upid=d.upid JOIN thread th ON th.upid=p.upid JOIN thread_track tt ON tt.utid=th.utid JOIN slice sl ON sl.track_id=tt.id
WHERE s.startup_id=235 AND sl.ts>=s.ts AND sl.ts<s.ts_end AND sl.depth=0
  AND (sl.name='bindApplication' OR sl.name='earlyPreloadGlContext' OR sl.name GLOB 'Choreographer#doFrame *')
GROUP BY sl.name ORDER BY total_ms DESC
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Each side is one capture, although each capture contains 20 cold starts; the remaining TTID shift is small relative to emulator, JIT, scheduling, and rendering variability.
- The current metadata describes a debuggable debug build on an sdk_gphone64_arm64 emulator; baseline build metadata was not recorded.
- No app stack samples or source-level slice names connect the measured framework/render slices to a changed method, so commit attribution is not justified.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 99 tool calls, $0.0561, 558 s.
Tokens: 63 input, 575,071 cache read, 59,798 cache write, 24,738 output.
