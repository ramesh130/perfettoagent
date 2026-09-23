# Roadmap

The features, in build order. Each item gets its own spec (`docs/specs/<nn>-<slug>.md`)
before implementation starts, and its own GitHub issue and branch. See `mission.md` for why
and `tech-stack.md` for tools and limits.

Status: `[ ]` todo, `[~]` in progress, `[x]` done.

## Phase 1: Harness and ground truth

Build the evaluation in week 1, not at the end.

**Exit:** `perfettoagent tp --trace x --sql "…"` works, and `pytest` is green with no network.

### 1. [x] Project scaffolding ([#1](https://github.com/ramesh130/perfettoagent/issues/1))
The uv package, ruff, pytest with sockets disabled, and a CLI stub.
- **Done when:** ruff check, ruff format --check and pytest pass offline.

### 2. [ ] Trace processor pinning, `query_trace`, and `tp` ([#2](https://github.com/ramesh130/perfettoagent/issues/2))
Download `trace_processor_shell` 58.2, verify its sha256, and cache it. Build the
`query_trace` tool and a `perfettoagent tp` passthrough. Port the behaviour from devicelab's
`lib/trace_processor.sh`.
- **Done when:** `tp` returns rows from a devicelab trace, a tampered archive is refused, and
  a non-SELECT statement is rejected.

### 3. [ ] Metric library ([#3](https://github.com/ramesh130/perfettoagent/issues/3) tracer, [#7](https://github.com/ramesh130/perfettoagent/issues/7) startup, [#8](https://github.com/ramesh130/perfettoagent/issues/8) frames, [#9](https://github.com/ramesh130/perfettoagent/issues/9) thread/memory)
Canned SQL, each tested against a fixture trace with a known answer.

| Metric | Source | Needs baseline |
|---|---|---|
| `startup_ttid_ms`, `startup_ttfd_ms` | `android_startups`, `slice` | yes |
| `jank_frames_pct`, `frame_p95_ms`, `frame_p99_ms` | `actual_/expected_frame_timeline_slice` | yes |
| `main_thread_blocked_ms` | `thread_state`, `slice` | no |
| `binder_wait_ms` | `slice` (binder) | no |
| `heap_growth_objects_by_class` | `heap_graph_object`, `heap_graph_class` | yes |
| `native_unfreed_bytes` | `heap_profile_allocation` | no |
| `gc_time_ms` | `slice` (`GC`) | no |

- **Blocked on:** open question Q4. Settle it before building the startup metrics.
- **Done when:** every metric has a passing fixture test, and `compute_metric` returns
  `sql_used`.

### 4. [ ] Verifier (the guardrail) ([#4](https://github.com/ramesh130/perfettoagent/issues/4))
Deterministic checks that run after the model's final output and before anything is written:
1. Re-run each trace citation's SQL. It must parse, and `row_count` must be ≥ 1.
2. For each commit citation, `git cat-file -e` must succeed, the commit must be inside
   `--range` (checked with `merge-base --is-ancestor`), and it must touch `path` when a path
   is given.
3. Drop any claim with a failed citation and log it under `dropped_claims` with the reason.
4. If a culprit is set, at least one surviving claim must cite it.
5. If no claim survives, the verdict becomes `inconclusive` with an explanation.
- **Done when:** unit tests with hand-built bad outputs cover every rule. If the verifier is
  slow, cache SQL results by hash. Never skip it.

### 5. [ ] Ground truth: planted regressions ([#5](https://github.com/ramesh130/perfettoagent/issues/5) startup, [#6](https://github.com/ramesh130/perfettoagent/issues/6) jank, [#10](https://github.com/ramesh130/perfettoagent/issues/10) case packaging)
Add startup and jank scenarios to devicelab, then capture these plants on the superPlayer
demo:

| Regression | Plant | Expected metric |
|---|---|---|
| Main-thread I/O on startup | Synchronous file read in `Application.onCreate` | `startup_ttid_ms` |
| Allocation storm | 50k small objects per frame in a scroll list | `jank_frames_pct`, `gc_time_ms` |
| Synchronous sleep | `Thread.sleep(120)` in a click handler | `main_thread_blocked_ms` |
| Layout thrash | Forced `requestLayout` in a `RecyclerView` bind | `frame_p95_ms` |
| Listener leak | devicelab's existing `resetForReuse` plant | `heap_growth_objects_by_class` |

