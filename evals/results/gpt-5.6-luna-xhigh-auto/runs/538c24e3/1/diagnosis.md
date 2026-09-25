# No regression

- **Metric:** `heap_growth_objects_by_class` -183 objects (399,535 → 399,352 objects)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

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

### c1. The selected heap-object metric is lower in the current trace: 399535 reachable objects in baseline versus 399352 in current, so this metric did not worsen.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
```

### c2. The class-level differences are also decreases for the largest changed classes shown: float[] falls from 641 to 534 and java.util.WeakHashMap$Entry falls from 275 to 201.

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

### c3. The range contains a UI change to the Interests thumbnail size, and blame assigns that changed line to commit f94b545f7b3e7b45b51de9e14750c895ad5d402f; however, the trace evidence shows no heap-object regression, so no culprit is assigned.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
f94b545f7b3e7b45b51de9e14750c895ad5d402f
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available, so the small object-count difference may be run-to-run noise.
- This conclusion is limited to final Java-heap reachability; the other canned performance metrics were unavailable in these traces.
- The current capture metadata identifies a debuggable debug build running on an emulator.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 25 tool calls, $0.0150, 168 s.
Tokens: 21 input, 68,539 cache read, 18,063 cache write, 7,596 output.
