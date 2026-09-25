# Inconclusive

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 4 claims kept, 0 dropped; 6 of 6 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 839.5 | 854.85 | +15.35 |

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

### c1. The median cold-start time to initial display increased from 839.504417 ms in the baseline to 854.851167 ms in the current trace, a 15.346750 ms increase.

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

The `current` trace: 1 row.

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

### c2. Each trace contains 20 cold starts, and the individual TTID values vary substantially within each capture, so this pair does not establish that the increase exceeds run-to-run noise.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, d.time_to_initial_display / 1e6 AS ttid_ms, s.ts / 1e6 AS start_ms
FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id)
WHERE s.startup_type='cold' AND d.time_to_initial_display IS NOT NULL
ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, d.time_to_initial_display / 1e6 AS ttid_ms, s.ts / 1e6 AS start_ms
FROM android_startups s JOIN android_startup_time_to_display d USING (startup_id)
WHERE s.startup_type='cold' AND d.time_to_initial_display IS NOT NULL
ORDER BY s.ts
```

### c3. The range contains a UI-size change that reduces Interests-row thumbnails from 56 dp to 48 dp; blame attributes that line to commit cd4f22cbbddcc8efac9413ac2678b06e321492aa.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

### c4. The range also contains a widget refresh-period resource change, from one hour to 30 minutes, which is not a demonstrated cause of cold-start TTID in these traces.

Commit, changing `app/src/main/res/values/integers.xml`:

```text
432218a1e58c49007d18fae8bd3d76fa40b57272
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- Only one baseline capture and one current capture are available.
- The traces were recorded on an Android emulator and the current build is debuggable.
- Other frame metrics improved: frame p95, frame p99, UI-time p95, and jank percentage all decreased, so the TTID increase is not a consistent UI-performance regression across the available metrics.

## Run

`gpt-5.6-luna` on openai, effort medium: 40 tool calls, $0.0135, 223 s.
Tokens: 24 input, 79,222 cache read, 20,831 cache write, 5,562 output.
