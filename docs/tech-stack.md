# Tech stack

Every tool and version pin used here, and the limits they must respect. To change anything in
this file, first record an ADR in `docs/adr/`.

## Language and tooling

| Tool | Choice | Notes |
|---|---|---|
| Language | Python 3.12 | One package, `perfettoagent`, under `src/`. |
| Env / packaging | `uv` | `uv sync`, `uv run …`. The lockfile is committed. |
| Lint / format | `ruff` | Rules `E, F, I, B, UP`. A Claude Code hook formats edited `.py` files. |
| Tests | `pytest` + `pytest-socket` | `--disable-socket` is always on, so the suite must pass with no network. |
| Large fixtures | Git LFS | Traces too large for plain git: test fixtures under `tests/fixtures/large/` (ADR-0004), new ones gzipped (ADR-0010), including the R8 mapping that goes with a minified capture (ADR-0019), and the eval cases' traces under `evals/cases/`, which a default fetch leaves out (ADR-0015). Without LFS, the tests that need them skip. |
| CLI | `argparse` | Subcommands `diagnose`, `review`, `eval`, `tp`. |
| CI | GitHub Actions | Runs `uv sync --locked`, ruff check, ruff format --check and pytest. Manual only (`workflow_dispatch`) until there is an Actions budget; until then run the same checks locally. |
| License | Apache-2.0 | ADR-0002. |

## Model and SDK

Two providers, chosen per run with `--provider {anthropic,openai}` and `--model <id>`
(ADR-0020, which supersedes ADR-0001). ADR-0020 maps each rule below onto both SDKs.

- **Default: OpenAI `gpt-5.6-luna`**, the headline model in the eval table (ADR-0023).
  **Anthropic `claude-opus-5-5`** is the compared variant, with `--provider anthropic`.
  Model ids have no date suffix. A model with no row in the price table, or named under the
  other provider, is refused before any request.
- **Anthropic Python SDK**, beta Tool Runner (`client.beta.messages.tool_runner` with
  `@beta_tool`). Don't hand-write the `stop_reason == "tool_use"` loop in v1. Each tool's
  schema is written by hand and passed to `beta_tool` unchanged, not generated (ADR-0018).
  Adaptive thinking is on.
- **OpenAI Python SDK**, Responses API (`client.responses.create`), not Chat Completions. It
  has no tool runner, so this one loop is written by hand. The same hand-written schemas go
  in as strict function tools, unchanged (ADR-0020). Requests set `store: false` and replay
  the whole history, reasoning items included (ADR-0023).
