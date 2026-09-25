# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`
- **Verified:** 5 claims kept, 0 dropped; 14 of 14 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

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

### c2. The change is in the com.example.jetnews process and is concentrated in Compose state objects and PostCards-generated callbacks: SnapshotMutableStateImpl$StateStateRecord grew from 1027 to 1747, ParcelableSnapshotMutableState from 526 to 886, AtomicInt from 610 to 970, and PostCardsKt$$ExternalSyntheticLambda2 from 30 to 360.

The `baseline` trace: 4 rows.

```sql
WITH latest AS (SELECT MAX(graph_sample_ts) AS ts FROM heap_graph_object), target(name) AS (VALUES ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord'), ('androidx.compose.runtime.ParcelableSnapshotMutableState'), ('androidx.compose.runtime.internal.AtomicInt'), ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'), ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6'), ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9')) SELECT p.name AS process, p.pid, c.name AS class, COUNT(*) AS objects FROM heap_graph_object o JOIN latest l ON o.graph_sample_ts=l.ts JOIN heap_graph_class c ON o.type_id=c.id JOIN process p ON o.upid=p.upid JOIN target t ON c.name=t.name WHERE o.reachable GROUP BY p.name, p.pid, c.name ORDER BY objects DESC
```

The `current` trace: 6 rows.

```sql
WITH latest AS (SELECT MAX(graph_sample_ts) AS ts FROM heap_graph_object), target(name) AS (VALUES ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord'), ('androidx.compose.runtime.ParcelableSnapshotMutableState'), ('androidx.compose.runtime.internal.AtomicInt'), ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'), ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6'), ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9')) SELECT p.name AS process, p.pid, c.name AS class, COUNT(*) AS objects FROM heap_graph_object o JOIN latest l ON o.graph_sample_ts=l.ts JOIN heap_graph_class c ON o.type_id=c.id JOIN process p ON o.upid=p.upid JOIN target t ON c.name=t.name WHERE o.reachable GROUP BY p.name, p.pid, c.name ORDER BY objects DESC
```

### c3. In the current heap, PostCardsKt$$ExternalSyntheticLambda2 instances are retained through an Object[] and ArrayList whose field is FakePostsRepository.favoritesListeners.

The `current` trace: 3 rows.

```sql
SELECT r.id, r.owner_id, r.owned_id, r.field_name, r.field_type_name, oc.name AS owner_class FROM heap_graph_reference r JOIN heap_graph_object oo ON oo.id=r.owner_id JOIN heap_graph_class oc ON oc.id=oo.type_id WHERE r.owned_id IN (56828, 56886, 58970)
```

The `current` trace: 1 row.

```sql
SELECT r.id, r.owner_id, r.owned_id, r.field_name, r.field_type_name, oc.name AS owner_class FROM heap_graph_reference r JOIN heap_graph_object oo ON oo.id=r.owner_id JOIN heap_graph_class oc ON oc.id=oo.type_id WHERE r.owned_id=23150
```

The `current` trace: 1 row.

```sql
SELECT r.id, r.owner_id, r.owned_id, r.field_name, r.field_type_name, oc.name AS owner_class FROM heap_graph_reference r JOIN heap_graph_object oo ON oo.id=r.owner_id JOIN heap_graph_class oc ON oc.id=oo.type_id WHERE r.owned_id=23146
```

### c4. Commit 9facdf1 introduced the PostCardSimple callback registration and the repository listener list that stores callbacks; the relevant lines are attributed to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

### c5. The trace evidence and the changed code directly connect the object increase to the new favorites-listener callbacks in PostCardsSimple, making 9facdf1 the direct culprit.

The `current` trace: 11 rows.

```sql
WITH latest AS (SELECT MAX(graph_sample_ts) AS ts FROM heap_graph_object) SELECT c.name AS class, COUNT(*) AS reachable_objects FROM heap_graph_object o JOIN latest l ON o.graph_sample_ts=l.ts JOIN heap_graph_class c ON o.type_id=c.id WHERE o.reachable AND (c.name LIKE 'com.example.jetnews.ui.home.PostCardsKt%' OR c.name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.internal.AtomicInt')) GROUP BY c.name ORDER BY reachable_objects DESC
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
- This compares one heap dump per side; reachable-object counts can have some run-to-run variability.
- The metric measures objects reachable at the final Java heap dump, not allocation rate or object size. The captures were from a debuggable debug build on an emulator.

## Run

`gpt-5.6-luna` on openai, effort high: 33 tool calls, $0.0262, 513 s.
Tokens: 36 input, 305,976 cache read, 41,228 cache write, 8,151 output.
