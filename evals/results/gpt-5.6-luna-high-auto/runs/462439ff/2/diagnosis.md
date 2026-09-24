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

### c1. Reachable Java objects increased from 432751 in baseline to 434935 in current, a growth of 2184 objects.

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

### c2. The object growth is concentrated in a listener-related chain: $Proxy3 grew from 16 to 164, ForwardingPlayer listeners from 17 to 165, ListenerHolder objects from 50 to 198, and the SuperPlayer and FeedRow listener-related lambda classes also grew by 148 each.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','$Proxy3')
GROUP BY type_name
ORDER BY type_name
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','$Proxy3')
GROUP BY type_name
ORDER BY type_name
```

### c3. Commit 6efb841e56d8071cddf03a32002d8413507b2797 removed the resetForReuse cleanup that removed every wrapped listener from the delegate and cleared wrappedListeners.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

### c4. The removed listener cleanup directly matches the current-trace growth of proxy, listener-holder, forwarding-listener, and feed-row listener objects, so this commit is the direct attribution for the heap-growth regression.

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1','$Proxy3')
GROUP BY type_name
ORDER BY type_name
```

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

## Caveats

- Only one capture per side is available, so run-to-run heap variability is not measured.
- The selected metric compares reachable objects from the last recorded Java heap-graph sample in each trace; it does not measure retained bytes or prove the full retention path.

## Run

`gpt-5.6-luna` on openai, effort high: 38 tool calls, $0.0192, 154 s.
Tokens: 27 input, 168,218 cache read, 35,595 cache write, 5,779 output.