- The effort level sweeps `low`, `medium`, `high` and `xhigh` for the cost table, and
  defaults to `high`. `diagnose --effort` chooses it (#49, ADR-0023). It is always sent:
  `output_config.effort` for Anthropic, `reasoning.effort` for OpenAI. A level a model does
  not support is refused, never rounded.
- Every request is streamed, with an output cap of 64000 tokens (`max_tokens`,
  `max_output_tokens`). Check for truncation and refusal before reading content. Record a
  refusal or a truncated output as an `inconclusive` verdict with its reason (and its
  category, where the provider gives one), and never retry it in a loop.
- Structured output goes through `output_config.format` or `text.format`, and is then
  validated again locally.
- The system prompt is frozen text, cached: a `cache_control` breakpoint for Anthropic, the
  first `developer` item under implicit caching for OpenAI. Volatile inputs (range, run
  metadata; never a path, ADR-0022) go in the first user message. From the second eval run
  on, cache reads must be non-zero: `usage.cache_read_input_tokens` for Anthropic,
  `usage.input_tokens_details.cached_tokens` for OpenAI.
- Don't use assistant prefill or forced tool choice. Tool choice is `auto` on both.
- Look up SDK details from the source, not from memory: the `claude-api` skill for
  Anthropic, OpenAI's own docs for OpenAI. The Anthropic API surface changed in 2026.
- Auth comes from `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`, in the environment or a `.env`
  file that `.gitignore` excludes, the environment winning; Anthropic also takes an
  `ant auth login` profile (ADR-0023). No key is ever logged or written to results, and
  printed errors are redacted. Tests use neither key. Never put secrets in the repo.
- USD per run comes from a price table keyed by model id, with each price's source and the
  date it was checked (ADR-0020).

## Perfetto

- **`trace_processor_shell` pinned to 58.2**, the version devicelab also pins.
- It's downloaded for the host platform and its sha256 is checked against a pin file in this
  repo. A mismatched archive is refused, not run.
- It's cached under `~/.cache/perfettoagent`. `TRACE_PROCESSOR=/path` overrides it.
- Traces are opened read-only through trace processor. **Nothing in this repo parses the
  protobuf.**
- Use the stdlib modules (`INCLUDE PERFETTO MODULE android.startup.startups`,
  `android.frames.timeline`) rather than re-deriving them. Name the module in `sql_used`.

## Target repo access

- The target repo is read **only** through `git` subprocess calls (`log`, `diff`, `blame`,
  `grep`, `cat-file`, `merge-base`). Nothing ever writes to it.

## Agent tool surface and limits

Every tool is a Python function with a strict JSON schema (`strict: true`,
`additionalProperties: false`), declared together as a `perfettoagent.tools.Tool` (ADR-0018).
Each description says what the tool *cannot* tell the model. A cap is the default and the
ceiling, and each capped result says whether it was cut and gives the true total.

| Tool | Limit / rule |
|---|---|
| `query_trace(sql, which)` | Accepts only `SELECT`/`WITH`, after any `INCLUDE PERFETTO MODULE` lines, as a citation does (ADR-0022). Returns at most **200 rows**, capped in our code, and `row_count` always gives the true total. |
| `list_metrics()` | Lists the canned metric library only. |
| `compute_metric(name)` | Returns the `sql_used` so the model can cite it. A per-key metric also returns at most 40 breakdown rows, and each one has its own `sql_used` (ADR-0005). A value the trace has no data for is `null`, with a `no_data` reason, never 0 (ADR-0014). |
| `get_git_log(range, paths)` | At most **200 commits**. |
| `get_git_diff(sha, path, max_lines=400)` | Reports when output was truncated. |
| `git_blame(path, line_start, line_end, at)` | At most **200 lines** (ADR-0018). |
| `grep_repo(pattern, paths, max_hits=100, at)` | Implemented with `git grep`, on commit `at`, never the working tree (ADR-0018). |
| `symbolize(frame, which)` | Java/Kotlin only, using `stack_profile_*` tables and `--mapping`. Returns `null` for native frames. `frame` is a `stack_profile_frame` id in the `which` trace, and each side has its own R8 mapping, read as text (ADR-0019). |
| `read_run_metadata()` | Available only when `--run-json` was passed. The file is run metadata schema 1, not a capture tool's `run.json`, and its commit must be inside `--range` (ADR-0025). |

## Evaluation

- Run evals with a local runner, `perfettoagent eval` or `evals/run_eval.py` (ADR-0016,
  ADR-0027). Each case is staged afresh per run, and each set of runs shares one model,
  effort level and metric choice (`--provider`, `--model`, `--effort`), in
  `evals/results/<model>-<effort>-<metric>/`, never pooled with another (ADR-0029). `evalharness`
  (`pareto-eval`) was checked first. Its scorer and aggregator cannot express item 9's rates
  or repeated runs, and integrating would cost more than a day. The ADR records the gap.

## Not allowed

- A web UI, a database, or LangChain.
- A third model provider, without its own ADR. Two are allowed (ADR-0020).
- Any runtime or test-time dependency on superPlayer or devicelab. Copy fixtures and code in
  instead; copying about 50 lines beats importing.
- Parsing trace protobufs directly.
