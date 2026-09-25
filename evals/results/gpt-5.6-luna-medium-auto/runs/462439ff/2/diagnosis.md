# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 3 claims kept, 1 dropped; 6 of 7 citations passed
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

### c1. Reachable heap objects increased by 2184, from 432751 in the baseline to 434935 in the current trace.

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

### c2. The growth is concentrated in listener-related objects: ForwardingPlayer listeners rose from 17 to 165, ListenerSet holders from 50 to 198, SuperPlayer listener lambdas from 16 to 164, and FeedRow listener objects from 4 to 152.

The `baseline` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY type_name ORDER BY type_name
```

The `current` trace: 4 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND type_name IN ('androidx.media3.common.util.ListenerSet$ListenerHolder','androidx.media3.common.ForwardingPlayer$ForwardingListener','com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1') GROUP BY type_name ORDER BY type_name
```

### c3. Commit 6efb841 removed the resetForReuse loop that removed wrapped listeners from the delegate before clearing the wrapper map.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

## Caveats

- This diagnosis uses one capture per side; heap growth can contain run-to-run variation, although the listener-specific increase matches the changed cleanup code.
- The traces were captured on an Android SDK 36 emulator, and the metric measures reachable object counts rather than retained bytes or a confirmed GC leak path.
- Frame, startup, binder, and scheduler metrics had no data in these captures, so this diagnosis is specifically a memory/heap regression rather than a demonstrated frame-time regression.

## Dropped claims

### c4. The removed listener cleanup was introduced by the commit identified as the culprit; blame at the range head attributes the surrounding resetForReuse implementation to the initial import, while the deleted cleanup is the specific change in 6efb841.

Dropped: citation 2: ccdf1f9446d2a45d8e6dc396601f528951434322 is not inside the range

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`: Failed: ccdf1f9446d2a45d8e6dc396601f528951434322 is not inside the range

```text
ccdf1f9446d2a45d8e6dc396601f528951434322
```

## Run

`gpt-5.6-luna` on openai, effort medium: 32 tool calls, $0.0146, 140 s.
Tokens: 24 input, 116,737 cache read, 31,803 cache write, 3,580 output.
