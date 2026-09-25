# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`
- **Verified:** 4 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. Reachable Java objects increased from 399535 in the baseline to 401322 in the current trace, a delta of 1787 objects.

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

### c2. The localized heap difference is in com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2, which increased from 30 reachable objects to 360.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT upid, type_name, reachable_obj_count
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT upid, type_name, reachable_obj_count
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
```

### c3. Commit 9facdf1f56ddf777d1233826fd7fb332945ee418 adds the PostCardSimple repository-listener registration and adds a mutable favorites-listener collection that appends callbacks in FakePostsRepository.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

### c4. The trace's PostCardsKt synthetic-lambda increase directly matches the new listener-registration code in PostCards.kt and the callback-retaining list in FakePostsRepository.kt, making this commit the direct culprit for the heap-growth regression.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT upid, type_name, reachable_obj_count
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis compares one capture per build; reachable-heap counts are scenario-dependent and should be confirmed with repeated captures.
- The current run is a debuggable debug build on an Android emulator, so absolute heap behavior may differ from a production device build.

## Run

`gpt-5.6-luna` on openai, effort high: 36 tool calls, $0.0152, 159 s.
Tokens: 24 input, 94,641 cache read, 21,709 cache write, 6,601 output.
