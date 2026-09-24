# Inconclusive

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** low (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttfd_ms` | ms | 2,077.31 | 2,282.74 | +205.43 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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

### c1. Median cold-start time to full display increased from 2077.310959 ms to 2282.739626 ms, a delta of 205.428667 ms.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH
  cold AS (
    SELECT s.package, d.time_to_full_display AS ns
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
    SELECT s.package, d.time_to_full_display AS ns
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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 100) AS value
```

### c2. The localized event is the reportFullyDrawn trace span associated with each cold start; the baseline and current traces both contain these events, but their offsets vary substantially across starts, so the pair does not identify a changed application slice or frame.

The `baseline` trace: 40 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT s.startup_id, (r.ts-s.ts)/1e6 AS report_ms, r.dur/1e6 AS report_slice_ms
FROM android_startups AS s JOIN slice AS r ON r.name LIKE 'reportFullyDrawn%'
 AND r.ts>=s.ts AND r.ts<s.ts+5000000000
WHERE s.startup_type='cold' ORDER BY s.startup_id
```

The `current` trace: 40 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT s.startup_id, (r.ts-s.ts)/1e6 AS report_ms, r.dur/1e6 AS report_slice_ms
FROM android_startups AS s JOIN slice AS r ON r.name LIKE 'reportFullyDrawn%'
 AND r.ts>=s.ts AND r.ts<s.ts+5000000000
WHERE s.startup_type='cold' ORDER BY s.startup_id
```

### c3. The range includes a change that increases MoQ position-reporting frequency from every two seconds to every one second in MoqScreen.kt, but the trace evidence does not connect that change directly to the reportFullyDrawn timing.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MoqScreen.kt`:

```text
2fa1b7e9db091ea90dc7775f5c7c20cec0ca5279
```

The `baseline` trace: 40 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT s.startup_id, (r.ts-s.ts)/1e6 AS report_ms, r.dur/1e6 AS report_slice_ms
FROM android_startups AS s JOIN slice AS r ON r.name LIKE 'reportFullyDrawn%'
 AND r.ts>=s.ts AND r.ts<s.ts+5000000000
WHERE s.startup_type='cold' ORDER BY s.startup_id
```

The `current` trace: 40 rows.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT s.startup_id, (r.ts-s.ts)/1e6 AS report_ms, r.dur/1e6 AS report_slice_ms
FROM android_startups AS s JOIN slice AS r ON r.name LIKE 'reportFullyDrawn%'
 AND r.ts>=s.ts AND r.ts<s.ts+5000000000
WHERE s.startup_type='cold' ORDER BY s.startup_id
```

## Caveats

- This comparison has one baseline capture and one current capture, so run-to-run startup and video-rendering variability cannot be separated from a code regression.
- Both traces were captured on an sdk_gphone64_arm64 emulator; TTFD includes player readiness and first-frame rendering, not only application UI work.

## Run

`gpt-5.6-luna` on openai, effort high: 78 tool calls, $0.0486, 468 s.
Tokens: 81 input, 843,233 cache read, 54,064 cache write, 15,169 output.
