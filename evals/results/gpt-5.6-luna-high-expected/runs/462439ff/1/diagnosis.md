# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
- **Model's confidence:** high (never scored)

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

### c1. Reachable Java objects increased from 432751 in the baseline to 434935 in the current trace, a delta of 2184 objects.

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

### c2. The distinctive increase is in the listener-related object chain: ForwardingPlayer listeners grew from 17 to 165, ListenerHolder objects from 50 to 198, SuperPlayer wrapper lambdas from 16 to 164, and FeedRow listener objects from 4 to 152.

The `baseline` trace: 5 rows.

```sql
SELECT c.name AS class_name, COUNT(*) AS objects, SUM(o.reachable) AS reachable_objects
FROM __intrinsic_heap_graph_object o JOIN __intrinsic_heap_graph_class c ON c.id=o.type_id
WHERE c.name IN ('com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord')
GROUP BY c.name ORDER BY c.name
```

The `current` trace: 5 rows.

```sql
SELECT c.name AS class_name, COUNT(*) AS objects, SUM(o.reachable) AS reachable_objects
FROM __intrinsic_heap_graph_object o JOIN __intrinsic_heap_graph_class c ON c.id=o.type_id
WHERE c.name IN ('com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord')
GROUP BY c.name ORDER BY c.name
```

### c3. In the current heap, the wrapper lambda retains both the SuperPlayer and FeedRow listener; the FeedRow listener is retained through ListenerHolder and ForwardingListener objects. The corresponding edges are much smaller in the baseline.

The `current` trace: 7 rows.

```sql
SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, COUNT(*) AS edges
FROM __intrinsic_heap_graph_reference r
JOIN __intrinsic_heap_graph_object o ON o.id=r.owner_id
JOIN __intrinsic_heap_graph_class c ON c.id=o.type_id
JOIN __intrinsic_heap_graph_object oo ON oo.id=r.owned_id
JOIN __intrinsic_heap_graph_class oc ON oc.id=oo.type_id
WHERE oc.name IN ('com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder')
GROUP BY owner_class, r.field_name, owned_class ORDER BY edges DESC
```

The `baseline` trace: 7 rows.

```sql
SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, COUNT(*) AS edges
FROM __intrinsic_heap_graph_reference r
JOIN __intrinsic_heap_graph_object o ON o.id=r.owner_id
JOIN __intrinsic_heap_graph_class c ON c.id=o.type_id
JOIN __intrinsic_heap_graph_object oo ON oo.id=r.owned_id
JOIN __intrinsic_heap_graph_class oc ON oc.id=oo.type_id
WHERE oc.name IN ('com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder')
GROUP BY owner_class, r.field_name, owned_class ORDER BY edges DESC
```

### c4. Commit 6efb841e removed the listener cleanup from SuperPlayer.resetForReuse(): it stopped removing each wrapped listener from the delegate and stopped clearing wrappedListeners. This directly matches the retained listener chain in the current heap.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

The `current` trace: 7 rows.

```sql
SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, COUNT(*) AS edges
FROM __intrinsic_heap_graph_reference r
JOIN __intrinsic_heap_graph_object o ON o.id=r.owner_id
JOIN __intrinsic_heap_graph_class c ON c.id=o.type_id
JOIN __intrinsic_heap_graph_object oo ON oo.id=r.owned_id
JOIN __intrinsic_heap_graph_class oc ON oc.id=oo.type_id
WHERE oc.name IN ('com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder')
GROUP BY owner_class, r.field_name, owned_class ORDER BY edges DESC
```

## Caveats

- This conclusion is based on one heap dump per trace, so smaller changes can be affected by capture-to-capture noise.
- The metric measures reachable object counts, not allocation rate or retained bytes; the trace establishes the retained listener-object increase but not its eventual user-visible impact.

## Run

`gpt-5.6-luna` on openai, effort high: 34 tool calls, $0.0254, 108 s.
Tokens: 27 input, 186,421 cache read, 52,419 cache write, 7,105 output.