Also capture **clean pairs** (baseline against a second clean capture), at least as many as
there are planted cases.

Each case lives in `evals/cases/<opaque-id>/` with the patch, both traces, the range as two
shas, the expected metric and the expected culprit. Case rules:
- Each range contains at least 8 unrelated commits, so attribution is a search, not a lookup.
- No prompt, path or fixture that the model can see names the plant.
- **Done when:** five planted cases and at least five clean pairs are committed.

## Phase 2: Agent and eval

**Exit:** the README has real numbers, `docs/postmortem.md` exists, and a two-minute
recording (trace in, diagnosis out) is linked.

### 6. [ ] Git and repo tools
`get_git_log`, `get_git_diff`, `git_blame`, `grep_repo`, `symbolize` and
`read_run_metadata`, with the limits in `tech-stack.md`.
- **Done when:** each tool has schema and limit tests against a fixture repo.

### 7. [ ] `diagnose`: agent loop and output
Build the Tool Runner loop, the frozen system prompt and structured output.

The prompt states the workflow: establish the metric delta, then localise it in the trace
(thread, slice, span), then correlate it with the range, then blame.

Input rules:
- If the `--run-json` commit is outside `--range`, refuse.
- A dirty tree or a `debuggable: true` build becomes a caveat in the header. Never accept one
  silently.

Outputs:
- `diagnosis.json` (schema 1) with: verdict (`regression`, `no_regression` or
  `inconclusive`); the metric with baseline, current and delta; confidence; the culprit
  (commit, files, and attribution `direct` or `correlated`); claims with `trace` or `commit`
  citations; caveats; `dropped_claims`; tool-call count; usage and USD; and wall time.
- `diagnosis.md`, which leads with the verdict, then a metric table, then each claim followed
  by its evidence in a fenced block. A reader should get the point from the first ten lines.
- **Done when:** the first end-to-end diagnosis of the leak case passes the verifier.

### 8. [ ] Second app
Pick Now in Android, Tivi or Signal-Android (see Q1). Apply the same five plants and capture
clean pairs.
- **Done when:** its cases are in `evals/cases/`.

### 9. [ ] Eval runner and results
Use `evalharness` if Q2 allows it; otherwise write a local `evals/run_eval.py`. Run every case
**three times** and sweep effort levels. Report:

| Metric | Definition |
|---|---|
| Detection rate | Planted cases where the verdict is `regression` and the metric matches |
| Attribution rate | Detected cases where `culprit.commit` equals the planted sha |
| False-positive rate | Clean pairs where the verdict is `regression` |
| Citation validity | Citations that pass the verifier before dropping, as a share of all citations |
| Time to diagnosis | Agent wall time vs. timed manual triage on the same five cases |
| Cost and tokens per trace | USD, input, output and cache-read tokens at each effort level |

Never score on the model's own confidence field.
- **Done when:** a summary table is committed to `evals/results/summary.md`.

### 10. [ ] `review`: human-in-the-loop feedback
`perfettoagent review <out-dir>` accepts `accept`, `reject <reason>` or
`partial <claim-ids>`, and appends the answer to `evals/feedback.jsonl` along with hashes of
the inputs. A rejected diagnosis is a candidate eval case.

### 11. [ ] Write-up
The README opens with the one-liner, a real diagnosis and the eval table. Add
`docs/postmortem.md` covering what the agent got wrong and why. Record a two-minute
walkthrough.

## Open questions

Settle each one by recording an ADR in `docs/adr/`.

1. **Q1.** Which open-source app builds fastest on Apple silicon with the API 36 emulator?
   Decide by trying, time-boxed to two hours. Blocks item 8.
2. **Q2.** Does `evalharness` accept a per-case tool-call transcript as a quality input, or is
   a local runner needed? Check its scorer interface first. Blocks item 9.
3. **Q3.** Should `--metric auto` ship in v1? Start with `auto`. If attribution drops more than
   10 points compared with a named metric, report both. Affects items 7 and 9.
4. **Q4.** Is the `android_startups` stdlib module reliable on API 36 emulator traces? Verify
   on the first capture. Blocks the startup metrics in item 3.

## Definition of done (v1)

The eval table is published in the README, backed by `evals/results/`, and the walkthrough is
recorded.
