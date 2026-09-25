# Roadmap

The features, in build order. Each item has a GitHub issue that serves as its spec
(ADR-0003), and its own branch. See `mission.md` for why and `tech-stack.md` for tools and
limits.

Status: `[ ]` todo, `[~]` in progress, `[x]` done.

## Phase 1: Harness and ground truth

Build the evaluation in week 1, not at the end.

**Exit:** `perfettoagent tp --trace x --sql "…"` works, and `pytest` is green with no network.

### 1. [x] Project scaffolding ([#1](https://github.com/ramesh130/perfettoagent/issues/1))
The uv package, ruff, pytest with sockets disabled, and a CLI stub.
- **Done when:** ruff check, ruff format --check and pytest pass offline.

### 2. [x] Trace processor pinning, `query_trace`, and `tp` ([#2](https://github.com/ramesh130/perfettoagent/issues/2))
Download `trace_processor_shell` 58.2, verify its sha256, and cache it. Build the
`query_trace` tool and a `perfettoagent tp` passthrough. Port the behaviour from devicelab's
`lib/trace_processor.sh`.
- **Done when:** `tp` returns rows from a devicelab trace, a tampered archive is refused, and
  a non-SELECT statement is rejected.

### 3. [x] Metric library ([#3](https://github.com/ramesh130/perfettoagent/issues/3) tracer, [#7](https://github.com/ramesh130/perfettoagent/issues/7) startup, [#8](https://github.com/ramesh130/perfettoagent/issues/8) frames, [#9](https://github.com/ramesh130/perfettoagent/issues/9) thread/memory)
Canned SQL, each tested against a fixture trace with a known answer.

