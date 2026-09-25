# No regression

- **Metric:** `heap_growth_objects_by_class` -183 objects (399,535 → 399,352 objects)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. Reachable Java objects decreased from 399535 in the baseline heap graph to 399352 in the current heap graph, a delta of -183 objects; the checked metric therefore shows no regression.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT graph_sample_ts, SUM(reachable_obj_count) AS reachable_objects, COUNT(DISTINCT type_name) AS class_count
FROM android_heap_graph_class_aggregation
GROUP BY graph_sample_ts
ORDER BY graph_sample_ts
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT graph_sample_ts, SUM(reachable_obj_count) AS reachable_objects, COUNT(DISTINCT type_name) AS class_count
FROM android_heap_graph_class_aggregation
GROUP BY graph_sample_ts
ORDER BY graph_sample_ts
```

### c2. The heap data is from the com.example.jetnews process in both captures, and the notable class-level changes are decreases in float[] objects from 641 to 534 and java.util.WeakHashMap$Entry objects from 275 to 201.

The `baseline` trace: 1 row.

```sql
SELECT h.ts, h.upid, p.name AS process_name, h.dump_reason, h.heap_size
FROM heap_graph AS h
LEFT JOIN process AS p USING (upid)
ORDER BY h.ts
```

The `current` trace: 1 row.

```sql
SELECT h.ts, h.upid, p.name AS process_name, h.dump_reason, h.heap_size
FROM heap_graph AS h
LEFT JOIN process AS p USING (upid)
ORDER BY h.ts
```

The `baseline` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name AS class_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
GROUP BY type_name
HAVING type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
ORDER BY class_name
```

The `current` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name AS class_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
GROUP BY type_name
HAVING type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
ORDER BY class_name
```

### c3. The range includes f94b545f7b3e7b45b51de9e14750c895ad5d402f, which changes the Interests-row thumbnail from 56.dp to 48.dp; git blame at the range head assigns the new .size(48.dp) line to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
f94b545f7b3e7b45b51de9e14750c895ad5d402f
```

### c4. The trace localization names generic runtime and Compose heap classes rather than a class or method changed by f94b545f7b3e7b45b51de9e14750c895ad5d402f, so the range does not provide a defensible direct culprit for the small heap decrease.

The `baseline` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name AS class_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
GROUP BY type_name
HAVING type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
ORDER BY class_name
```

The `current` trace: 9 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name AS class_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
GROUP BY type_name
HAVING type_name IN ('java.lang.Long[]', 'java.lang.Object[]', 'java.util.ArrayList', 'int[]', 'java.lang.ThreadLocal$ThreadLocalMap', 'java.lang.ThreadLocal$ThreadLocalMap$Entry[]', 'java.lang.ThreadLocal$ThreadLocalMap$Entry', 'java.util.WeakHashMap$Entry', 'float[]')
ORDER BY class_name
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
f94b545f7b3e7b45b51de9e14750c895ad5d402f
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- There is only one capture per side; a 183-object difference is small and may be run-to-run heap-dump noise.
- The available non-null comparison is reachable Java-object count; frame timing, binder, startup, GC, and native-heap metrics were unavailable in these captures.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 51 tool calls, $0.0294, 243 s.
Tokens: 42 input, 271,639 cache read, 36,203 cache write, 12,385 output.
