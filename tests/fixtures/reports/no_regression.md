# No regression

- **Metric:** `startup_ttid_ms` +1.25 ms (412.25 → 413.5 ms)
- **Culprit:** none attributed
- **Verified:** 1 claim kept, 0 dropped; 3 of 3 citations passed
- **Model's confidence:** medium (never scored)

## Metric

| Metric | Unit | Baseline | Current | Delta |
|---|---|---:|---:|---:|
| `startup_ttid_ms` | ms | 412.25 | 413.5 | +1.25 |

Measured by:

```sql
INCLUDE PERFETTO MODULE android.startup.startups;
SELECT ttid FROM android_startups
```

## Claims

### c0. Cold start moved 1.25 ms, inside one capture's noise.

The `current` trace: 3 rows.

````sql
SELECT `ts`, dur FROM slice WHERE name = 'x ``` y'
````

## Run

`gpt-5.6-luna` on openai, effort high: 12 tool calls, $0.0051, 41 s.
Tokens: 33 input, 221,104 cache read, 44,528 cache write, 8,663 output.
