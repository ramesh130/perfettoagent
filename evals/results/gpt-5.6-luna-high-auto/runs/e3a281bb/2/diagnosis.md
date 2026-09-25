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

### c1. The current trace has 401322 reachable Java heap objects versus 399535 in the baseline, an increase of 1787 objects.

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

### c2. The growth is localized to the app process: reachable PostCardsKt synthetic-lambda objects increased from 210 to 570.

The `baseline` trace: 1 row.

```sql
SELECT p.name AS process_name, p.pid, count(*) AS objects, sum(CASE WHEN o.reachable THEN 1 ELSE 0 END) AS reachable_objects FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id JOIN process AS p ON p.upid = o.upid WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name LIKE 'com.example.jetnews.ui.home.PostCardsKt%' GROUP BY p.name, p.pid ORDER BY objects DESC
```

The `current` trace: 1 row.

```sql
SELECT p.name AS process_name, p.pid, count(*) AS objects, sum(CASE WHEN o.reachable THEN 1 ELSE 0 END) AS reachable_objects FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id JOIN process AS p ON p.upid = o.upid WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name LIKE 'com.example.jetnews.ui.home.PostCardsKt%' GROUP BY p.name, p.pid ORDER BY objects DESC
```

### c3. The specific PostCardsKt$$ExternalSyntheticLambda2 class increased from 30 objects in the baseline to 360 in the current trace.

The `baseline` trace: 7 rows.

```sql
SELECT c.name AS class_name, count(*) AS objects, sum(CASE WHEN o.reachable THEN 1 ELSE 0 END) AS reachable_objects FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name LIKE 'com.example.jetnews.ui.home.PostCardsKt%' GROUP BY c.name ORDER BY c.name
```

The `current` trace: 8 rows.

```sql
SELECT c.name AS class_name, count(*) AS objects, sum(CASE WHEN o.reachable THEN 1 ELSE 0 END) AS reachable_objects FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name LIKE 'com.example.jetnews.ui.home.PostCardsKt%' GROUP BY c.name ORDER BY c.name
```

### c4. Likely retention mechanism: the current heap graph shows 360 of these lambda objects held through an ArrayList backing Object[]; each lambda captures a Post and ParcelableSnapshotMutableState. Commit 9facdf1 adds the remembered PostCards callback and the repository's mutable favorites-listener registration, which directly matches this retained object pattern.

The `current` trace: 1 row.

```sql
WITH target AS (SELECT DISTINCT r.owner_id AS array_id FROM heap_graph_reference AS r JOIN heap_graph_object AS o ON o.id = r.owned_id JOIN heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name = 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2') SELECT coalesce(owner_class.name, '<unknown>') AS owner_class, r.field_name, coalesce(ac.name, '<unknown>') AS owned_class, count(*) AS edges FROM heap_graph_reference AS r JOIN target ON target.array_id = r.owned_id LEFT JOIN heap_graph_object AS owner ON owner.id = r.owner_id LEFT JOIN heap_graph_class AS owner_class ON owner_class.id = owner.type_id LEFT JOIN heap_graph_class AS ac ON ac.id = (SELECT type_id FROM heap_graph_object WHERE id = r.owned_id) GROUP BY owner_class, r.field_name, ac.name ORDER BY edges DESC LIMIT 50
```

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

### c5. The regression is directly attributable to 9facdf1f56ddf777d1233826fd7fb332945ee418: it is the range commit that changed both PostCards.kt and the repository implementations to add this listener-based bookmark path.

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
- This conclusion is based on one capture per side; reachable-object counts can vary with lifecycle state and scenario repetition.
- The metric measures reachable Java objects at the last heap dump, not retained bytes or post-GC memory, so the object-count regression should be confirmed with repeated captures and a heap-retention investigation.

## Run

`gpt-5.6-luna` on openai, effort high: 36 tool calls, $0.0236, 171 s.
Tokens: 33 input, 205,234 cache read, 31,048 cache write, 9,792 output.
