# No regression

- **Metric:** `heap_growth_objects_by_class` -183 objects (399,535 → 399,352 objects)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 1 dropped; 9 of 10 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `heap_growth_objects_by_class` | objects | 399,535 | 399,352 | -183 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT sum(value) AS value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

)
```

## Claims

### c1. Reachable Java objects decreased from 399535 in the baseline to 399352 in the current trace, a measured delta of -183 objects; this is not a regression in the selected metric.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT sum(value) AS value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT sum(value) AS value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

)
```

### c2. Both heap graphs belong to the com.example.jetnews process.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT p.upid, p.name AS process_name, p.pid
FROM process AS p
WHERE p.upid IN (SELECT DISTINCT upid FROM android_heap_graph_class_aggregation)
ORDER BY p.upid
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT p.upid, p.name AS process_name, p.pid
FROM process AS p
WHERE p.upid IN (SELECT DISTINCT upid FROM android_heap_graph_class_aggregation)
ORDER BY p.upid
```

### c3. The largest reductions are in generic runtime classes: float[] fell from 641 to 534 objects and java.util.WeakHashMap$Entry fell from 275 to 201 objects; the changed-class rows do not identify an app class or method.

The `baseline` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
GROUP BY type_name
ORDER BY type_name
```

The `current` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
GROUP BY type_name
ORDER BY type_name
```

### c4. The range includes the thumbnail-size change in f94b545f7b3e7b45b51de9e14750c895ad5d402f, but the heap localization does not point to that Kotlin code, so no commit is directly attributed.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
f94b545f7b3e7b45b51de9e14750c895ad5d402f
```

The `current` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
GROUP BY type_name
ORDER BY type_name
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one capture per side; the small object-count decrease may be run-to-run noise rather than a meaningful memory improvement.
- The selected metric is reachable-object count from the final Java heap graph, not allocation rate, retained bytes, or frame latency.
- The current run metadata identifies a debuggable debug build on an sdk_gphone64_arm64 emulator; baseline build metadata was not available.

## Dropped claims

### c5. The frame_p95_ms metric is unavailable because its SQL returns NULL on both traces, so these captures cannot establish a frame-latency regression.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 11 col 54 SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT upid FROM window_frames GROUP BY count(*) DESC, upid LIMIT 1
  ),
  frames AS (
    SELECT * FROM window_frames WHERE upid = (SELECT upid FROM app)
  ),
  ranked AS (
    SELECT dur AS ns, row_number() OVER (ORDER BY dur) AS rank, count(*) OVER () AS n
    FROM frames
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n * 95 + 99) / 100) AS value
```

## Run

`gpt-5.6-luna` on openai, effort xhigh: 44 tool calls, $0.0271, 251 s.
Tokens: 39 input, 187,411 cache read, 26,706 cache write, 13,921 output.
