# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (correlated); `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`
- **Verified:** 3 claims kept, 1 dropped; 5 of 6 citations passed
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

### c1. Reachable heap objects increased from 432751 to 434935, a delta of 2184 objects.

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

### c3. Commit 6efb841 removed the listener-removal and listener-map-clearing block from resetForReuse, which correlates with the increased retained Media3 listener objects.

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/SuperPlayer.kt`:

```text
6efb841e56d8071cddf03a32002d8413507b2797
```

### c4. The current build corresponds to the range head and was captured as a non-debuggable benchmark build on an Android emulator.

Commit:

```text
a49a1ebb1aca7a202d251d55598256bbb7992169
```

## Caveats

- The heap metric compares reachable objects in the last heap dump of each trace; it is evidence of increased retention, not a direct frame-time or latency measurement.
- The standard frame, startup, binder, GC, and main-thread-blocked metrics returned no data because the traces lack the required frame-timeline or related data sources.
- Each side has only one capture, so run-to-run variation cannot be separated from the measured heap difference.

## Dropped claims

### c2. The largest named increases include SnapshotMutableStateImpl$StateStateRecord (+290), while several Media3 listener-related classes each increased by 148, including ForwardingPlayer$ForwardingListener and ListenerSet$ListenerHolder.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 7 col 50 SELECT MAX(graph_sample_ts) FROM android.memory.heap_graph.heap_graph_class_aggregation ^ syntax error near '.'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 7 col 50 SELECT MAX(graph_sample_ts) FROM android.memory.heap_graph.heap_graph_class_aggregation ^ syntax error near '.'

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.heap_graph_class_aggregation;
SELECT 'androidx.media3.common.ForwardingPlayer$ForwardingListener' AS key, coalesce((SELECT value FROM (
SELECT type_name AS key, SUM(reachable_obj_count) AS value
FROM android_heap_graph_class_aggregation
WHERE graph_sample_ts = (
  SELECT MAX(graph_sample_ts) FROM android.memory.heap_graph.heap_graph_class_aggregation
)
GROUP BY type_name
HAVING value > 0
ORDER BY key

) WHERE key IS 'androidx.media3.common.ForwardingPlayer$ForwardingListener'), 0) AS value
```

## Run

`gpt-5.6-luna` on openai, effort low: 17 tool calls, $0.0103, 100 s.
Tokens: 15 input, 36,042 cache read, 29,793 cache write, 1,775 output.
