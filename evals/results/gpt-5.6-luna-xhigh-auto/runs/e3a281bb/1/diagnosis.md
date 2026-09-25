# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. Reachable Java objects increased from 399535 in the baseline trace to 401322 in the current trace, a delta of 1787 objects.

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

### c2. The increase is concentrated in Compose state and PostCards-generated objects: SnapshotMutableStateImpl$StateStateRecord rose from 1027 to 1747, ParcelableSnapshotMutableState from 526 to 886, AtomicInt from 610 to 970, and PostCardsKt$$ExternalSyntheticLambda2 from 30 to 360; the current trace also contains 30 each of Lambda6 and Lambda9.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord', 'androidx.compose.runtime.ParcelableSnapshotMutableState', 'androidx.compose.runtime.internal.AtomicInt', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9')
GROUP BY type_name
ORDER BY reachable_objects DESC
```

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord', 'androidx.compose.runtime.ParcelableSnapshotMutableState', 'androidx.compose.runtime.internal.AtomicInt', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9')
GROUP BY type_name
ORDER BY reachable_objects DESC
```

### c3. Commit 9facdf1f56ddf777d1233826fd7fb332945ee418 added remembered bookmark state and a repository favorites listener to PostCardSimple, and its repository implementations append those callbacks to a mutable listener list.

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

### c4. The new PostCards lambda/state objects align with the runtime code introduced by 9facdf1f56ddf777d1233826fd7fb332945ee418, making that commit the direct cause of the reachable-object regression.

The `current` trace: 6 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord', 'androidx.compose.runtime.ParcelableSnapshotMutableState', 'androidx.compose.runtime.internal.AtomicInt', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda6', 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda9')
GROUP BY type_name
ORDER BY reachable_objects DESC
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This comparison uses one final Java heap snapshot per trace; a small object-count delta can be affected by run-to-run noise.
- The current run is a debuggable debug build on an Android emulator, and frame-timeline data was unavailable, so this diagnosis does not establish a frame-latency regression.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 27 tool calls, $0.0183, 164 s.
Tokens: 24 input, 77,515 cache read, 22,455 cache write, 9,279 output.
