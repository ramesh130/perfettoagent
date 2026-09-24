# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 4 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `heap_growth_objects_by_class` | objects | 432,751 | 434,935 | +2,184 |

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

### c1. Reachable heap objects increased from 432751 in the baseline to 434935 in the current trace, a delta of 2184 objects.

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

### c2. The increase is concentrated in the listener and feed-object chain: ListenerSet$ListenerHolder rose from 50 to 198, ForwardingPlayer$ForwardingListener from 17 to 165, SuperPlayer synthetic listener lambdas from 16 to 164, and FeedScreen row listener objects from 4 to 152.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, reachable_obj_count, reachable_size_bytes, dominated_obj_count, dominated_size_bytes FROM android_heap_graph_class_aggregation WHERE graph_sample_ts=(SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord') ORDER BY type_name
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, reachable_obj_count, reachable_size_bytes, dominated_obj_count, dominated_size_bytes FROM android_heap_graph_class_aggregation WHERE graph_sample_ts=(SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord') ORDER BY type_name
```

### c3. In the current heap graph, the synthetic listener lambda retains both a SuperPlayer and FeedScreen row object, and ListenerSet$ListenerHolder retains ForwardingPlayer$ForwardingListener objects, matching unreleased player listeners.

The `current` trace: 19 rows.

```sql
WITH classes AS (SELECT id,name FROM __intrinsic_heap_graph_class),
objects AS (SELECT o.id,c.name FROM __intrinsic_heap_graph_object o JOIN classes c ON c.id=o.type_id WHERE o.graph_sample_ts=(SELECT MAX(ts) FROM __intrinsic_heap_graph))
SELECT owner.name AS owner_type, r.field_name, coalesce(owned.name,'<non-object>') AS owned_type, count(*) AS edges
FROM __intrinsic_heap_graph_reference r
JOIN objects owner ON owner.id=r.owner_id
LEFT JOIN objects owned ON owned.id=r.owned_id
WHERE owner.name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')
GROUP BY owner.name,r.field_name,owned_type ORDER BY owner.name,edges DESC LIMIT 100
```

### c4. Commit 6efb841e56d8071cddf03a32002d8413507b2797 changed SuperPlayer.resetForReuse by removing the synchronized cleanup that removed all wrapped listeners from the delegate and cleared the wrapped-listener map. This directly matches the listener-retention pattern in the current heap graph.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

The `current` trace: 19 rows.

```sql
WITH classes AS (SELECT id,name FROM __intrinsic_heap_graph_class),
objects AS (SELECT o.id,c.name FROM __intrinsic_heap_graph_object o JOIN classes c ON c.id=o.type_id WHERE o.graph_sample_ts=(SELECT MAX(ts) FROM __intrinsic_heap_graph))
SELECT owner.name AS owner_type, r.field_name, coalesce(owned.name,'<non-object>') AS owned_type, count(*) AS edges
FROM __intrinsic_heap_graph_reference r
JOIN objects owner ON owner.id=r.owner_id
LEFT JOIN objects owned ON owned.id=r.owned_id
WHERE owner.name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')
GROUP BY owner.name,r.field_name,owned_type ORDER BY owner.name,edges DESC LIMIT 100
```

## Caveats

- This conclusion is based on one capture per side and one heap-graph snapshot per trace.
- The metric counts reachable Java objects, not retained bytes or a direct user-visible latency measure.
- The captures are from an emulator benchmark, so absolute memory behavior may differ on physical devices.

## Run

`gpt-5.6-luna` on openai, effort high: 41 tool calls, $0.0290, 214 s.
Tokens: 36 input, 324,790 cache read, 53,146 cache write, 7,649 output.
