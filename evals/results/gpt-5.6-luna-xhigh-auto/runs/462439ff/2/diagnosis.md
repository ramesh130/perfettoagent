# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c2. The increase is concentrated in listener-related objects: ListenerSet$ListenerHolder grew from 50 to 198, SuperPlayer listener lambdas from 16 to 164, FeedRow listener objects from 4 to 152, and ListenerHolder.listener links from 50 to 198.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT
  coalesce((SELECT SUM(reachable_obj_count) FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder'), 0) AS listener_holders,
  coalesce((SELECT SUM(reachable_obj_count) FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'), 0) AS superplayer_listener_lambdas,
  coalesce((SELECT SUM(reachable_obj_count) FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name = 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1'), 0) AS feed_row_listeners,
  (SELECT count(*)
   FROM heap_graph_reference AS r
   JOIN heap_graph_object AS o ON o.reference_set_id = r.reference_set_id
   JOIN heap_graph_class AS c ON c.id = o.type_id
   WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
     AND c.name = 'androidx.media3.common.util.ListenerSet$ListenerHolder'
     AND r.field_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder.listener') AS holder_listener_links
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT
  coalesce((SELECT SUM(reachable_obj_count) FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder'), 0) AS listener_holders,
  coalesce((SELECT SUM(reachable_obj_count) FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'), 0) AS superplayer_listener_lambdas,
  coalesce((SELECT SUM(reachable_obj_count) FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name = 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1'), 0) AS feed_row_listeners,
  (SELECT count(*)
   FROM heap_graph_reference AS r
   JOIN heap_graph_object AS o ON o.reference_set_id = r.reference_set_id
   JOIN heap_graph_class AS c ON c.id = o.type_id
   WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
     AND c.name = 'androidx.media3.common.util.ListenerSet$ListenerHolder'
     AND r.field_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder.listener') AS holder_listener_links
```

### c3. In the current heap, 164 ListenerHolder.listener references retain ForwardingPlayer listener wrappers leading to $Proxy3 objects, and 152 SuperPlayer listener lambdas retain FeedRow listener objects; the corresponding baseline counts are 16 and 4.

The `baseline` trace: 14 rows.

```sql
SELECT owner_class, field_name, owned_class, references_count
FROM (
  SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, count(*) AS references_count
  FROM heap_graph_reference AS r
  JOIN heap_graph_object AS o ON o.reference_set_id = r.reference_set_id
  JOIN heap_graph_class AS c ON c.id = o.type_id
  JOIN heap_graph_object AS oo ON oo.id = r.owned_id
  JOIN heap_graph_class AS oc ON oc.id = oo.type_id
  WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  GROUP BY c.name, r.field_name, oc.name
)
WHERE (owner_class = 'androidx.media3.common.util.ListenerSet$ListenerHolder' AND field_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder.listener')
   OR (owner_class = 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AND field_name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener.listener')
   OR (owner_class = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND field_name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0.f$1')
ORDER BY owner_class, field_name, owned_class
```

The `current` trace: 14 rows.

```sql
SELECT owner_class, field_name, owned_class, references_count
FROM (
  SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, count(*) AS references_count
  FROM heap_graph_reference AS r
  JOIN heap_graph_object AS o ON o.reference_set_id = r.reference_set_id
  JOIN heap_graph_class AS c ON c.id = o.type_id
  JOIN heap_graph_object AS oo ON oo.id = r.owned_id
  JOIN heap_graph_class AS oc ON oc.id = oo.type_id
  WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  GROUP BY c.name, r.field_name, oc.name
)
WHERE (owner_class = 'androidx.media3.common.util.ListenerSet$ListenerHolder' AND field_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder.listener')
   OR (owner_class = 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AND field_name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener.listener')
   OR (owner_class = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND field_name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0.f$1')
ORDER BY owner_class, field_name, owned_class
```

### c4. Commit 6efb841e removed the resetForReuse cleanup that removed every wrapped listener from the delegate and cleared wrappedListeners; the remaining release-time cleanup does not perform that reset-time unregister.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

### c5. The listener-retention pattern in the current trace matches that removed resetForReuse cleanup, so 6efb841e is the direct culprit for the heap-growth regression.

The `baseline` trace: 14 rows.

```sql
SELECT owner_class, field_name, owned_class, references_count
FROM (
  SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, count(*) AS references_count
  FROM heap_graph_reference AS r
  JOIN heap_graph_object AS o ON o.reference_set_id = r.reference_set_id
  JOIN heap_graph_class AS c ON c.id = o.type_id
  JOIN heap_graph_object AS oo ON oo.id = r.owned_id
  JOIN heap_graph_class AS oc ON oc.id = oo.type_id
  WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  GROUP BY c.name, r.field_name, oc.name
)
WHERE (owner_class = 'androidx.media3.common.util.ListenerSet$ListenerHolder' AND field_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder.listener')
   OR (owner_class = 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AND field_name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener.listener')
   OR (owner_class = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND field_name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0.f$1')
ORDER BY owner_class, field_name, owned_class
```

The `current` trace: 14 rows.

```sql
SELECT owner_class, field_name, owned_class, references_count
FROM (
  SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, count(*) AS references_count
  FROM heap_graph_reference AS r
  JOIN heap_graph_object AS o ON o.reference_set_id = r.reference_set_id
  JOIN heap_graph_class AS c ON c.id = o.type_id
  JOIN heap_graph_object AS oo ON oo.id = r.owned_id
  JOIN heap_graph_class AS oc ON oc.id = oo.type_id
  WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  GROUP BY c.name, r.field_name, oc.name
)
WHERE (owner_class = 'androidx.media3.common.util.ListenerSet$ListenerHolder' AND field_name = 'androidx.media3.common.util.ListenerSet$ListenerHolder.listener')
   OR (owner_class = 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AND field_name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener.listener')
   OR (owner_class = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND field_name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0.f$1')
ORDER BY owner_class, field_name, owned_class
```

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

## Caveats

- Only one capture per side is available, so unrelated heap-graph variation cannot be ruled out completely.
- The selected metric is reachable-object count from the final Java heap graph; it demonstrates a memory-retention regression, not a measured frame-time or startup-time regression.
- The current capture is a non-debuggable benchmark run on an Android emulator (sdk_gphone64_arm64, SDK 36).

## Run

`gpt-5.6-luna` on openai, effort xhigh: 41 tool calls, $0.0296, 194 s.
Tokens: 27 input, 181,491 cache read, 46,612 cache write, 11,912 output.
