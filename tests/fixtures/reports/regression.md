# Regression

- **Metric:** `heap_growth_objects_by_class` +2,184 objects (432,751 → 434,935 objects)
- **Culprit:** `6efb841e56d8` (direct); `app/src/main/java/com/example/Feed.kt`
- **Verified:** 2 claims kept, 1 dropped; 5 of 6 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `heap_growth_objects_by_class` | objects | 432,751 | 434,935 | +2,184 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.memory.heap_graph.class_aggregation;
SELECT SUM(obj_count) AS objects FROM android_heap_graph_class_aggregation
```

## Claims

### c0. Reachable FeedListener objects grew from 12 to 2,196.

The `current` trace: 1 row.

```sql
SELECT name, obj_count FROM android_heap_graph_class_aggregation WHERE name LIKE '%FeedListener%'
```

The `baseline` trace: 1 row.

```sql
SELECT name, obj_count FROM android_heap_graph_class_aggregation WHERE name LIKE '%FeedListener%'
```

### c1. The commit registers a listener on every bind and never removes it.

Commit, changing `app/src/main/java/com/example/Feed.kt`:

```text
6efb841e56d8a1b2c3d4e5f60718293a4b5c6d7e
```

## Caveats

- One capture per side, on an emulator.

## Dropped claims

### c2. A second commit also leaks.

Dropped: citation 1: 6efb841e2797 names no commit in the repo (or is ambiguous)

Commit: Failed: 6efb841e2797 names no commit in the repo (or is ambiguous)

```text
6efb841e2797
```

## Run

`gpt-5.6-luna` on openai, effort high: 40 tool calls, $0.0231, 136 s.
Tokens: 33 input, 221,104 cache read, 44,528 cache write, 8,663 output.
