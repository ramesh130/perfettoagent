# Regression

- **Metric:** `startup_ttid_ms` +315.2 ms (349.68 → 664.88 ms)
- **Culprit:** `fb30a9c67862` (direct); `demo/src/main/AndroidManifest.xml`, `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`
- **Verified:** 4 claims kept, 0 dropped; 10 of 10 citations passed
- **Model's confidence:** high (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 349.68 | 664.88 | +315.2 |

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

### c1. Cold-start median TTID increased from 349.682708 ms in the baseline to 664.881333 ms in the current trace, a 315.198625 ms regression.

The `baseline` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.superplayer.demo' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold
)
SELECT ns / 1e6 AS median_ttid_ms FROM ranked WHERE rank = (n + 1) / 2
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.superplayer.demo' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold
)
SELECT ns / 1e6 AS median_ttid_ms FROM ranked WHERE rank = (n + 1) / 2
```

### c2. The regression localizes to the app's main-thread bindApplication work: its median duration rose from 97.692292 ms in the baseline to 465.286959 ms in the current trace.

The `baseline` trace: 1 row.

```sql
WITH ranked AS (
  SELECT s.dur / 1e6 AS bind_ms,
         row_number() OVER (ORDER BY s.dur) AS rank,
         count(*) OVER () AS n
  FROM process AS p JOIN thread AS t ON t.upid=p.upid
  JOIN thread_track AS tt ON tt.utid=t.utid JOIN track AS tr ON tr.id=tt.id
  JOIN slice AS s ON s.track_id=tr.id
  WHERE p.name='com.superplayer.demo' AND t.tid=p.pid AND s.name='bindApplication'
)
SELECT bind_ms AS median_bind_application_ms FROM ranked WHERE rank = (n + 1) / 2
```

The `current` trace: 1 row.

```sql
WITH ranked AS (
  SELECT s.dur / 1e6 AS bind_ms,
         row_number() OVER (ORDER BY s.dur) AS rank,
         count(*) OVER () AS n
  FROM process AS p JOIN thread AS t ON t.upid=p.upid
  JOIN thread_track AS tt ON tt.utid=t.utid JOIN track AS tr ON tr.id=tt.id
  JOIN slice AS s ON s.track_id=tr.id
  WHERE p.name='com.superplayer.demo' AND t.tid=p.pid AND s.name='bindApplication'
)
SELECT bind_ms AS median_bind_application_ms FROM ranked WHERE rank = (n + 1) / 2
```

### c3. Commit fb30a9c67862bd42f9d8fab36f6c8dff37069417 registers DemoApplication in the manifest and adds synchronous launch-time cache work: checking or rebuilding a 192 MiB file and computing its CRC32 in Application.onCreate.

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

### c4. The launch-time code added by fb30a9c67862bd42f9d8fab36f6c8dff37069417 directly matches the trace's bindApplication and TTID regression, so it is the attributed culprit.

The `current` trace: 1 row.

```sql
WITH ranked AS (
  SELECT s.dur / 1e6 AS bind_ms,
         row_number() OVER (ORDER BY s.dur) AS rank,
         count(*) OVER () AS n
  FROM process AS p JOIN thread AS t ON t.upid=p.upid
  JOIN thread_track AS tt ON tt.utid=t.utid JOIN track AS tr ON tr.id=tt.id
  JOIN slice AS s ON s.track_id=tr.id
  WHERE p.name='com.superplayer.demo' AND t.tid=p.pid AND s.name='bindApplication'
)
SELECT bind_ms AS median_bind_application_ms FROM ranked WHERE rank = (n + 1) / 2
```

The `current` trace: 1 row.

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
INCLUDE PERFETTO MODULE android.startup.time_to_display;
WITH cold AS (
  SELECT d.time_to_initial_display AS ns
  FROM android_startups AS s
  JOIN android_startup_time_to_display AS d USING (startup_id)
  WHERE s.package = 'com.superplayer.demo' AND s.startup_type = 'cold'
), ranked AS (
  SELECT ns, row_number() OVER (ORDER BY ns) AS rank, count(*) OVER () AS n
  FROM cold
)
SELECT ns / 1e6 AS median_ttid_ms FROM ranked WHERE rank = (n + 1) / 2
```

Commit, changing `demo/src/main/kotlin/com/superplayer/demo/DemoApplication.kt`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

Commit, changing `demo/src/main/AndroidManifest.xml`:

```text
fb30a9c67862bd42f9d8fab36f6c8dff37069417
```

## Caveats

- Each side is a single trace capture, so run-to-run noise cannot be quantified independently, although each trace contains multiple cold starts.
- The current run metadata identifies a non-debuggable benchmark build on an sdk_gphone64_arm64 emulator.

## Run

`gpt-5.6-luna` on openai, effort high: 40 tool calls, $0.0267, 283 s.
Tokens: 30 input, 195,154 cache read, 48,799 cache write, 8,853 output.
