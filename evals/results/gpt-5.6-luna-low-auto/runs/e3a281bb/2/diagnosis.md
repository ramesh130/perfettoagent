# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`
- **Verified:** 2 claims kept, 1 dropped; 5 of 6 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `heap_growth_objects_by_class` | objects | 399,535 | 401,322 | +1,787 |

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

### c1. Reachable Java-heap objects increased from 399535 in the baseline trace to 401322 in the current trace, a delta of 1787 objects.

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

### c3. Commit 9facdf1 added a repository favorites listener and registered a listener lambda inside PostCardSimple, directly changing the PostCards code associated with the increased synthetic lambda and Compose state objects.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side; heap counts can vary with scenario state and capture timing.
- The current run metadata identifies a debuggable build on an Android emulator.
- Frame, startup, binder, GC, and scheduler-based metrics had no data in these traces, so the measured regression is limited to reachable Java-heap objects.

## Dropped claims

### c2. The largest class-level increases were Compose snapshot state records (+720), ParcelableSnapshotMutableState (+360), AtomicInt (+360), and PostCardsKt$$ExternalSyntheticLambda2 (+330).

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 7 col 50 SELECT MAX(graph_sample_ts) FROM android.memory.heap_graph.heap_graph_class_aggregation ^ syntax error near '.'

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'), 0) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 7 col 50 SELECT MAX(graph_sample_ts) FROM android.memory.heap_graph.heap_graph_class_aggregation ^ syntax error near '.'

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android.memory.heap_graph.heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'), 0) AS value
```

## Run

`gpt-5.6-luna` on openai, effort low: 16 tool calls, $0.0093, 90 s.
Tokens: 15 input, 32,957 cache read, 26,906 cache write, 1,626 output.
