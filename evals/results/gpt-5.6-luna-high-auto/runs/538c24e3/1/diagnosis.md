# No regression

- **Metric:** `heap_growth_objects_by_class` -183 objects (399,535 → 399,352 objects)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 12 of 12 citations passed
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

### c1. Reachable Java objects decreased from 399535 in baseline to 399352 in current, a delta of -183; the measured direction is lower rather than worse.

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

### c2. The largest class-level decreases are 107 fewer float[] objects and 74 fewer java.util.WeakHashMap$Entry objects.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'float[]' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'float[]'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'float[]' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'float[]'), 0) AS value
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'java.util.WeakHashMap$Entry' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'java.util.WeakHashMap$Entry'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'java.util.WeakHashMap$Entry' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'java.util.WeakHashMap$Entry'), 0) AS value
```

### c3. The com.example.jetnews app-class counts in the final heap snapshots are unchanged between baseline and current, so the observed object-count difference does not identify a changed app class.

The `baseline` trace: 159 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name GLOB 'com.example.*'
GROUP BY type_name
HAVING objects > 0
ORDER BY objects DESC
```

The `current` trace: 159 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name GLOB 'com.example.*'
GROUP BY type_name
HAVING objects > 0
ORDER BY objects DESC
```

### c4. The range includes UI-only changes such as smaller Interests thumbnails and additional dialog-button padding, but the trace does not directly connect either change to the observed heap-class differences; no culprit is assigned.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
f94b545f7b3e7b45b51de9e14750c895ad5d402f
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
87e9f4098fc8e5f29e9bc309aa75db0ea7692e44
```

The `baseline` trace: 159 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name GLOB 'com.example.*'
GROUP BY type_name
HAVING objects > 0
ORDER BY objects DESC
```

The `current` trace: 159 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name GLOB 'com.example.*'
GROUP BY type_name
HAVING objects > 0
ORDER BY objects DESC
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only the heap-object metric had data in these captures; frame, startup, GC, binder, and native-memory timing metrics were unavailable.
- This is one capture per side, so the small object-count decrease may be run-to-run noise rather than a meaningful change.

## Run

`gpt-5.6-luna` on openai, effort high: 35 tool calls, $0.0175, 147 s.
Tokens: 21 input, 75,259 cache read, 30,094 cache write, 7,053 output.
