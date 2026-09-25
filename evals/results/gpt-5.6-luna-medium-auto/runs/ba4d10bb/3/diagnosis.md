# Regression

- **Metric:** `startup_ttid_ms` +756.93 ms (839.5 → 1,596.43 ms)
- **Culprit:** `bea44a9561ce` (correlated); `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`
- **Verified:** 3 claims kept, 1 dropped; 5 of 6 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 839.5 | 1,596.43 | +756.93 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Claims

### c2. The regression is concentrated in application binding: the traces contain 20 bindApplication slices each, with average duration increasing from 361.7080627 ms to 1138.5053027 ms and maximum duration increasing from 428.984792 ms to 1506.993584 ms.

The `baseline` trace: 1 row.

```sql
SELECT count(*) AS bind_application_count,
       avg(dur) / 1e6 AS avg_bind_application_ms,
       max(dur) / 1e6 AS max_bind_application_ms
FROM slice
WHERE name = 'bindApplication';
```

The `current` trace: 1 row.

```sql
SELECT count(*) AS bind_application_count,
       avg(dur) / 1e6 AS avg_bind_application_ms,
       max(dur) / 1e6 AS max_bind_application_ms
FROM slice
WHERE name = 'bindApplication';
```

### c3. Commit bea44a9561ce48b23fc6102f729f1c78d49b2af5 adds verifyArticleCache() to JetnewsApplication.onCreate(), including a 768 MiB cache-file check/rebuild and a full CRC32 read, which is consistent with the increased bindApplication and startup duration.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

### c4. The added launch-time verification lines are attributed by blame to bea44a9561ce48b23fc6102f729f1c78d49b2af5.

Commit, changing `app/src/main/java/com/example/jetnews/JetnewsApplication.kt`:

```text
bea44a9561ce48b23fc6102f729f1c78d49b2af5
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This compares one baseline capture with one current capture, although each capture contains 20 cold starts.
- Both captures were made on an Android emulator using a debuggable build.
- The trace exposes the framework bindApplication span rather than a direct trace slice for verifyArticleCache(), so the culprit attribution is correlated rather than direct.

## Dropped claims

### c1. Median cold-start time to initial display increased from 839.504417 ms to 1596.432376 ms, a regression of 756.927959 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 22 col 1 SELECT json_group_array(name) AS __perfettoagent_columns FROM pragma_table_info('__perfettoagent_query') ^ aggregate functions are not allowed in the GROUP BY clause

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_initial_display AS ns
    FROM android_startups AS s
    JOIN android_startup_time_to_display AS d USING (startup_id)
    WHERE s.startup_type = 'cold'
  ),
  app AS (
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Run

`gpt-5.6-luna` on openai, effort medium: 33 tool calls, $0.0152, 496 s.
Tokens: 24 input, 117,581 cache read, 29,932 cache write, 4,493 output.
