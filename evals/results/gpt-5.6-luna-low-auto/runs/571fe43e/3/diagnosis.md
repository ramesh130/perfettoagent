# No regression

- **Metric:** `startup_ttfd_ms` +205.43 ms (2,077.31 → 2,282.74 ms)
- **Culprit:** none attributed
- **Verified:** 3 claims kept, 0 dropped; 7 of 7 citations passed
- **Model's confidence:** high (never scored)

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

### c1. Median cold-start time to full display is higher in the current trace than the baseline trace.

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
SELECT (SELECT ns / 1e6 FROM ranked WHERE rank = (n + 1) / 2) AS value
```

### c2. The only commit in the range that touches the localized feed playback code renames a Handler field and its corresponding use; it does not change the Handler construction, posting behavior, or startup logic.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
3c45fa773a148f0cd3f45cdf56318eb3dc52e6c0
```

### c3. The observed startup difference is therefore not attributable to a behavior-changing commit in the supplied range.

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
3c45fa773a148f0cd3f45cdf56318eb3dc52e6c0
```

Commit, changing `superplayer-core/src/main/kotlin/com/superplayer/core/PlayerPool.kt`:

```text
c3ebbc6614f42e471394eac1e0a91c52aa59d429
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/MainActivity.kt`:

```text
3a78df0448d62ccd759276ff8bb3b8739be06e46
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`:

```text
912961f6d42eaabec8c0da030a6ed44db2414d2d
```

## Caveats

- Each side is a single capture, so the startup delta may include run-to-run variability.
- The traces were captured on an Android emulator (sdk_gphone64_arm64, SDK 36).
- The current build is a non-debuggable benchmark build; baseline build metadata was not available.

## Run

`gpt-5.6-luna` on openai, effort low: 15 tool calls, $0.0121, 86 s.
Tokens: 15 input, 55,244 cache read, 33,908 cache write, 2,100 output.
