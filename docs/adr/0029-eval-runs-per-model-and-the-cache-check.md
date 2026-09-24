# Eval runs name their model and effort, are never pooled, and must read the cache

Issue #44 lets the eval runner run any priced model, so the sweep can compare `gpt-5.6-luna`, the headline, with `claude-opus-5-5` (ADR-0020). Its criteria are three: results never pooled across models, the scoring rules unchanged, and cache reads checked per provider from the second run on. This records how each is met. Affects `src/perfettoagent/evalrun.py`, `scoring.py` and `cli.py`, `docs/tech-stack.md` (Evaluation) and roadmap item 9.

## Decisions

- **`perfettoagent eval --provider --model --effort`,** checked by `models.check_model` before any run, as `diagnose` checks them (exit 2). The default results directory is `<model>-<effort>-<metric>`, and every `result.json` and `scores.json` records the provider, model, effort and metric choice. `--effort` is here, not in #49, because the sweep (#36) runs the eval, not `diagnose`.
- **Never pooled, by construction.** A results directory holds one model, effort and metric choice. A run found there with other settings stops the eval before any request: resuming into the wrong directory would otherwise mix two models' runs into one score. So every rate and cost is per model and effort level. The summary (#36) sets them side by side and never adds them together.
- **The scoring is unchanged.** `scoring.score` takes no model, and nothing in it depends on one.
- **The cache check.** Every run from the second repetition on that gave a diagnosis must have read cached tokens. `run.usage.cache_read_input_tokens` is already each provider's own field, mapped by its loop: Anthropic's `cache_read_input_tokens`, and OpenAI's `input_tokens_details.cached_tokens` (ADR-0023). So one check covers both. A run that read nothing is listed in `scores.json` (`cache.missing`) and in `scores.md`, and is not scored differently: a cold cache costs money, not correctness.
  - **"From the second run on" means the second repetition.** First runs may start cold, and with `--jobs` several of them run at once.
  - Within one run, every request after the first also reads its growing history from the cache. So a run with no cache read at all means the frozen prefix changed.

## The check on the first results

Re-scoring `gpt-5.6-luna-high-auto`: all 20 runs from the second repetition on read cached tokens.

## Consequences

- The live `claude-opus-5-5` runs wait for an Anthropic key. Their results would go in `claude-opus-5-5-<effort>-auto/`, beside `gpt-5.6-luna`'s, with nothing else to change.
