# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
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

### c1. The last Java heap dump holds 432751 reachable objects in the baseline and 434935 in the current trace, 2184 more.

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

### c2. Listener-wrapper classes grow by the same count, which points to a leak. androidx.media3.common.ForwardingPlayer$ForwardingListener goes from 17 to 165. $Proxy3 goes from 16 to 164. SuperPlayerKt's lambda goes from 16 to 164. The demo feed's FeedScreenKt$FeedRow$1$1$1$1 listener goes from 4 to 152. Each class gains 148 objects.

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'androidx.media3.common.ForwardingPlayer$ForwardingListener'), 0) AS value
```

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'androidx.media3.common.ForwardingPlayer$ForwardingListener'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT '$Proxy3' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS '$Proxy3'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'com.superplayer.core.SuperPlayerKt$$ExternalSyntheticLambda0'), 0) AS value
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1'), 0) AS value
```

### c3. Commit 6efb841 ('Trim resetForReuse') deletes the block in SuperPlayer.resetForReuse that removed every wrapped listener from the delegate and cleared wrappedListeners. After it, a pooled player keeps each listener wrapper, and the feed-row listener it holds, attached across every reuse. SuperPlayer.addListener wraps each listener with reportingSourceAs, which returns a Proxy.newProxyInstance wrapper. That matches the growth in $Proxy3 and in the SuperPlayerKt lambda.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

### c4. The other commits in the range touch comments, names, test-kit files or gradle.properties. None of their subjects suggests a change to how listeners are kept.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
04beebdcfc014c9fab76c29a49d3ca876648ce6d
```

Commit, changing `gradle.properties`:

```text
b9bddca8037da62758505129fdbe9458be24e5c5
```

## Caveats

- There is one capture per side, on an emulator (sdk_gphone64_arm64, SDK 36). The headline delta is small, about 0.5% of reachable objects. The evidence rests on the matching +148 growth in the listener-wrapper classes rather than on the total.
- The current build is from a49a1eb and is not debuggable (benchmark build type). The baseline trace's build is not recorded.
- git_blame cannot show deleted lines. The attribution rests on 6efb841's diff, which removed the listener cleanup from resetForReuse. At the head, lines 523-555 of resetForReuse no longer mention wrappedListeners.
- I did not read the diffs of the other SuperPlayer.kt commits (a49a1eb, cc662f9, befc18d, 04beebd, 7db8614, 0b24d41). Ruling them out rests on their commit subjects.

## Run

`claude-opus-5-5` on anthropic, effort high: 8 tool calls, $0.5481, 96 s.
Tokens: 105,431 input, 29,230 cache read, 5,846 cache write, 4,565 output.
