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

### c2. The current heap graph has 152 FeedRow listener objects versus 4 in the baseline, 164 SuperPlayer listener-wrapper lambdas versus 16, 165 ForwardingPlayer listeners versus 17, and 198 ListenerHolder objects versus 50.

The `baseline` trace: 5 rows.

```sql
SELECT c.name, count(*) AS objects, sum(o.reachable) AS reachable FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name IN ('com.superplayer.core.SuperPlayer','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder') GROUP BY c.name ORDER BY c.name
```

The `current` trace: 5 rows.

```sql
SELECT c.name, count(*) AS objects, sum(o.reachable) AS reachable FROM heap_graph_object AS o JOIN heap_graph_class AS c ON c.id = o.type_id WHERE o.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND c.name IN ('com.superplayer.core.SuperPlayer','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder') GROUP BY c.name ORDER BY c.name
```

### c3. The current graph records 164 ListenerHolder references to ForwardingPlayer listeners and 152 wrapper-lambda references to FeedRow objects, compared with 16 and 4 respectively in the baseline.

The `baseline` trace: 2 rows.

```sql
SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, count(*) AS refs FROM heap_graph_reference AS r JOIN heap_graph_object AS oo ON oo.id = r.owner_id JOIN heap_graph_class AS c ON c.id = oo.type_id JOIN heap_graph_object AS od ON od.id = r.owned_id JOIN heap_graph_class AS oc ON oc.id = od.type_id WHERE oo.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND ((c.name = 'androidx.media3.common.util.ListenerSet$ListenerHolder' AND oc.name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener') OR (c.name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND oc.name = 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')) GROUP BY c.name, r.field_name, oc.name ORDER BY c.name
```

The `current` trace: 2 rows.

```sql
SELECT c.name AS owner_class, r.field_name, oc.name AS owned_class, count(*) AS refs FROM heap_graph_reference AS r JOIN heap_graph_object AS oo ON oo.id = r.owner_id JOIN heap_graph_class AS c ON c.id = oo.type_id JOIN heap_graph_object AS od ON od.id = r.owned_id JOIN heap_graph_class AS oc ON oc.id = od.type_id WHERE oo.graph_sample_ts = (SELECT max(graph_sample_ts) FROM heap_graph_object) AND ((c.name = 'androidx.media3.common.util.ListenerSet$ListenerHolder' AND oc.name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener') OR (c.name = 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AND oc.name = 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')) GROUP BY c.name, r.field_name, oc.name ORDER BY c.name
```

### c4. Commit 6efb841 removed the listener-removal block from SuperPlayer.resetForReuse, making it the direct range change corresponding to the increased retained Media3 listener and FeedRow object population.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

## Caveats

- This diagnosis uses one capture per side; the heap metric is a point-in-time reachable-object count rather than a repeated measurement or a direct byte measurement.

## Run

`gpt-5.6-luna` on openai, effort high: 41 tool calls, $0.0238, 489 s.
Tokens: 36 input, 245,466 cache read, 38,448 cache write, 7,725 output.
