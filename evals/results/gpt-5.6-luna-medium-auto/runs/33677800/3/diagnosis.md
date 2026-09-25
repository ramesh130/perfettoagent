# No regression

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 6 of 6 citations passed
- **Current build:** debuggable; see Caveats
- **Model's confidence:** medium (never scored)

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

### c1. Median cold-start time to initial display increased from 839.504417 ms in the baseline to 854.851167 ms in the current trace, a delta of 15.346750000000043 ms.

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
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1) AND ns IS NOT NULL
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
    SELECT package FROM cold GROUP BY count(*) ORDER BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM cold GROUP BY package ORDER BY count(*) DESC, package LIMIT 1) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

### c2. Each trace contains 20 cold starts for com.example.jetnews; the baseline TTID values include 839.504417 ms at the median, while the current values include 854.851167 ms at the median.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display, d.time_to_full_display FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id) ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id, s.package, s.startup_type, s.ts, s.dur, d.time_to_initial_display, d.time_to_full_display FROM android_startups AS s JOIN android_startup_time_to_display AS d USING (startup_id) ORDER BY s.ts
```

### c3. The range's endpoint commit changes only the drawer gesture comment in JetnewsApp.kt; the traced startup metric does not provide a direct code-level link to that change.

Commit, changing `app/src/main/java/com/example/jetnews/ui/JetnewsApp.kt`:

```text
bb767eec9f98c0e9493140735e2e477828fcb9b1
```

The `current` trace: 40 rows.

```sql
SELECT s.name, COUNT(*) AS n, SUM(s.dur)/1e6 AS total_ms, MAX(s.dur)/1e6 AS max_ms FROM slice s JOIN thread_track tt ON s.track_id=tt.id JOIN thread t ON tt.utid=t.utid JOIN process p ON t.upid=p.upid WHERE p.name='com.example.jetnews' GROUP BY s.name ORDER BY total_ms DESC LIMIT 40
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one baseline capture and one current capture, so the 15.35 ms TTID increase may be run-to-run noise rather than a regression caused by the commit range.
- The current trace was captured on an emulator (sdk_gphone64_arm64, SDK 36) using a debuggable build.

## Run

`gpt-5.6-luna` on openai, effort medium: 23 tool calls, $0.0109, 126 s.
Tokens: 21 input, 65,032 cache read, 19,604 cache write, 3,877 output.
