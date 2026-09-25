# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`
- **Verified:** 5 claims kept, 0 dropped; 13 of 13 citations passed
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

### c1. Reachable Java objects increased from 399535 in the baseline trace to 401322 in the current trace.

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

### c2. The increase is concentrated in Compose state and PostCards-generated listener objects: SnapshotMutableStateImpl$StateStateRecord is 1027 versus 1747, while PostCardsKt$$ExternalSyntheticLambda2 is 30 versus 360 between baseline and current.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY type_name ORDER BY reachable_objects DESC
```

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6','com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9') GROUP BY type_name ORDER BY reachable_objects DESC
```

### c3. In the current heap, FakePostsRepository has a favoritesListeners ArrayList, and that list retains 360 PostCardsKt$$ExternalSyntheticLambda2 listener objects.

The `current` trace: 1 row.

```sql
WITH latest AS (SELECT MAX(graph_sample_ts) AS ts FROM heap_graph_object), repo AS (SELECT o.id FROM heap_graph_object o JOIN latest l ON o.graph_sample_ts=l.ts JOIN heap_graph_class c ON c.id=o.type_id WHERE COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.data.posts.impl.FakePostsRepository'), listeners AS (SELECT r.owned_id AS list_id FROM heap_graph_reference r JOIN repo ON r.owner_id=repo.id WHERE r.field_name='com.example.jetnews.data.posts.impl.FakePostsRepository.favoritesListeners'), arrays AS (SELECT r.owned_id AS array_id FROM heap_graph_reference r JOIN listeners l ON r.owner_id=l.list_id WHERE r.field_name='java.util.ArrayList.elementData') SELECT COUNT(DISTINCT r.owned_id) AS retained_listener_lambdas FROM heap_graph_reference r JOIN arrays a ON r.owner_id=a.array_id JOIN heap_graph_object o ON o.id=r.owned_id JOIN heap_graph_class c ON c.id=o.type_id WHERE COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
```

The `current` trace: 3 rows.

```sql
WITH latest AS (SELECT MAX(graph_sample_ts) AS ts FROM heap_graph_object), repo AS (SELECT o.id,o.reference_set_id FROM heap_graph_object o JOIN heap_graph_class c ON c.id=o.type_id JOIN latest l ON o.graph_sample_ts=l.ts WHERE COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.data.posts.impl.FakePostsRepository') SELECT repo.id, r.owned_id, r.field_name, r.field_type_name, COALESCE(c.deobfuscated_name,c.name) AS owned_type FROM repo JOIN heap_graph_reference r ON r.reference_set_id=repo.reference_set_id LEFT JOIN heap_graph_object o ON o.id=r.owned_id LEFT JOIN heap_graph_class c ON c.id=o.type_id ORDER BY r.field_name
```

### c4. The baseline contains 30 PostCardsKt$$ExternalSyntheticLambda2 objects, compared with 360 in the current trace.

The `baseline` trace: 1 row.

```sql
SELECT COALESCE(c.deobfuscated_name,c.name) AS type_name, COUNT(*) AS objects FROM heap_graph_object o JOIN heap_graph_class c ON c.id=o.type_id WHERE o.graph_sample_ts=(SELECT MAX(graph_sample_ts) FROM heap_graph_object) AND COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' GROUP BY type_name
```

The `current` trace: 1 row.

```sql
SELECT COALESCE(c.deobfuscated_name,c.name) AS type_name, COUNT(*) AS objects FROM heap_graph_object o JOIN heap_graph_class c ON c.id=o.type_id WHERE o.graph_sample_ts=(SELECT MAX(graph_sample_ts) FROM heap_graph_object) AND COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' GROUP BY type_name
```

### c5. Commit 9facdf1 adds the per-card bookmark state and direct favorites listener registration in PostCards.kt, plus the favoritesListeners storage and registration API in the repository implementations; the changed code directly matches the retained classes in the current heap.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`:

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

The `current` trace: 1 row.

```sql
WITH latest AS (SELECT MAX(graph_sample_ts) AS ts FROM heap_graph_object), repo AS (SELECT o.id FROM heap_graph_object o JOIN latest l ON o.graph_sample_ts=l.ts JOIN heap_graph_class c ON c.id=o.type_id WHERE COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.data.posts.impl.FakePostsRepository'), listeners AS (SELECT r.owned_id AS list_id FROM heap_graph_reference r JOIN repo ON r.owner_id=repo.id WHERE r.field_name='com.example.jetnews.data.posts.impl.FakePostsRepository.favoritesListeners'), arrays AS (SELECT r.owned_id AS array_id FROM heap_graph_reference r JOIN listeners l ON r.owner_id=l.list_id WHERE r.field_name='java.util.ArrayList.elementData') SELECT COUNT(DISTINCT r.owned_id) AS retained_listener_lambdas FROM heap_graph_reference r JOIN arrays a ON r.owner_id=a.array_id JOIN heap_graph_object o ON o.id=r.owned_id JOIN heap_graph_class c ON c.id=o.type_id WHERE COALESCE(c.deobfuscated_name,c.name)='com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture per side is available, so small whole-heap differences can contain run-to-run noise.
- The current run is a debuggable build captured on an emulator; the metric counts reachable objects in the last Java heap dump, not allocation rate or object size.

## Run

`gpt-5.6-luna` on openai, effort high: 40 tool calls, $0.0308, 208 s.
Tokens: 42 input, 302,807 cache read, 44,839 cache write, 11,284 output.
