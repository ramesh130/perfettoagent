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
| Large fixtures | Git LFS | Traces too large for plain git: test fixtures under `tests/fixtures/large/` (ADR-0004), new ones gzipped (ADR-0010), and the eval cases' traces under `evals/cases/`, which a default fetch leaves out (ADR-0015). Without LFS, the tests that need them skip. |
| CLI | `argparse` | Subcommands `diagnose`, `review`, `eval`, `tp`. |
| CI | GitHub Actions | Runs `uv sync --locked`, ruff check, ruff format --check and pytest. Manual only (`workflow_dispatch`) until there is an Actions budget; until then run the same checks locally. |
| License | Apache-2.0 | ADR-0002. |

## Model and SDK

- **Anthropic Python SDK**, beta Tool Runner (`client.beta.messages.tool_runner` with
  `@beta_tool`). Don't hand-write the `stop_reason == "tool_use"` loop in v1. Each tool's
  schema is written by hand and passed to `beta_tool` unchanged, not generated (ADR-0018).
- **Model `claude-opus-5-5`** (ADR-0001), with no date suffix. Adaptive thinking is on.
  `output_config.effort` defaults to `high`. A CLI flag sweeps `low`, `medium`, `high` and
  `xhigh` for the cost table.
- Every request is streamed. The agent loop uses `max_tokens` 64000. Check `stop_reason` for
  `max_tokens` and `refusal` before reading content. Record a refusal as an `inconclusive`
  verdict with its category, and never retry it in a loop.
- Structured output goes through `output_config.format` and is then validated again locally.
- The system prompt is frozen text with a `cache_control` breakpoint. Volatile inputs
  (paths, range, run metadata) go in the first user message. From the second eval run on,
  `usage.cache_read_input_tokens` must be non-zero.
- Don't use assistant prefill or forced `tool_choice`; current models don't support them.
- Look up SDK details with the `claude-api` skill, not from memory. The API surface
  changed in 2026.
- Auth comes from `ANTHROPIC_API_KEY` or an `ant auth login` profile. Never put secrets in
  the repo.

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
| `query_trace(sql, which)` | Accepts only `SELECT`/`WITH`. Returns at most **200 rows**, capped in our code, and `row_count` always gives the true total. |
| `list_metrics()` | Lists the canned metric library only. |
| `compute_metric(name)` | Returns the `sql_used` so the model can cite it. A per-key metric also returns at most 40 breakdown rows, and each one has its own `sql_used` (ADR-0005). A value the trace has no data for is `null`, with a `no_data` reason, never 0 (ADR-0014). |
| `get_git_log(range, paths)` | At most **200 commits**. |
| `get_git_diff(sha, path, max_lines=400)` | Reports when output was truncated. |
| `git_blame(path, line_start, line_end, at)` | At most **200 lines** (ADR-0018). |
| `grep_repo(pattern, paths, max_hits=100, at)` | Implemented with `git grep`, on commit `at`, never the working tree (ADR-0018). |
| `symbolize(frame)` | Java/Kotlin only, using `stack_profile_*` tables and `--mapping`. Returns `null` for native frames. |
| `read_run_metadata()` | Available only when `--run-json` was passed. |

## Evaluation

- Run evals with a local runner, `evals/run_eval.py` (ADR-0016). `evalharness`
  (`pareto-eval`) was checked first. Its scorer and aggregator cannot express item 9's rates
  or repeated runs, and integrating would cost more than a day. The ADR records the gap.

## Not allowed

- A web UI, a database, LangChain, or a second model provider.
- Any runtime or test-time dependency on superPlayer or devicelab. Copy fixtures and code in
  instead; copying about 50 lines beats importing.
- Parsing trace protobufs directly.
