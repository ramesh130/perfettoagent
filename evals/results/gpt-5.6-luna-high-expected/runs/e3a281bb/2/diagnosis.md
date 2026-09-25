# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`
- **Verified:** 5 claims kept, 0 dropped; 11 of 11 citations passed
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

### c1. Reachable Java objects increased from 399535 in the baseline heap dump to 401322 in the current dump, a regression of 1787 objects.

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

### c2. The increase is concentrated in Compose state and the generated PostCards listener lambda: baseline versus current counts are ParcelableSnapshotMutableState 526 versus 886, StateStateRecord 1027 versus 1747, AtomicInt 610 versus 970, and PostCardsKt$$ExternalSyntheticLambda2 30 versus 360.

The `baseline` trace: 4 rows.

```sql
SELECT c.name AS class_name, COUNT(*) AS reachable_objects FROM __intrinsic_heap_graph_object o JOIN __intrinsic_heap_graph_class c ON c.id = o.type_id WHERE o.reachable = 1 AND o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM __intrinsic_heap_graph_object) AND c.name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord', 'androidx.compose.runtime.ParcelableSnapshotMutableState', 'androidx.compose.runtime.internal.AtomicInt', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY c.name ORDER BY c.name
```

The `current` trace: 6 rows.

```sql
SELECT c.name AS class_name, COUNT(*) AS reachable_objects FROM __intrinsic_heap_graph_object o JOIN __intrinsic_heap_graph_class c ON c.id = o.type_id WHERE o.reachable = 1 AND o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM __intrinsic_heap_graph_object) AND c.name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord', 'androidx.compose.runtime.ParcelableSnapshotMutableState', 'androidx.compose.runtime.internal.AtomicInt', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY c.name ORDER BY c.name
```

### c3. In the current app heap, FakePostsRepository.favoritesListeners retains 360 PostCardsKt$$ExternalSyntheticLambda2 objects; each such lambda captures a Post and an androidx.compose.runtime.MutableState.

The `current` trace: 1 row.

```sql
WITH listener_array AS (
  SELECT r.owned_id
  FROM __intrinsic_heap_graph_reference r
  JOIN __intrinsic_heap_graph_object owner ON owner.id = r.owner_id
  JOIN __intrinsic_heap_graph_class owner_class ON owner_class.id = owner.type_id
  WHERE owner.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM __intrinsic_heap_graph_object)
    AND owner.reachable = 1
    AND owner_class.name = 'com.example.jetnews.data.posts.impl.FakePostsRepository'
    AND r.field_name LIKE '%favoritesListeners%'
), element_data AS (
  SELECT r.owned_id
  FROM __intrinsic_heap_graph_reference r
  JOIN listener_array a ON a.owned_id = r.owner_id
  WHERE r.field_name = 'java.util.ArrayList.elementData'
)
SELECT owned_class.name AS listener_class, COUNT(*) AS listener_references
FROM __intrinsic_heap_graph_reference r
JOIN element_data d ON d.owned_id = r.owner_id
JOIN __intrinsic_heap_graph_object owned ON owned.id = r.owned_id
JOIN __intrinsic_heap_graph_class owned_class ON owned_class.id = owned.type_id
GROUP BY owned_class.name
ORDER BY listener_references DESC
```

The `current` trace: 2 rows.

```sql
SELECT c.name AS class_name, r.field_name, r.field_type_name, COUNT(*) AS references_count FROM __intrinsic_heap_graph_object o JOIN __intrinsic_heap_graph_class c ON c.id = o.type_id JOIN __intrinsic_heap_graph_reference r ON r.owner_id = o.id WHERE o.reachable = 1 AND o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM __intrinsic_heap_graph_object) AND c.name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' GROUP BY c.name, r.field_name, r.field_type_name ORDER BY r.field_name
```

### c4. Commit 9facdf1f changed PostCards.kt to add remembered bookmark state and register an addFavoritesListener callback, and changed the repository implementations to store and invoke those listeners. The new lines are attributed to that commit at the range head.

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

### c5. The heap evidence points directly to 9facdf1f: the increased generated class is under PostCardsKt, and that commit changed PostCards.kt and introduced the listener-retention path.

The `current` trace: 1 row.

```sql
SELECT c.name AS class_name, COUNT(*) AS reachable_objects FROM __intrinsic_heap_graph_object o JOIN __intrinsic_heap_graph_class c ON c.id = o.type_id WHERE o.reachable = 1 AND o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM __intrinsic_heap_graph_object) AND c.name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' GROUP BY c.name
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available, so residual run-to-run heap-dump noise cannot be ruled out; the retained-listener and class-count pattern nevertheless provides direct attribution to the changed code.

## Run

`gpt-5.6-luna` on openai, effort high: 58 tool calls, $0.0324, 213 s.
Tokens: 66 input, 491,392 cache read, 34,939 cache write, 11,550 output.
