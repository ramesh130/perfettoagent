# Inconclusive

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 7 of 9 citations passed
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

### c2. The startup rows are for repeated cold starts of com.example.jetnews, and the per-start timings vary across both traces rather than identifying a single uniquely slow startup.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
ORDER BY s.ts
```

### c3. The frame-based metrics select com.google.android.apps.nexuslauncher as the process with the most window frames in both captures, so they do not directly localize Jetnews startup work.

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
  ), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count,
       (SELECT count(*) FROM thread t2 WHERE t2.utid IN (SELECT ui_thread_utid FROM frames)) AS ui_threads
FROM frames
JOIN process p USING (upid)
JOIN thread t ON t.utid = frames.ui_thread_utid
GROUP BY p.name, t.name
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
  ), frames AS (SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app))
SELECT p.name AS process_name, t.name AS thread_name, count(*) AS frame_count,
       (SELECT count(*) FROM thread t2 WHERE t2.utid IN (SELECT ui_thread_utid FROM frames)) AS ui_threads
FROM frames
JOIN process p USING (upid)
JOIN thread t ON t.utid = frames.ui_thread_utid
GROUP BY p.name, t.name
```

### c4. The range includes UI-size changes to the topic-selection button and Interests thumbnails, but the trace evidence does not directly connect either change to the startup-TTID increase.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display / 1e6 AS ttid_ms, d.time_to_full_display / 1e6 AS ttfd_ms
FROM android_startups AS s
JOIN android_startup_time_to_display AS d USING (startup_id)
ORDER BY s.ts
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one baseline/current capture pair on an emulator and a debuggable build, so the TTID difference may be run-to-run or environment noise.
- No commit in the range is directly attributable from the recorded startup rows; therefore the result is inconclusive rather than a commit-attributed regression.

## Dropped claims

### c1. Median cold-start time to initial display increased from 839.504417 ms in the baseline to 854.851167 ms in the current trace, a 15.34675 ms increase.

Dropped: citation 1: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause; citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

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
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Run

`gpt-5.6-luna` on openai, effort high: 63 tool calls, $0.0271, 284 s.
Tokens: 33 input, 193,925 cache read, 41,818 cache write, 10,611 output.
