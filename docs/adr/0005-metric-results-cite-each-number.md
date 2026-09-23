# Metric results carry SQL that re-runs to each number they report

Issue #3 gives `compute_metric` the shape `{baseline, current, delta, unit, sql_used}`, and the verifier (roadmap item 4) re-runs a citation's SQL through `query_trace`, which returns at most 200 rows. That works for a scalar metric. It does not work for a per-class one: a heap dump has about 43,000 classes, and a claim about one of them cites a number the 200-row cap cannot show. So the result shape is extended, and every number in it comes with SQL that returns exactly that number on either trace. Affects `docs/tech-stack.md` (Agent tool surface: `compute_metric`) and `src/perfettoagent/metrics/`.

- A metric is one `.sql` file in `src/perfettoagent/metrics/`, with an `@field` header. It is either scalar (one row, `value`) or keyed (rows of `key, value`, whose values add up across keys, so an absent key counts as 0).
- A scalar metric's `sql_used` is its file's SQL, verbatim.
- A keyed metric's `sql_used` wraps the file's SQL as `SELECT sum(value) AS value FROM (...)`, so the headline `baseline` and `current` are the totals across keys. Its `breakdown` lists up to 40 keys, ranked by growth. Each row has its own `sql_used`, which returns that key's one row, or 0 where the key is absent.
- In every `sql_used`, the `INCLUDE PERFETTO MODULE` lines come first, verbatim. `query.split_includes` turns an `sql_used` back into the `sql` and `modules` that `query_trace` takes. The verifier, and the model-facing `query_trace` tool if it accepts pasted citations, must split it this way. The SELECT-only gate still applies to what is left.
- `query_trace(max_rows=None)` lifts the 200-row cap. Only `compute_metric` uses it, to join two traces' rows in code before the model sees any of them. The model-facing tool (roadmap item 7) must not expose it. The cap in `tech-stack.md` is a limit on what the model is shown, and it still holds.

## Consequences

- A keyed metric costs about 150 tokens per breakdown row, so about 6k tokens for 40 rows.
- Computing it runs the trace processor four times per trace: twice for the headline and twice for the full table.
