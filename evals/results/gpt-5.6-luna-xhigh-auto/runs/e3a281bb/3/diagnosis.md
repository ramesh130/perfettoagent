# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
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

### c2. The increase is localized to Compose state and the home-screen bookmark listener closure: PostCardsKt$$ExternalSyntheticLambda2 grew from 30 to 360 objects, while ParcelableSnapshotMutableState grew from 526 to 886 objects.

The `baseline` trace: 4 rows.

```sql
SELECT c.name AS type_name, COUNT(*) AS reachable_objects, SUM(o.self_size) AS self_bytes, SUM(o.native_size) AS native_bytes FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id=o.type_id WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object) AND c.name IN ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','com.example.jetnews.data.posts.impl.FakePostsRepository') GROUP BY c.name ORDER BY c.name
```

The `current` trace: 4 rows.

```sql
SELECT c.name AS type_name, COUNT(*) AS reachable_objects, SUM(o.self_size) AS self_bytes, SUM(o.native_size) AS native_bytes FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id=o.type_id WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object) AND c.name IN ('com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2','androidx.compose.runtime.ParcelableSnapshotMutableState','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','com.example.jetnews.data.posts.impl.FakePostsRepository') GROUP BY c.name ORDER BY c.name
```

### c3. In the current com.example.jetnews heap, FakePostsRepository.favoritesListeners points to an ArrayList whose backing array retains PostCardsKt$$ExternalSyntheticLambda2 instances; those closures reference both a Post and a ParcelableSnapshotMutableState.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT p.upid, p.pid, p.name FROM process AS p JOIN android_heap_graph_class_aggregation AS h ON h.upid = p.upid GROUP BY p.upid, p.pid, p.name
```

The `current` trace: 3 rows.

```sql
SELECT r.owner_id, r.owned_id, r.field_name, r.field_type_name, c2.name AS owned_type FROM heap_graph_reference AS r JOIN heap_graph_object AS o2 ON o2.id = r.owned_id JOIN heap_graph_class AS c2 ON c2.id = o2.type_id WHERE r.owner_id = 12793 ORDER BY r.field_name, r.owned_id
```

The `current` trace: 50 rows.

```sql
SELECT r.owner_id, r.owned_id, r.field_name, r.field_type_name, c.name AS owned_type FROM heap_graph_reference AS r JOIN heap_graph_object AS o ON o.id=r.owned_id JOIN heap_graph_class AS c ON c.id=o.type_id WHERE r.owner_id = 23150 LIMIT 50
```

The `current` trace: 50 rows.

```sql
SELECT r.owner_id, r.owned_id, r.field_name, r.field_type_name, c.name AS owner_type, c2.name AS owned_type FROM heap_graph_reference AS r LEFT JOIN heap_graph_object AS o ON o.id = r.owner_id LEFT JOIN heap_graph_class AS c ON c.id = o.type_id LEFT JOIN heap_graph_object AS o2 ON o2.id = r.owned_id LEFT JOIN heap_graph_class AS c2 ON c2.id = o2.type_id WHERE r.owner_id IN (SELECT o.id FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id WHERE c.name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2') LIMIT 50
```

### c4. Commit 9facdf1f56ddf777d1233826fd7fb332945ee418 introduced the PostCard call to addFavoritesListener and the FakePostsRepository list that appends listeners without a corresponding removal; blame at the range head assigns these relevant lines to that commit.

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
- This conclusion compares one heap snapshot per side; repeat captures would strengthen confidence in the absolute object-count delta.
- The regression identified here is reachable-heap growth rather than a measured UI frame-latency regression.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 57 tool calls, $0.0320, 260 s.
Tokens: 39 input, 283,414 cache read, 40,188 cache write, 13,564 output.
