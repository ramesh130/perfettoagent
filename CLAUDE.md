# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

Greenfield. `PRD.md` is the spec; nothing is built yet. **Read `PRD.md` in full before any
feature work**, and treat it as the source of truth unless `docs/decisions.md` records a
divergence.

## Hard rules (from PRD §6, §8, §9.3, §12)

- **No uncited claims.** Every claim in `diagnosis.json` cites a trace SQL or a commit. The
  verifier (`verifier.py`, PRD §8.4) is deterministic Python that re-runs cited SQL and checks
  commits are in range. It is never replaced by a prompt instruction and never skipped for
  speed — cache SQL results by hash instead.
- Traces are read only via the pinned `trace_processor_shell` **58.2** (sha256-verified,
  cached in `~/.cache/perfettoagent`, `TRACE_PROCESSOR` override). Never parse the protobuf
  in-repo. Refuse a mismatched archive.
- The target app repo (`--repo`) is read with `git` subprocess calls only; never write to it.
- `query_trace` accepts only `SELECT`/`WITH`, caps rows at 200 in our code, and reports the
  true `row_count`.
- Use Perfetto stdlib modules (`INCLUDE PERFETTO MODULE …`) for startup/frame metrics rather
  than re-deriving; name the module in `sql_used`.
- Eval integrity: case dirs are opaque IDs; never name the planted regression in any prompt,
  path, or fixture the model sees; never score on the model's confidence field; run each
  case 3× and report the spread.
- **Nothing in README may claim a number that `evals/results/` does not contain.**
- No runtime or test-time dependency on superPlayer/devicelab — copy fixtures and code in
  (prefer copying ~50 lines over importing).
- Forbidden: web UI, database, LangChain, a second model provider, secrets in the repo.

## Anthropic SDK usage

- Use the `claude-api` skill for SDK details, not memory — the API surface changed in 2026.
- Model: `claude-opus-5-5` (diverges from PRD; see `docs/decisions.md`). No date suffixes.
- Agent loop via beta Tool Runner (`client.beta.messages.tool_runner` + `@beta_tool`); do not
  hand-write the `stop_reason == "tool_use"` loop. Tools use `strict: true`,
  `additionalProperties: false`.
- Stream every request; `max_tokens` 64000 on the agent loop; check `stop_reason` for
  `max_tokens` and `refusal` before reading content. A refusal becomes an `inconclusive`
  verdict with its category — never retry in a loop.
- Structured output via `output_config.format`, then re-validate locally. No assistant prefill,
  no forced `tool_choice`.
- Frozen system prompt with a `cache_control` breakpoint; volatile inputs go in the first user
  message.

## Tooling

- Python 3.12, `uv`, `ruff`, `pytest`. `pytest` must pass with no network access.
- API key from `ANTHROPIC_API_KEY` or an `ant auth login` profile.

## Workflow

- Work is tracked in GitHub Issues; branch per issue as `issue-<number>-<short-slug>`.
- Diverging from the PRD is fine; silent divergence is not. Log every divergence and every
  settled open question (PRD §13) in `docs/decisions.md` — use `/decision`.
