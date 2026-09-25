# Inconclusive

- **Metric:** `frame_p99_ms` +4.24 ms (66.91 → 71.15 ms)
- **Culprit:** none attributed
- **Verified:** 6 claims kept, 0 dropped; 14 of 14 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `frame_p99_ms` | ms | 66.91 | 71.15 | +4.24 |

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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

## Claims

### c1. The selected frame_p99_ms metric increased from 66.911833 ms in baseline to 71.153583 ms in current, a delta of 4.241749999999996 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH
  window_frames AS (
    SELECT DISTINCT f.upid, f.ui_thread_utid, a.id, a.ts, a.dur, a.jank_type
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 99 + 99) / 100) AS value
```

### c2. The rank-selected p99 frame is marked Prediction Error, Buffer Stuffing in both traces, rather than being uniquely attributed to app deadline misses.

The `baseline` trace: 7 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT f.upid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), r AS (SELECT dur/1e6 AS frame_ms,row_number() OVER(ORDER BY dur) rn,count(*) OVER() n,jank_type FROM w WHERE upid=(SELECT upid FROM app)) SELECT rn,n,frame_ms,jank_type FROM r WHERE rn BETWEEN (n*99+99)/100-3 AND (n*99+99)/100+3 ORDER BY rn
```

The `current` trace: 7 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT f.upid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), r AS (SELECT dur/1e6 AS frame_ms,row_number() OVER(ORDER BY dur) rn,count(*) OVER() n,jank_type FROM w WHERE upid=(SELECT upid FROM app)) SELECT rn,n,frame_ms,jank_type FROM r WHERE rn BETWEEN (n*99+99)/100-3 AND (n*99+99)/100+3 ORDER BY rn
```

### c3. The prominent named app-side work around the scenario is Compose lazy-list prefetch. Its compose and apply totals decreased in current, while prefetch measure time increased.

The `baseline` trace: 4 rows.

```sql
SELECT t.name AS track_name, s.name, count(*) AS count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN track t ON t.id=s.track_id WHERE s.name GLOB 'compose:lazy:prefetch:*' GROUP BY t.name,s.name ORDER BY total_ms DESC
```

The `current` trace: 4 rows.

```sql
SELECT t.name AS track_name, s.name, count(*) AS count, sum(s.dur)/1e6 AS total_ms, max(s.dur)/1e6 AS max_ms FROM slice s JOIN track t ON t.id=s.track_id WHERE s.name GLOB 'compose:lazy:prefetch:*' GROUP BY t.name,s.name ORDER BY total_ms DESC
```

### c4. The UI-only frame p95 did not worsen: it decreased from 26.550666 ms to 25.719583 ms.

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

### c5. The range contains two UI changes in the Interests flow that overlap the localized lazy-list work: commit 91eb564 changes the Interests row thumbnail from 56 dp to 48 dp, and commit 8cc4be4 changes the topic-selection button to 40 dp.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
8cc4be474ff991ddc6a1a01e6e2af962039a8f85
```

### c6. Because the p99 increase is in frames labeled with buffer-stuffing/prediction effects, while the UI-only p95 and some prefetch totals improved, this single pair of captures does not establish that either Interests commit caused a regression.

The `baseline` trace: 7 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT f.upid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), r AS (SELECT dur/1e6 AS frame_ms,row_number() OVER(ORDER BY dur) rn,count(*) OVER() n,jank_type FROM w WHERE upid=(SELECT upid FROM app)) SELECT rn,n,frame_ms,jank_type FROM r WHERE rn BETWEEN (n*99+99)/100-3 AND (n*99+99)/100+3 ORDER BY rn
```

The `current` trace: 7 rows.

```sql
INCLUDE PERFETTO MODULE android.frames.timeline;
WITH w AS (SELECT DISTINCT f.upid,a.id,a.dur,a.jank_type FROM android_frames_layers f JOIN actual_frame_timeline_slice a ON a.id=f.actual_frame_timeline_id WHERE f.layer_name NOT GLOB '*SurfaceView*' AND a.dur>0), app AS (SELECT upid FROM w GROUP BY upid ORDER BY count(*) DESC,upid LIMIT 1), r AS (SELECT dur/1e6 AS frame_ms,row_number() OVER(ORDER BY dur) rn,count(*) OVER() n,jank_type FROM w WHERE upid=(SELECT upid FROM app)) SELECT rn,n,frame_ms,jank_type FROM r WHERE rn BETWEEN (n*99+99)/100-3 AND (n*99+99)/100+3 ORDER BY rn
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
91eb564a995b5f47ac2de9f35636027304e2d356
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
8cc4be474ff991ddc6a1a01e6e2af962039a8f85
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture is available for each side, so a p99 change driven by a few frames may be run-to-run noise.
- The traces were captured on an Android emulator in a debuggable build.
- No sampled Java callstack data was available to attribute the affected prefetch slices to a specific application method.

## Run

`gpt-5.6-luna` on openai, effort high: 59 tool calls, $0.0328, 189 s.
Tokens: 36 input, 227,493 cache read, 49,131 cache write, 13,288 output.
