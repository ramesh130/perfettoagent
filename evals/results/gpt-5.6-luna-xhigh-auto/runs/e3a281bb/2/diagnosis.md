# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c2. The increase is concentrated in Compose snapshot state and a generated home-card lambda: SnapshotMutableStateImpl$StateStateRecord increased from 1027 to 1747, ParcelableSnapshotMutableState from 526 to 886, AtomicInt from 610 to 970, and PostCardsKt$$ExternalSyntheticLambda2 from 30 to 360.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'androidx.compose.runtime.ParcelableSnapshotMutableState',
    'androidx.compose.runtime.internal.AtomicInt',
    'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
  )
GROUP BY type_name
ORDER BY type_name
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'androidx.compose.runtime.ParcelableSnapshotMutableState',
    'androidx.compose.runtime.internal.AtomicInt',
    'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
  )
GROUP BY type_name
ORDER BY type_name
```

### c3. Commit 9facdf1f56ddf777d1233826fd7fb332945ee418 changed PostCardSimple to create remembered mutable bookmark state, register a repository favorites listener, and use that state for the bookmark UI.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

### c4. The same commit added a repository-owned favoritesListeners list and appended callbacks to it; this is the likely mechanism retaining the extra PostCards lambdas and Compose state objects observed in the current heap.

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'androidx.compose.runtime.ParcelableSnapshotMutableState',
    'androidx.compose.runtime.internal.AtomicInt',
    'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
  )
GROUP BY type_name
ORDER BY type_name
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'androidx.compose.runtime.ParcelableSnapshotMutableState',
    'androidx.compose.runtime.internal.AtomicInt',
    'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
  )
GROUP BY type_name
ORDER BY type_name
```

### c5. Because the trace-localized PostCardsKt class corresponds to PostCards.kt, which was changed by 9facdf1f56ddf777d1233826fd7fb332945ee418, the attribution is direct rather than merely correlated with a commit in the range.

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'androidx.compose.runtime.ParcelableSnapshotMutableState',
    'androidx.compose.runtime.internal.AtomicInt',
    'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'
  )
GROUP BY type_name
ORDER BY type_name
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one capture was available for each build, so the magnitude should be confirmed with repeated captures using the same interaction sequence.
- This metric counts reachable Java objects in the final heap dump; it establishes an object-retention regression, not a direct frame-time or latency regression.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 47 tool calls, $0.0376, 252 s.
Tokens: 39 input, 393,851 cache read, 59,050 cache write, 12,426 output.
