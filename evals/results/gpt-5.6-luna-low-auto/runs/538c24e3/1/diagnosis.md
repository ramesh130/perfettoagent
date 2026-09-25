# No regression

- **Metric:** `heap_growth_objects_by_class` -183 objects (399,535 → 399,352 objects)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. The measured reachable Java-object count decreased from 399535 objects in the baseline to 399352 objects in the current trace, a delta of -183 objects; this is not a performance regression by this metric.

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

### c2. The largest reported class-level decreases were 107 fewer float[] objects and 74 fewer java.util.WeakHashMap$Entry objects in the current trace.

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

### c3. The inspected range contains UI, documentation, build-configuration, and naming changes, but the available metric does not show a worsening attributable to any of them.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
87e9f4098fc8e5f29e9bc309aa75db0ea7692e44
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
f94b545f7b3e7b45b51de9e14750c895ad5d402f
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/HomeViewModel.kt`:

```text
60edbf10ac7899d8965982edb9b4d2841a913df5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- The frame, startup, binder, GC, blocking, and native-memory metrics had no usable data in these traces, so the diagnosis is limited to reachable Java-object count.
- Only one capture per side is available; the -183-object difference may be run-to-run noise.
- The capture was from an emulator and a debuggable build, which limits generalization to production performance.

## Run

`gpt-5.6-luna` on openai, effort low: 11 tool calls, $0.0048, 85 s.
Tokens: 21 input, 42,467 cache read, 7,572 cache write, 1,693 output.
