# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`
- **Verified:** 5 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. Reachable Java objects increased from 399535 in the baseline heap dump to 401322 in the current dump, a delta of 1787 objects.

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

### c2. The largest class-level increases include SnapshotMutableStateImpl$StateStateRecord, up by 720 objects; ParcelableSnapshotMutableState, up by 360; and PostCardsKt$$ExternalSyntheticLambda2, up by 330. The current trace also contains PostCardsKt$$ExternalSyntheticLambda6 and Lambda9 instances that are absent from the baseline query results.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT graph_sample_ts, type_name, SUM(reachable_obj_count) AS reachable_obj_count, SUM(native_size_bytes) AS native_size_bytes FROM android_heap_graph_class_aggregation WHERE type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY graph_sample_ts, type_name ORDER BY graph_sample_ts, type_name
```

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT graph_sample_ts, type_name, SUM(reachable_obj_count) AS reachable_obj_count, SUM(native_size_bytes) AS native_size_bytes FROM android_heap_graph_class_aggregation WHERE type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY graph_sample_ts, type_name ORDER BY graph_sample_ts, type_name
```

### c3. Commit 9facdf1 introduces remembered bookmark state in PostCards and registers a repository listener for each post card.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

### c4. The same commit adds a mutable favorites-listener collection to the fake repositories, appends listeners, immediately invokes them, and invokes them again on favorite changes without adding a corresponding removal operation.

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

### c5. The heap-class increase is directly correlated with the PostCards-generated lambda and Compose state classes, making commit 9facdf1 the likely cause of the regression.

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT graph_sample_ts, type_name, SUM(reachable_obj_count) AS reachable_obj_count, SUM(native_size_bytes) AS native_size_bytes FROM android_heap_graph_class_aggregation WHERE type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY graph_sample_ts, type_name ORDER BY graph_sample_ts, type_name
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This diagnosis uses one capture per side, so run-to-run variation cannot be quantified.
- The metric reports reachable objects at the last heap dump; it does not by itself prove that every additional object is permanently leaked.
- The traces were recorded on an Android emulator using a debuggable build.

## Run

`gpt-5.6-luna` on openai, effort high: 25 tool calls, $0.0109, 112 s.
Tokens: 18 input, 55,507 cache read, 16,332 cache write, 4,727 output.