| Metric | Source | Needs baseline |
|---|---|---|
| `startup_ttid_ms`, `startup_ttfd_ms` | `android_startups`, `android_startup_time_to_display` | yes |
| `jank_frames_pct`, `frame_p95_ms`, `frame_p99_ms` | stdlib `android_frames_layers` (the app's window layer), `actual_frame_timeline_slice` | yes |
| `frame_ui_time_p95_ms` (ADR-0011) | stdlib `android_frames_choreographer_do_frame` (UI time, as `android_frames_ui_time`) | yes |
| `main_thread_blocked_ms` (ADR-0013) | `thread_state` inside the main thread's top-level `slice`s other than `Choreographer#doFrame` | no |
| `binder_wait_ms` (ADR-0013) | stdlib `android_binder_txns` (the main thread's synchronous calls) | no |
| `heap_growth_objects_by_class` | stdlib `heap_graph_class_aggregation` (reachable objects in `heap_graph_object`, by `heap_graph_class`) | yes |
| `native_unfreed_bytes` (ADR-0014) | `heap_profile_allocation` | no |
| `gc_time_ms` (ADR-0013) | stdlib `android_garbage_collection_events` (the app's collections) | no |

- The startup metrics are the median cold start of the app (ADR-0009).
- The frame metrics count the app's window layer, and jank is `App Deadline Missed`
  (ADR-0011).
- The thread metrics use the frame metrics' app and its main thread. Main-thread
  blocking counts only blocking outside `Choreographer#doFrame` (ADR-0013).
- A metric with no data on a trace reads `null` with a `no_data` reason, never 0.
  No fixture has a native heap profile, so `native_unfreed_bytes` is tested only on
  that path until a heapprofd capture exists (ADR-0014).
- **Done when:** every metric has a passing fixture test, and `compute_metric` returns
  `sql_used`.

### 4. [x] Verifier (the guardrail) ([#4](https://github.com/ramesh130/perfettoagent/issues/4))
Deterministic checks that run after the model's final output and before anything is written:
1. Re-run each trace citation's SQL. It must parse, and `row_count` must be ≥ 1.
2. For each commit citation, the sha must resolve to a commit (`git cat-file
   --batch-check`, ADR-0006), the commit must be inside
   `--range` (checked with `merge-base --is-ancestor`), and it must touch `path` when a path
   is given.
3. Drop any claim with a failed citation and log it under `dropped_claims` with the reason.
4. If a culprit is set, at least one surviving claim must cite it.
5. If no claim survives, the verdict becomes `inconclusive` with an explanation.
- **Done when:** unit tests with hand-built bad outputs cover every rule. If the verifier is
  slow, cache SQL results by hash. Never skip it. The exact meaning of each rule, and the
  cache, are in ADR-0006.

### 5. [x] Ground truth: planted regressions ([#5](https://github.com/ramesh130/perfettoagent/issues/5) startup, [#6](https://github.com/ramesh130/perfettoagent/issues/6) jank, [#10](https://github.com/ramesh130/perfettoagent/issues/10) case packaging)
Add startup and jank scenarios to devicelab, then capture these plants on the superPlayer
demo:

| Regression | Plant | Expected metric |
|---|---|---|
| Main-thread I/O on startup | Synchronous file read in `Application.onCreate` (the patch adds the subclass; ADR-0007) | `startup_ttid_ms` |
| Allocation storm | 1M boxed floats in each scrolled frame's draw in the feed (ADR-0008) | `frame_ui_time_p95_ms`, `gc_time_ms` (ADR-0011) |
| Synchronous sleep | `Thread.sleep(120)` in a click handler | `main_thread_blocked_ms` |
| Layout thrash | Forced re-measure of each visible item every frame in a Compose `LazyColumn`, with a width-fitted title (ADR-0007, ADR-0008) | `frame_ui_time_p95_ms`, `jank_frames_pct` (ADR-0011) |
| Listener leak | devicelab's existing `resetForReuse` plant | `heap_growth_objects_by_class` |

Also capture **clean pairs** (baseline against a second clean capture), at least as many as
there are planted cases.

Each case is an opaque id. `evals/cases/<id>/` holds only what the model sees: both traces,
and the range as two shas in a fixture repo built to match them. The expected metric, the
expected culprit and the patch live apart, in `evals/answers/` (ADR-0015). Case rules:
- Each range contains at least 8 unrelated commits, so attribution is a search, not a lookup.
- No prompt, path or fixture that the model can see names the plant. A test scans for leaks.
- **Done when:** five planted cases and at least five clean pairs are committed.

## Phase 2: Agent and eval

**Exit:** the README has real numbers, `docs/postmortem.md` exists, and a two-minute
recording (trace in, diagnosis out) is linked.

### 6. [x] Git and repo tools ([#24](https://github.com/ramesh130/perfettoagent/issues/24) git tools, [#25](https://github.com/ramesh130/perfettoagent/issues/25) `symbolize`, [#31](https://github.com/ramesh130/perfettoagent/issues/31) `read_run_metadata`)
`get_git_log`, `get_git_diff`, `git_blame`, `grep_repo`, `symbolize` and
`read_run_metadata` (ADR-0025), with the limits in `tech-stack.md`.
- **Done when:** each tool has schema and limit tests against a fixture repo.

### 7. [x] `diagnose`: agent loop and output ([#29](https://github.com/ramesh130/perfettoagent/issues/29) tracer bullet, [#43](https://github.com/ramesh130/perfettoagent/issues/43) OpenAI)
Build the Tool Runner loop, the frozen system prompt and structured output. #29 built the
Anthropic loop, `diagnosis.json` and an offline end-to-end test (ADR-0022). #43 added the
OpenAI loop and made `gpt-5.6-luna` the default; `--provider` and `--model` choose the
model (ADR-0020). The done criterion below is met by a live `gpt-5.6-luna` run (ADR-0023).
#30 added `diagnosis.md`, rendered from the verified `diagnosis.json` (ADR-0024), and #31
the `--run-json` rules and `read_run_metadata` (ADR-0025), and #49 the `--effort` flag.
A live `claude-opus-5-5` run of the leak case found the same culprit, with every claim kept (ADR-0023).

The prompt states the workflow: establish the metric delta, then localise it in the trace
(thread, slice, span), then correlate it with the range, then blame.

Input rules (ADR-0025; `--run-json` takes run metadata schema 1, not a capture's `run.json`):
- If the `--run-json` commit is outside `--range`, refuse.
- A dirty tree or a `debuggable: true` build becomes a caveat in the header. Never accept one
  silently.

Outputs:
- `diagnosis.json` (schema 1, ADR-0006) with: verdict (`regression`, `no_regression` or
  `inconclusive`); the metric with baseline, current and delta; confidence; the culprit
  (commit, files, and attribution `direct` or `correlated`); claims with `trace` or `commit`
  citations; caveats; `dropped_claims`; tool-call count; usage and USD; and wall time.
- `diagnosis.md`, which leads with the verdict, then a metric table, then each claim followed
  by its evidence in a fenced block. A reader should get the point from the first ten lines.
  A trace citation's evidence is its SQL and verified row count; schema 1 keeps no rows
  (ADR-0024).
- **Done when:** the first end-to-end diagnosis of the leak case passes the verifier.

### 8. [x] Second app ([#34](https://github.com/ramesh130/perfettoagent/issues/34) plants and captures, [#35](https://github.com/ramesh130/perfettoagent/issues/35) cases)
JetNews, from Google's `android/compose-samples` (Q1, ADR-0017, which maps where each plant
goes). Apply the same five plants and capture clean pairs.
- **Plants and captures (#34, ADR-0021):** done, in the private repo `ramesh130/jetnews-perf`.
  Each plant is sized from JetNews's own clean noise, and three captures of each show it on its
  expected metric. The leak's culprit adds a listener registration with no removal. Layout
  thrash shows on `frame_ui_time_p95_ms` but not on `jank_frames_pct`.
- **Cases (#35, ADR-0028):** five planted cases and five clean pairs, built by
  `evals/build_jetnews_cases.py` into their own bundle. Layout thrash expects
  `frame_ui_time_p95_ms` only on this app.
- **Done when:** its cases are in `evals/cases/`.

### 9. [x] Eval runner and results ([#33](https://github.com/ramesh130/perfettoagent/issues/33) runner)
Write a local `evals/run_eval.py`, since `evalharness` cannot score these runs (Q2, ADR-0016).
#33 built it as `perfettoagent eval`, and scored every superPlayer case three times on
`gpt-5.6-luna` at effort `high` (ADR-0027). #44 added `--provider`, `--model` and
`--effort`, one results directory per setting, and the cache check (ADR-0029). #36 swept
both apps' cases at four effort levels on `gpt-5.6-luna`, and settled Q3, into the
generated `evals/results/summary.md` (ADR-0031). `claude-opus-5-5` was not swept, by
decision: one live run only (ADR-0023).
Run every case **three times** and sweep effort levels, for each model: `gpt-5.6-luna`, the
headline, and `claude-opus-5-5`, compared (ADR-0020). Never pool results across models.
Report:

| Metric | Definition |
|---|---|
| Detection rate | Planted cases where the verdict is `regression` and the metric matches |
| Attribution rate | Detected cases where `culprit.commit` equals the planted sha |
| False-positive rate | Clean pairs where the verdict is `regression` |
| Citation validity | Citations that pass the verifier before dropping, as a share of all citations |
| Time to diagnosis | Agent wall time vs. timed manual triage on the same five cases (assumed until #27 measures it, ADR-0030) |
| Cost and tokens per trace | USD, input, output and cache-read tokens for each model and effort level |

Never score on the model's own confidence field.
- **Done when:** a summary table is committed to `evals/results/summary.md`.

### 10. [x] `review`: human-in-the-loop feedback ([#32](https://github.com/ramesh130/perfettoagent/issues/32))
`perfettoagent review <out-dir>` accepts `accept`, `reject <reason>` or
`partial <claim-ids>`, and appends the answer to `evals/feedback.jsonl` along with hashes of
the inputs. A rejected diagnosis is a candidate eval case. The trace hashes and range come
from `diagnosis.json`'s `run.inputs`, recorded by `diagnose`; `partial` names the kept
claims that are right (ADR-0026).

### 11. [ ] Write-up
The README opens with the one-liner, a real diagnosis and the eval table. Add
`docs/postmortem.md` covering what the agent got wrong and why. Record a two-minute
walkthrough.

## Open questions

Settle each one by recording an ADR in `docs/adr/`.

1. **Q1.** ~~Which open-source app builds fastest on Apple silicon with the API 36 emulator?~~
   **Resolved (ADR-0017):** JetNews, from Google's `android/compose-samples` (Apache-2.0).
   The user's expense tracker, tried first, had its whole UI in one file and an empty list.
   JetNews built unchanged in 156 s cold, with Java processes peaking at 2.4 GB, and its home
   feed scrolls offline. `android_startups` found both cold starts in its trace.
2. **Q2.** ~~Does `evalharness` accept a per-case tool-call transcript as a quality input, or is
   a local runner needed?~~
   **Resolved (ADR-0016):** a local runner. Its scorer sees tool calls without their results
   and returns one float per task, and it refuses repeated runs of a case. Item 9 writes
   `evals/run_eval.py`.
3. **Q3.** ~~Should `--metric auto` ship in v1?~~
   **Resolved (ADR-0031):** yes, alone. At `high`, attribution is the same with `auto` as with
   the named metric (26/26 against 30/30). Detection is lower (26/30 against 30/30), and the
   summary shows that beside it.
4. **Q4.** ~~Is the `android_startups` stdlib module reliable on API 36 emulator traces?~~
   **Resolved (ADR-0009):** yes. It found all 160 cold starts in the eight #5 captures, and
   each startup's duration was within 1.1 ms of `am start -W`.

## Definition of done (v1)

The eval table is published in the README, backed by `evals/results/`, and the walkthrough is
recorded.
