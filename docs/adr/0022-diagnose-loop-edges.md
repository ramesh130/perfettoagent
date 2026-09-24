# The `diagnose` loop: what the model sees, which errors it gets back, and runs with no answer

Issue #29 builds `diagnose` (roadmap item 7) on the Anthropic Tool Runner. The issue and `docs/tech-stack.md` leave several edges open, and two of the choices diverge from `docs/tech-stack.md` as written, so they are recorded here. Affects `src/perfettoagent/agent.py`, `trace_tools.py` and `cli.py`, and `docs/tech-stack.md` ("Model and SDK", and the `query_trace` row of the tool table).

## `query_trace` takes the SQL a citation takes

`docs/tech-stack.md` said `query_trace` "accepts only `SELECT`/`WITH`". It also says to use the Perfetto stdlib modules and to name the module in `sql_used`, and a trace citation may start with `INCLUDE PERFETTO MODULE` lines (ADR-0005). With a SELECT-only tool the model could cite a module's rows but never run the query it cites. So `query_trace` takes one SELECT or WITH, optionally preceded by `INCLUDE PERFETTO MODULE <name>;` lines, split off by `split_includes` exactly as the verifier splits a citation. The statement after them still has to pass the SELECT-only gate, and a module name must match the module-name pattern. What the model runs is what it cites is what the verifier re-runs.

## The model is shown no path

`docs/tech-stack.md` listed paths among the volatile inputs for the first user message. The first message carries the range and the metric choice only, and the range as the two full shas its ends resolve to, never the names it was given: `main..fix-slow-feed` would say what the range holds. The trace tools name a trace by its side (`baseline`, `current`) and the git tools read the repo the run binds, so the model never needs a path. A path can say more than the trace does: an eval case's staged path is neutral, but a user's `leak-hunt/heap-final.perfetto-trace` is not, and CLAUDE.md forbids naming the planted change in anything the model sees. A test checks that no request carries either path.

## Which tool errors the model gets back

ADR-0018 said a `ToolInputError` or a `GitError` becomes an error tool_result. The loop adds three more that are the model's call's own doing: `QueryRejected` (not a SELECT), `MetricError` (no such metric) and `TraceProcessorError`. The last counts because the binary is resolved and both traces checked before the first request, so inside the loop it can only be the SQL's fault: a syntax error, an unknown table, a timeout. Its message is cut to its last 2,000 characters, which name what went wrong.

Anything else a tool raises, `GitUnavailable` above all, is a failure of the run. The SDK's runner turns every exception into an error result, so the loop runs each turn's tools itself, as soon as the turn ends, and raises `RunFailed` before another request. The model never sees a broken machine as its own mistake.

## A run with no answer is an inconclusive diagnosis

`stop_reason` is read before any content. A refusal, an answer cut off at `max_tokens`, 60 turns without an answer (`MAX_TURNS`, a guard against a loop that is not converging) or any other stop reason gives an `inconclusive` output with no claims and the reason as a caveat. A refusal's caveat names its `stop_details.category`, or `unspecified`: schema 1 has no field for it, and a caveat is the model-facing slot for what limits the answer. That output still goes through the verifier, and `diagnosis.json` is written, so the run's tokens and USD are recorded like any other run's. Nothing is retried.

An answer that is not JSON, or does not match `OUTPUT_SCHEMA`, is different: structured output should make it impossible, so it raises `DiagnosisInvalid` and nothing is written. A `diagnosis.json` that exists has always been verified.

## The metric is re-measured by name

ADR-0006 asked that `metric` come from `compute_metric` rather than the model's copy. The name is `--metric` when one was given, else the name the model wrote. With `--metric`, the metric is measured even if the model answered with none, since a measured change with no cause is still worth reporting. A name the library does not have leaves `metric` null, with a caveat that says so.

## `symbolize` is bound, with no mapping yet

The issue lists `query_trace`, `list_metrics`, `compute_metric` and the git tools. `symbolize` (ADR-0019) is bound too, since the prompt's step 2 localises to frames. `diagnose` has no `--mapping` flag yet, so it returns each frame's name as the trace has it and says so (`no_mapping`).

## Consequences

- `docs/tech-stack.md` cites this ADR in the `query_trace` row and for the first user message.
- The live end-to-end run on the leak case (roadmap item 7's done criterion, and #29's second acceptance criterion) moves to #43, because no API key was available when #29 was built. In its place, an offline test runs the SDK's real Tool Runner against a scripted model over an in-process HTTP transport, with the real tools on the staged case, and checks that its `diagnosis.json` keeps every claim. That proves the plumbing, from tool calls through the verifier to the file. It does not prove that a model finds the commit; only the live run can, on each provider #43 ships.
- `diagnosis.md`, `--run-json`, `--effort`, and `--provider`/`--model` (ADR-0020) are left to later issues. `diagnose()` takes `model` and `effort` as parameters, and refuses a model with no price row, but does not yet check an effort level against the model.
