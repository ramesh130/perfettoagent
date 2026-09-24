# No fixture has a native heap profile, and a metric with no data says so

Issue #9 asks for `native_unfreed_bytes`, read from `heap_profile_allocation`, with a fixture test on a capture that has that data. If no capture has it, the metric must return an explicit "no data" rather than 0, and the gap is recorded as an ADR. This is that ADR. It also records how "no data" reaches the model, which extends ADR-0005's result shape. Affects `src/perfettoagent/metrics/__init__.py`, `docs/tech-stack.md` (`compute_metric`) and roadmap item 3.

## The gap

`heap_profile_allocation` is filled only by the `android.heapprofd` data source. No fixture was captured with it: the heap dumps (`heap-a-*`) are Java heap graphs, and the startup and jank captures don't configure it. Each fixture has 0 rows, checked with the pinned trace processor (58.2) on all ten large fixtures and the tiny trace, and asserted by the tests on each of them. None of superPlayer devicelab's trace configs names heapprofd either. So `native_unfreed_bytes` ships with its NULL path tested on every fixture. Its value path, `sum(size)` over the native heaps, is tested against no real profile. That query is the stdlib's own definition of unreleased memory, summed over every callstack.

Closing the gap needs a devicelab scenario that runs heapprofd on the demo, and a fixture from it. That belongs with roadmap item 5 or a later issue, not this one.

## How "no data" is represented

A metric's SQL returns NULL when the trace lacks what it reads. That is already how the frame metrics read on a trace without `frametimeline` (ADR-0011). NULL was implicit, though: `current: null` next to a `sql_used`, which a model could read as zero, or as a failure worth retrying. So:

- **A metric file may carry `-- @no_data: <reason>`,** saying what the trace lacks when the SQL returns NULL.
- **`compute_metric` adds `no_data: {side: reason}`** for each trace it was given whose value is NULL. A file without `@no_data` gets a generic reason. `baseline`, `current` and `delta` stay None, as before. When every value is present, the key is absent, so every existing result keeps its shape.
- **In SQL, NULL is the only "no data".** No sentinel number or string can be mistaken for a measurement. A metric returns NULL when the data it reads is missing: its data source was off, or produced nothing to measure, or the app it looks for is absent. When the data is there and the app simply has no events in it, it returns 0 (ADR-0013).
- **Why here, not in each metric's description.** The description is read before choosing a metric. `no_data` arrives with the result, next to the missing number, so it can be passed on or cited as a reason for being inconclusive. It is general: any metric that can read NULL gets it, including a keyed one whose headline sum covers zero rows.

## Consequences

- The metrics that read NULL before this change (the frame and startup metrics) have no `@no_data` line yet, so they give the generic reason. Adding theirs is a follow-up.

- The result shape gains one optional key. The verifier (ADR-0006) is unchanged. A `sql_used` that returns NULL still re-runs to one row, so a claim that a trace lacks the data can be cited. A claim of a number where the result says `no_data` has nothing to cite.
- Roadmap item 3 is done by the issue's own acceptance criteria. `native_unfreed_bytes`' fixture test covers only its NULL path until a heapprofd fixture exists.
