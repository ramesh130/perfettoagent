# Regression

- **Metric:** `heap_growth_objects_by_class` +1,787 objects (399,535 → 401,322 objects)
- **Culprit:** `9facdf1f56dd` (direct); `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`, `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/FakePostsRepository.kt`, `app/src/main/java/com/example/jetnews/data/posts/impl/BlockingFakePostsRepository.kt`
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

### c1. Reachable Java objects increased from 399535 in the baseline trace to 401322 in the current trace, a regression of 1787 objects.

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

### c2. The largest class-level increase was androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord, which grew from 1027 to 1747 reachable objects.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord'), 0) AS value
```

### c3. The com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2 class increased from 30 to 360 reachable objects, directly locating a substantial part of the growth in PostCards code.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'com.example.jetnews.ui.home.PostCardsKt$$ExternalSyntheticLambda2'), 0) AS value
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

### c4. Commit 9facdf1f56ddf777d1233826fd7fb332945ee418 added direct favorites listeners and remembered bookmark state in PostCards, and blame assigns the new PostCards lines to that commit.

Commit, changing `app/src/main/java/com/example/jetnews/ui/home/PostCards.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

Commit, changing `app/src/main/java/com/example/jetnews/data/posts/PostsRepository.kt`:

```text
9facdf1f56ddf777d1233826fd7fb332945ee418
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- The heap metric measures reachable objects at the last heap dump; it does not establish a UI-frame latency regression.
- Both captures are single runs, so run-to-run variation cannot be excluded.
- The current trace is from a debuggable build on an Android emulator (sdk_gphone64_arm64, SDK 36).
- Frame, startup, binder, GC, and scheduler-based metrics had no data because the traces lacked the required frame-timeline or related data sources.

## Run

`gpt-5.6-luna` on openai, effort medium: 18 tool calls, $0.0112, 109 s.
Tokens: 15 input, 34,122 cache read, 28,639 cache write, 2,759 output.
