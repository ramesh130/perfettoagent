# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 5 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. Reachable Java objects increased from 432751 in the baseline heap dump to 434935 in the current dump, a delta of 2184 objects.

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

### c2. The increase includes substantial growth in listener-related and feed-row objects: ListenerSet$ListenerHolder grew from 50 to 198, ForwardingPlayer$ForwardingListener from 17 to 165, the SuperPlayer synthetic listener lambda from 16 to 164, and the FeedRow closure from 4 to 152.

The `baseline` trace: 5 rows.

```sql
WITH target AS (SELECT id, name FROM heap_graph_class WHERE name IN ('com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener')) SELECT c.name, c.id AS type_id, COUNT(o.id) AS objects, SUM(CASE WHEN o.reachable = 1 THEN 1 ELSE 0 END) AS reachable, MIN(o.root_distance) AS min_root_distance, COUNT(DISTINCT o.root_type) AS root_types FROM target c LEFT JOIN heap_graph_object o ON o.type_id = c.id AND o.graph_sample_ts = (SELECT MAX(ts) FROM heap_graph) GROUP BY c.name, c.id ORDER BY reachable DESC
```

The `current` trace: 5 rows.

```sql
WITH target AS (SELECT id, name FROM heap_graph_class WHERE name IN ('com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord','androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener')) SELECT c.name, c.id AS type_id, COUNT(o.id) AS objects, SUM(CASE WHEN o.reachable = 1 THEN 1 ELSE 0 END) AS reachable, MIN(o.root_distance) AS min_root_distance, COUNT(DISTINCT o.root_type) AS root_types FROM target c LEFT JOIN heap_graph_object o ON o.type_id = c.id AND o.graph_sample_ts = (SELECT MAX(ts) FROM heap_graph) GROUP BY c.name, c.id ORDER BY reachable DESC
```

### c3. In the current heap, 152 FeedRow closures are retained through the synthetic lambda's f$1 field; those lambda objects are retained by $Proxy3 Proxy.h fields, and the proxies are retained by ForwardingPlayer listener fields.

The `current` trace: 2 rows.

```sql
WITH target AS (SELECT o.id FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id WHERE c.name = 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1' AND o.graph_sample_ts = (SELECT MAX(ts) FROM heap_graph)) SELECT oc.name AS owner_class, r.field_name, COUNT(*) AS refs FROM heap_graph_reference r JOIN target t ON t.id = r.owned_id JOIN heap_graph_object oo ON oo.id = r.owner_id JOIN heap_graph_class oc ON oc.id = oo.type_id GROUP BY oc.name, r.field_name ORDER BY refs DESC LIMIT 20
```

The `current` trace: 1 row.

```sql
WITH target AS (SELECT o.id FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id WHERE c.name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND o.graph_sample_ts = (SELECT MAX(ts) FROM heap_graph)) SELECT oc.name AS owner_class, r.field_name, COUNT(*) AS refs FROM heap_graph_reference r JOIN target t ON t.id = r.owned_id JOIN heap_graph_object oo ON oo.id = r.owner_id JOIN heap_graph_class oc ON oc.id = oo.type_id GROUP BY oc.name, r.field_name ORDER BY refs DESC LIMIT 20
```

The `current` trace: 2 rows.

```sql
WITH target AS (SELECT o.id FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id WHERE c.name = '$Proxy3' AND o.graph_sample_ts = (SELECT MAX(ts) FROM heap_graph)) SELECT oc.name AS owner_class, r.field_name, COUNT(*) AS refs FROM heap_graph_reference r JOIN target t ON t.id = r.owned_id JOIN heap_graph_object oo ON oo.id = r.owner_id JOIN heap_graph_class oc ON oc.id = oo.type_id GROUP BY oc.name, r.field_name ORDER BY refs DESC LIMIT 20
```

### c4. Commit 6efb841e56d8071cddf03a32002d8413507b2797 removed the resetForReuse cleanup that removed every wrapped listener from the delegate and cleared wrappedListeners.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

### c5. The removed listener cleanup matches the current retained-object path: pooled player listeners retain proxy wrappers, synthetic lambdas, and FeedRow closures, identifying 6efb841e56d8071cddf03a32002d8413507b2797 as the regression culprit.

The `current` trace: 2 rows.

```sql
WITH target AS (SELECT o.id FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id WHERE c.name = 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1' AND o.graph_sample_ts = (SELECT MAX(ts) FROM heap_graph)) SELECT oc.name AS owner_class, r.field_name, COUNT(*) AS refs FROM heap_graph_reference r JOIN target t ON t.id = r.owned_id JOIN heap_graph_object oo ON oo.id = r.owner_id JOIN heap_graph_class oc ON oc.id = oo.type_id GROUP BY oc.name, r.field_name ORDER BY refs DESC LIMIT 20
```

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

## Caveats

- This diagnosis compares one capture per side; small heap deltas can be affected by run-to-run variation. The listener-wrapper and FeedRow retention pattern, together with the cleanup removal, makes this delta stronger than a small undifferentiated count change.

## Run

`gpt-5.6-luna` on openai, effort high: 43 tool calls, $0.0308, 142 s.
Tokens: 57 input, 416,297 cache read, 38,881 cache write, 10,630 output.
