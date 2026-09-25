# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 4 claims kept, 0 dropped; 9 of 9 citations passed
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

### c1. Reachable Java objects increased from 432751 in the baseline to 434935 in the current trace, a delta of 2184.

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

### c2. The localized increase is in retained playback listeners and feed-row objects: ForwardingPlayer$ForwardingListener rose from 17 to 165, while FeedRow$1$1$1$1 rose from 4 to 152.

The `baseline` trace: 2 rows.

```sql
SELECT c.name, count(*) AS reachable_objects FROM __intrinsic_heap_graph_object AS o JOIN __intrinsic_heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM __intrinsic_heap_graph_object) AND o.reachable = 1 AND c.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY c.name ORDER BY c.name
```

The `current` trace: 2 rows.

```sql
SELECT c.name, count(*) AS reachable_objects FROM __intrinsic_heap_graph_object AS o JOIN __intrinsic_heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM __intrinsic_heap_graph_object) AND o.reachable = 1 AND c.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY c.name ORDER BY c.name
```

### c3. The current heap retains 164 ListenerHolder references to ForwardingPlayer$ForwardingListener and 152 SuperPlayer lambda references to FeedRow objects; the corresponding baseline counts are 16 and 4.

The `baseline` trace: 5 rows.

```sql
SELECT c.name AS owner_class, oc.name AS owned_class, r.field_name, count(*) AS edges FROM __intrinsic_heap_graph_reference AS r JOIN __intrinsic_heap_graph_object AS o ON o.id = r.owner_id JOIN __intrinsic_heap_graph_class AS c ON c.id = o.type_id JOIN __intrinsic_heap_graph_object AS oo ON oo.id = r.owned_id JOIN __intrinsic_heap_graph_class AS oc ON oc.id = oo.type_id WHERE oc.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY c.name, oc.name, r.field_name ORDER BY oc.name, edges DESC
```

The `current` trace: 5 rows.

```sql
SELECT c.name AS owner_class, oc.name AS owned_class, r.field_name, count(*) AS edges FROM __intrinsic_heap_graph_reference AS r JOIN __intrinsic_heap_graph_object AS o ON o.id = r.owner_id JOIN __intrinsic_heap_graph_class AS c ON c.id = o.type_id JOIN __intrinsic_heap_graph_object AS oo ON oo.id = r.owned_id JOIN __intrinsic_heap_graph_class AS oc ON oc.id = oo.type_id WHERE oc.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY c.name, oc.name, r.field_name ORDER BY oc.name, edges DESC
```

### c4. Commit 6efb841e56d8071cddf03a32002d8413507b2797 removes the resetForReuse cleanup that removed delegate listeners and cleared wrappedListeners. That change directly matches the new retained-listener and retained-feed-row reference pattern.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

The `baseline` trace: 5 rows.

```sql
SELECT c.name AS owner_class, oc.name AS owned_class, r.field_name, count(*) AS edges FROM __intrinsic_heap_graph_reference AS r JOIN __intrinsic_heap_graph_object AS o ON o.id = r.owner_id JOIN __intrinsic_heap_graph_class AS c ON c.id = o.type_id JOIN __intrinsic_heap_graph_object AS oo ON oo.id = r.owned_id JOIN __intrinsic_heap_graph_class AS oc ON oc.id = oo.type_id WHERE oc.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY c.name, oc.name, r.field_name ORDER BY oc.name, edges DESC
```

The `current` trace: 5 rows.

```sql
SELECT c.name AS owner_class, oc.name AS owned_class, r.field_name, count(*) AS edges FROM __intrinsic_heap_graph_reference AS r JOIN __intrinsic_heap_graph_object AS o ON o.id = r.owner_id JOIN __intrinsic_heap_graph_class AS c ON c.id = o.type_id JOIN __intrinsic_heap_graph_object AS oo ON oo.id = r.owned_id JOIN __intrinsic_heap_graph_class AS oc ON oc.id = oo.type_id WHERE oc.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY c.name, oc.name, r.field_name ORDER BY oc.name, edges DESC
```

## Caveats

- There is only one capture per side; heap reachability is a last-heap-dump snapshot and can vary with scenario progress and garbage-collection timing.
- The selected metric measures reachable object counts, not retained bytes or user-visible latency, so the trace establishes a memory-retention regression rather than a quantified frame-time regression.
- The current run metadata describes a non-debuggable benchmark build running on an Android emulator.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 55 tool calls, $0.0350, 213 s.
Tokens: 39 input, 346,299 cache read, 60,757 cache write, 10,748 output.
