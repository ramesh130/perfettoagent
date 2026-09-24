# Inconclusive

- **Metric:** none measured
- **Culprit:** none attributed; the verifier dropped the model's: no surviving claim cites the culprit commit 1f2e3d4c5b6a
- **Verified:** 0 claims kept, 1 dropped; 0 of 2 citations passed
- **Verdict changed** by the verifier from `regression`: no claim survived verification: all 1 were dropped
- **Model's confidence:** none; the verifier changed what it was given for

## Claims

No claim survived the verifier.

## Caveats

- A single capture per side, on an emulator.
- the metric was dropped by the verifier: its sql_used on the baseline trace: returned 0 rows

## Dropped claims

### c0. Frames got slower.

Dropped: citation 1: returned 0 rows

The `current` trace: 0 rows. Failed: returned 0 rows

```sql
SELECT * FROM slice WHERE 0
```
