# Inconclusive

- **Metric:** `startup_ttid_ms` +15.35 ms (839.5 → 854.85 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 1 dropped; 10 of 11 citations passed
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

### c2. Both traces contain 20 cold starts of com.example.jetnews, so the comparison is based on repeated starts within one capture on each side rather than one launch.

The `baseline` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id,s.ts,s.package,s.startup_type,d.time_to_initial_display/1e6 AS ttid_ms,d.time_to_full_display/1e6 AS ttfd_ms
FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
WHERE s.package='com.example.jetnews'
ORDER BY s.ts
```

The `current` trace: 20 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
SELECT s.startup_id,s.ts,s.package,s.startup_type,d.time_to_initial_display/1e6 AS ttid_ms,d.time_to_full_display/1e6 AS ttfd_ms
FROM android_startups s JOIN android_startup_time_to_display d USING(startup_id)
WHERE s.package='com.example.jetnews'
ORDER BY s.ts
```

### c3. The startup-localized app slices do not show an added Compose or traversal cost in the current trace: aggregate Compose:recompose time changed from 4139.547971 ms to 3946.720670 ms, while traversal changed from 21554.905179 ms to 21221.554804 ms.

The `baseline` trace: 100 rows.

```sql
SELECT s.name,count(*) AS occurrences,sum(s.dur)/1e6 AS total_ms,max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews'
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

The `current` trace: 100 rows.

```sql
SELECT s.name,count(*) AS occurrences,sum(s.dur)/1e6 AS total_ms,max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews'
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

### c4. The range contains runtime-relevant UI changes to the Interests screen and a widget refresh interval, but the traces do not provide a direct link from those changes to the TTID increase.

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/SelectTopicButton.kt`:

```text
3e2fdaf2216b048731671bb61bd0fe7d2f2372a8
```

Commit, changing `app/src/main/java/com/example/jetnews/ui/interests/InterestsScreen.kt`:

```text
cd4f22cbbddcc8efac9413ac2678b06e321492aa
```

Commit, changing `app/src/main/res/values/integers.xml`:

```text
432218a1e58c49007d18fae8bd3d76fa40b57272
```

The `baseline` trace: 100 rows.

```sql
SELECT s.name,count(*) AS occurrences,sum(s.dur)/1e6 AS total_ms,max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews'
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

The `current` trace: 100 rows.

```sql
SELECT s.name,count(*) AS occurrences,sum(s.dur)/1e6 AS total_ms,max(s.dur)/1e6 AS max_ms
FROM slice s JOIN thread_track tt ON tt.id=s.track_id JOIN thread t ON t.utid=tt.utid JOIN process p ON p.upid=t.upid
WHERE p.name='com.example.jetnews'
GROUP BY s.name ORDER BY total_ms DESC LIMIT 100
```

## Caveats

- the current trace's build was debuggable (run metadata: debuggable), so ART ran it with fewer optimisations and its timings overstate a release build's
- This is one baseline/current capture pair, so the 15.346750 ms shift may be capture noise; repeated independent captures are needed to establish significance.
- The run metadata identifies a debuggable build on the sdk_gphone64_arm64 emulator, which can add startup variability.

## Dropped claims

### c1. The selected app-specific cold-start metric increased from 839.504417 ms to 854.851167 ms, a delta of 15.346750 ms.

Dropped: citation 2: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 48 SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1 ^ syntax error near 'DESC'

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

The `current` trace: Failed: did not run: trace processor failed: Traceback (most recent call last): File "stdin" line 12 col 48 SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1 ^ syntax error near 'DESC'

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
    SELECT package FROM cold GROUP BY count(*) DESC, package LIMIT 1
  ),
  ranked AS (
    SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
    FROM cold
    WHERE package = (SELECT package FROM app) AND ns IS NOT NULL
  )
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

## Run

`gpt-5.6-luna` on openai, effort high: 69 tool calls, $0.0497, 339 s.
Tokens: 48 input, 603,994 cache read, 79,466 cache write, 14,780 output.
