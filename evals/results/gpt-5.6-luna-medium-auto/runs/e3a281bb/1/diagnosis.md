# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
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

### c1. Reachable heap objects increased from 399535 to 401322, a delta of 1787 objects.

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

### c2. The largest class-level increases include SnapshotMutableStateImpl$StateStateRecord (+720), ParcelableSnapshotMutableState (+360), AtomicInt (+360), and the generated PostCardsKt$$ExternalSyntheticLambda2 class (+330).

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY type_name ORDER BY type_name
```

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY type_name ORDER BY type_name
```

### c3. Commit 9facdf1 introduced the PostCards listener registration and repository listener lists; the blamed lines show that listeners are added and invoked, with no removal path in the changed code. This directly matches the increased PostCards-generated lambda and Compose state objects in the current heap.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This conclusion is based on one baseline and one current capture; heap differences can be affected by scenario timing and run-to-run variation.
- The heap metric counts reachable objects, not bytes, and does not by itself prove that every additional object is permanently leaked.
- The current run metadata identifies a debuggable build on an Android emulator.

## Run

`gpt-5.6-luna` on openai, effort medium: 23 tool calls, $0.0099, 98 s.
Tokens: 18 input, 51,363 cache read, 20,805 cache write, 3,092 output.
