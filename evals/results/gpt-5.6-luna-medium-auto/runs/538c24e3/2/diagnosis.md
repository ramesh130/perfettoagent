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

### c1. Reachable heap objects decreased from 399535 in the baseline to 399352 in the current trace, a delta of -183 objects; this is not a regression for the selected metric.

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

### c2. The largest observed class counts were effectively unchanged between traces; for example, java.lang.String remained at 106572 objects and java.lang.HashMap$Node remained at 36059 objects.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
GROUP BY type_name
ORDER BY objects DESC
LIMIT 20
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
GROUP BY type_name
ORDER BY objects DESC
LIMIT 20
```

### c3. The range's endpoint changes only the fewer-stories dialog button padding from 15 dp to 16 dp in PostCards.kt; the trace evidence does not show a corresponding heap regression attributable to it.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
87e9f4098fc8e5f29e9bc309aa75db0ea7692e44
```

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

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is limited to reachable Java heap objects: frame-timing, startup, binder, GC, and native-heap metrics returned no data for these traces.
- There is only one capture per side, and the captures were made on an emulator in a debuggable build, so small changes should not be treated as conclusive evidence of runtime performance.

## Run

`gpt-5.6-luna` on openai, effort medium: 23 tool calls, $0.0088, 125 s.
Tokens: 24 input, 68,303 cache read, 14,052 cache write, 3,248 output.
