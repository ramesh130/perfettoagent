# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** none attributed; the verifier dropped the model's: no surviving claim cites the culprit commit 6efb841e56d8071cddf03a32002d8413507b2797
- **Verified:** 2 claims kept, 1 dropped; 5 of 6 citations passed
- **Model's confidence:** none; the verifier changed what it was given for

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

### c1. Reachable Java objects increased from 432751 to 434935, a growth of 2184 objects.

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

### c2. The growth is concentrated in listener and wrapper-related objects: ListenerHolder increased from 50 to 198, ForwardingPlayer$ForwardingListener from 17 to 165, SuperPlayerKt$$ExternalSyntheticLambda0 from 16 to 164, and Compose SnapshotMutableState records from 345 to 635.

The `baseline` trace: 1,441 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND (type_name GLOB '*Feed*' OR type_name GLOB '*SuperPlayer*' OR type_name GLOB '*SnapshotMutableState*' OR type_name GLOB '*Listener*' OR type_name GLOB '*FlagSet*') GROUP BY type_name ORDER BY objects DESC
```

The `current` trace: 1,439 rows.

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT type_name, SUM(reachable_obj_count) AS objects FROM android_heap_graph_class_aggregation WHERE graph_sample_ts = (SELECT MAX(graph_sample_ts) FROM android_heap_graph_class_aggregation) AND (type_name GLOB '*Feed*' OR type_name GLOB '*SuperPlayer*' OR type_name GLOB '*SnapshotMutableState*' OR type_name GLOB '*Listener*' OR type_name GLOB '*FlagSet*') GROUP BY type_name ORDER BY objects DESC
```

## Caveats

- This conclusion is based on one heap graph capture per side; reachable-object counts can vary with scenario timing.
- The current run is a non-debuggable benchmark build on an Android emulator (sdk_gphone64_arm64, SDK 36).
- Heap growth establishes increased retained reachable objects, but does not independently prove process lifetime or user-visible memory pressure.

## Dropped claims

### c3. Commit 6efb841e56d8071cddf03a32002d8413507b2797 removed the wrapped-listener cleanup from SuperPlayer.resetForReuse, while the same file still uses wrapped listener objects for delegate registration; this directly matches the current listener-wrapper growth.

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

`gpt-5.6-luna` on openai, effort medium: 27 tool calls, $0.0137, 123 s.
Tokens: 24 input, 104,501 cache read, 31,078 cache write, 3,188 output.
