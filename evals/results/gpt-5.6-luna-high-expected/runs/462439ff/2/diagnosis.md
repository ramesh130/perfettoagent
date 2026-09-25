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

### c1. The current trace has 434935 reachable Java objects versus 432751 in the baseline, an increase of 2184 objects.

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

### c2. The increase is localized in pooled-player and feed-row-related objects: ForwardingPlayer$ForwardingListener grows from 17 to 165, ListenerSet$ListenerHolder from 50 to 198, and the FeedRow closure class from 4 to 152.

The `baseline` trace: 3 rows.

```sql
SELECT c.name AS type_name, COUNT(*) AS object_count, MIN(o.root_distance) AS min_root_distance, MAX(o.root_distance) AS max_root_distance
FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id
WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  AND o.reachable = 1
  AND c.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')
GROUP BY c.name ORDER BY c.name
```

The `current` trace: 3 rows.

```sql
SELECT c.name AS type_name, COUNT(*) AS object_count, MIN(o.root_distance) AS min_root_distance, MAX(o.root_distance) AS max_root_distance
FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id
WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  AND o.reachable = 1
  AND c.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')
GROUP BY c.name ORDER BY c.name
```

### c3. In the current heap graph, ForwardingPlayer$ForwardingListener objects are retained through ListenerHolder.listener references and object-array references, matching accumulation of listener registrations rather than a broad class-wide increase.

The `current` trace: 3 rows.

```sql
SELECT c.name AS owner_type, r.field_name, r.deobfuscated_field_name, COUNT(*) AS refs
FROM heap_graph_reference r
JOIN heap_graph_object o ON o.id = r.owner_id
JOIN heap_graph_class c ON c.id = o.type_id
WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  AND r.owned_id IN (SELECT o2.id FROM heap_graph_object o2 JOIN heap_graph_class c2 ON c2.id = o2.type_id WHERE o2.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object) AND c2.name = 'androidx.media3.common.ForwardingPlayer$ForwardingListener')
GROUP BY c.name, r.field_name, r.deobfuscated_field_name ORDER BY refs DESC LIMIT 20
```

### c4. Commit 6efb841e56d8071cddf03a32002d8413507b2797 removed the wrapped-listener removal and clear operations from SuperPlayer.resetForReuse; that change directly explains why recycled feed players can retain prior listeners and their feed-row closures.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

The `baseline` trace: 3 rows.

```sql
SELECT c.name AS type_name, COUNT(*) AS object_count, MIN(o.root_distance) AS min_root_distance, MAX(o.root_distance) AS max_root_distance
FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id
WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  AND o.reachable = 1
  AND c.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')
GROUP BY c.name ORDER BY c.name
```

The `current` trace: 3 rows.

```sql
SELECT c.name AS type_name, COUNT(*) AS object_count, MIN(o.root_distance) AS min_root_distance, MAX(o.root_distance) AS max_root_distance
FROM heap_graph_object o JOIN heap_graph_class c ON c.id = o.type_id
WHERE o.graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM heap_graph_object)
  AND o.reachable = 1
  AND c.name IN ('androidx.media3.common.ForwardingPlayer$ForwardingListener','androidx.media3.common.util.ListenerSet$ListenerHolder','com.superplayer.demo.FeedScreenKt$FeedRow$1$1$1$1')
GROUP BY c.name ORDER BY c.name
```

## Caveats

- Only one capture per side is available, so ordinary run-to-run heap-dump noise cannot be quantified.
- The metric counts objects reachable in the final Java heap dump; it establishes retention in these captures but does not by itself prove how long the objects would remain reachable after a later lifecycle event or garbage collection.

## Run

`gpt-5.6-luna` on openai, effort high: 37 tool calls, $0.0248, 111 s.
Tokens: 27 input, 211,294 cache read, 45,116 cache write, 7,745 output.
