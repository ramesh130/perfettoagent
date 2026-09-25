# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 4 claims kept, 0 dropped; 8 of 8 citations passed
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

### c2. The increase is localized to listener and feed-related objects: ForwardingPlayer listeners rose from 17 to 165, ListenerSet holders from 50 to 198, the FeedRow lambda from 4 to 152, and the SuperPlayer lambda from 16 to 164; Compose state records also rose from 345 to 635.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.media3.common.ForwardingPlayer$ForwardingListener',
    'androidx.media3.common.util.ListenerSet$ListenerHolder',
    'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1',
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'
  )
GROUP BY type_name
ORDER BY type_name
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.media3.common.ForwardingPlayer$ForwardingListener',
    'androidx.media3.common.util.ListenerSet$ListenerHolder',
    'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1',
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'
  )
GROUP BY type_name
ORDER BY type_name
```

### c3. Commit 6efb841e56d8071cddf03a32002d8413507b2797 removed the listener cleanup from SuperPlayer.resetForReuse: the deleted block removed every wrapped listener from the delegate and then cleared the wrapped-listener map.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

### c4. The matching growth of ForwardingPlayer listeners, ListenerSet holders, and FeedRow objects makes commit 6efb841e56d8071cddf03a32002d8413507b2797 the likely cause of the heap regression.

The `baseline` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.media3.common.ForwardingPlayer$ForwardingListener',
    'androidx.media3.common.util.ListenerSet$ListenerHolder',
    'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1',
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'
  )
GROUP BY type_name
ORDER BY type_name
```

The `current` trace: 5 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS reachable_objects
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation)
  AND type_name IN (
    'androidx.media3.common.ForwardingPlayer$ForwardingListener',
    'androidx.media3.common.util.ListenerSet$ListenerHolder',
    'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1',
    'androidx.compose.runtime.SnapshotMutableStateImpl$StateStateRecord',
    'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'
  )
GROUP BY type_name
ORDER BY type_name
```

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

## Caveats

- This conclusion uses one heap-dump capture per side; reachable-object counts can have run-to-run variation.
- The captures did not provide usable frame-timeline, startup, GC, or binder metrics, so this establishes a heap-retention regression rather than a measured UI-latency regression.
- The heap metric counts reachable objects, not retained bytes.

## Run

`gpt-5.6-luna` on openai, effort xhigh: 54 tool calls, $0.0290, 241 s.
Tokens: 36 input, 258,689 cache read, 42,082 cache write, 11,116 output.
