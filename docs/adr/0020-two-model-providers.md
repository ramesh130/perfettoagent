# Two model providers, a `--model` flag, and `gpt-5.6-luna` as the default

Supersedes ADR-0001. `docs/tech-stack.md` banned a second model provider and pinned one model, `claude-opus-5-5`. Issue #42 changes that. `diagnose` and the eval runner support two providers, Anthropic and OpenAI, and the model is chosen per run. OpenAI's `gpt-5.6-luna` becomes the default for `diagnose` and the headline model in the eval table. `claude-opus-5-5` stays available as a compared variant. This ADR is the decision and the rules. The code comes in #43 (`diagnose` on OpenAI) and #44 (model variants in the eval runner). Affects `docs/tech-stack.md` ("Model and SDK", "Not allowed") and `docs/roadmap.md` items 7 and 9.

## The CLI surface

- `--provider {anthropic,openai}` picks the SDK. `--model <id>` picks the model, and each provider has a default model: `gpt-5.6-luna` for `openai`, `claude-opus-5-5` for `anthropic`.
- The default provider is `openai`. It becomes the default only when #43 ships. Until then `anthropic` / `claude-opus-5-5` is the only working path, and it is the default. So the `diagnose` tracer bullet (#29) is built as its issue describes, on the Anthropic SDK.
- A model id is sent as given, with no date suffix. A model that has no row in the price table (below) is refused before any request, so every run can record its USD. Adding a model means adding its price row, with a source and a date.
- `diagnosis.json` and each eval result record the provider, the model and the effort level. Results from different models are never pooled (#44).

## The model id was checked

`gpt-5.6-luna` is a real model id. On 2026-09-24 at 10:57 UTC it was checked with the user's OpenAI key, loaded from the git-ignored `.env` inside a subshell and never printed:

- `GET https://api.openai.com/v1/models/gpt-5.6-luna` returned `{"id": "gpt-5.6-luna", "object": "model", "owned_by": "system", "created": 1782228658}` (2026-06-23) and no error.
- `GET https://api.openai.com/v1/models`, filtered for `luna` and `gpt-5.6`, listed `gpt-5.6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra` and `gpt-6-luna`.

## The Responses API, not Chat Completions

The OpenAI path uses the Responses API (`client.responses.create`). Chat Completions still works for `gpt-5.6-luna`, but:

- OpenAI's reasoning guide says reasoning models "work better with the Responses API", with "improved model intelligence and performance".
- The `openai-python` README calls Responses "the primary API", and says Chat Completions stays supported.
- Reasoning items carry `encrypted_content`, so the loop can replay a turn's reasoning without keeping state on OpenAI's servers (see the last note under the table).

## How each provider meets the SDK rules

`docs/tech-stack.md` "Model and SDK" had one rule set, written for Anthropic. Each rule holds for both providers. The sources are the `claude-api` skill and Anthropic's docs for Anthropic, and OpenAI's own docs (below) for OpenAI. None is from memory.

| Rule | Anthropic | OpenAI (Responses API) |
|---|---|---|
| The loop | Beta Tool Runner, `client.beta.messages.tool_runner` with `beta_tool`, as before. | The `openai` SDK has no tool runner, so the loop is written by hand: run each `function_call`, send back a `function_call_output` with the same `call_id`, repeat until no call is left. |
| Streaming | `messages.stream`, as before. | `responses.create(stream=True)`. Argument text arrives as `response.function_call_arguments.delta` events. |
| Strict tool schemas | `strict: true` on each tool, schema from `Tool.input_schema` (ADR-0018). | `{"type": "function", "name", "description", "parameters", "strict": true}`, with the same `Tool.input_schema` unchanged as `parameters`. |
| Structured output | `output_config.format`. | `text.format` with `type: "json_schema"`, `strict: true` and the same `OUTPUT_SCHEMA`. |
| Local validation | `diagnosis.validate` again on the result, and `Tool.call` on every tool input (ADR-0006, ADR-0018). | The same two checks. They do not change with the provider. |
| Effort | `output_config.effort`. | `reasoning.effort`. See the mapping below. |
| Output cap | `max_tokens` 64000. | `max_output_tokens` 64000. It counts reasoning tokens too. |
| Truncated output | `stop_reason == "max_tokens"`, checked before reading content. | `status == "incomplete"` with `incomplete_details.reason == "max_output_tokens"`, checked before reading output. |
| Refusal | `stop_reason == "refusal"`, and `stop_details.category`. | An output content item of `type: "refusal"`, with its text. It carries no category. |
| Frozen, cached system prompt | The frozen prompt carries a `cache_control` breakpoint. | The frozen prompt is the first `developer` input item. GPT-5.6 caches the prefix by default (implicit mode). |
| A cache hit shows as | `usage.cache_read_input_tokens` > 0. Writes are `usage.cache_creation_input_tokens`. | `usage.input_tokens_details.cached_tokens` > 0. Writes are `usage.input_tokens_details.cache_write_tokens`. |
| Tool choice | `auto`. Forced choice returns a 400 on Opus 5.5. | `tool_choice: "auto"`. `required` and a named function exist, and are not used. |
| Prefill | Not used; it returns a 400. | Not applicable. |

Four notes on the table:

- **The schemas fit both strict modes.** The tool and output schemas use nine keywords (ADR-0006): `type`, `enum`, `const`, `anyOf`, `properties`, `required`, `additionalProperties`, `items` and `description`. Every property is required and every object has `additionalProperties: false` (ADR-0018). That is what OpenAI's strict mode asks for. Its function-calling guide shows an optional field as a `type` array; `anyOf [..., null]`, used here, is in its supported list. OpenAI's structured-output guide rejects `minimum`, `maximum` and `maxLength`, which the schemas already leave out. The pages checked do not list `const`. #43 confirms it against the API. If it is refused, a `const` becomes a one-value `enum`, which the validator already reads.
- **Tools and structured output in one request.** The pages checked do not say whether `text.format` and function tools can be combined in one Responses call. #43 checks it first. If they cannot, it records the answer in a new ADR before choosing a workaround, since a forced final tool call would break the no-forced-choice rule.
- **The cache.** Implicit mode is used, not explicit breakpoints. It also caches the growing loop history, and in explicit mode a request with no breakpoint is not cached at all. The prefix includes the tool definitions and the `text.format` schema, so both must be byte-for-byte the same on every run. Volatile inputs (paths, range, run metadata) go after the frozen prompt, in the first user item, as before. GPT-5.6's minimum cacheable prompt is 1,024 tokens. The cache check from the second eval run on is per provider: `cache_read_input_tokens` for Anthropic, `cached_tokens` for OpenAI.
- **The loop keeps no server state.** Requests set `store: false` and ask for each reasoning item's `encrypted_content`. Each turn replays every output item, reasoning items included, then the tool outputs. This is the same append-only history as the Anthropic path. `previous_response_id` would keep the run's history on OpenAI's servers.

## Refusals and truncation

On either provider a refusal becomes an `inconclusive` verdict and is never retried. The Anthropic path records `stop_details.category`. The OpenAI path records a null category and the refusal text as the reason. A truncated output also becomes `inconclusive`, with `max_tokens` or `max_output_tokens` as the reason, and is not retried either.

## The effort mapping

`--effort` keeps its four levels, and the default stays `high`. The value is always sent, never left to the API's default. That matters because both default models default to `medium`: Opus 5.5 per the `claude-api` skill, and `gpt-5.6-luna` per its model page.

| `--effort` | Anthropic `output_config.effort` | OpenAI `reasoning.effort` |
|---|---|---|
| `low` | `low` | `low` |
| `medium` | `medium` | `medium` |
| `high` | `high` | `high` |
| `xhigh` | `xhigh` | `xhigh` |

`gpt-5.6-luna`'s model page lists `none`, `low`, `medium`, `high`, `xhigh` and `max`, so all four map one to one. `none`, `minimal` and `max` are not swept. A level a model has no equivalent for is refused before any request, with an error naming the levels that model supports. It is never rounded to a nearby level, so a cost row always means the level it names. The price table (below) records the levels each model supports, and the sweep runs each model at every level it has.

## Prices

USD per million tokens, standard tier, as each provider's own page gave them on 2026-09-24.

| Model | Input | Cache write | Cache read | Output | Source |
|---|---|---|---|---|---|
| `gpt-5.6-luna` | $0.20 | $0.25 | $0.02 | $1.20 | [OpenAI pricing](https://developers.openai.com/api/docs/pricing), [model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna) |
| `claude-opus-5-5` | $4.00 | $5.00 (5-minute) | $0.20 | $20.00 | [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing) |

- `gpt-5.6-luna` charges more above 272K input tokens: $0.40 input, $0.50 cache write, $0.04 cache read and $1.80 output. #43 prices a request over that line at those rates.
- OpenAI bills reasoning tokens as output tokens (`output_tokens_details.reasoning_tokens` is part of `output_tokens`).
- Opus 5.5's cache read is 0.05× its input price, not the usual 0.1×. Its 1-hour cache write ($8.00) is not used.
- The prices go in one table in the code, keyed by model id, with the source URL and the date checked on each row. #43 derives the uncached input count from each provider's usage fields and checks the result against one recorded response's billed usage before trusting it.

## Credentials

- `ANTHROPIC_API_KEY`, or an `ant auth login` profile, as before.
- `OPENAI_API_KEY`, from the environment or from a `.env` file in the working directory. `.env` is in `.gitignore`. A variable already set in the environment wins over `.env`. Only these two names are read from it. A small stdlib reader does this; `python-dotenv` would add a dependency for about ten lines.
- Neither key is ever logged, printed, put in an error message or written to `diagnosis.json`, `diagnosis.md` or `evals/results/`. A run records the provider and the model, not where the key came from.
- Tests use neither key and no network. `--disable-socket` stays on, and the OpenAI loop is tested with a faked client, as the Anthropic one is.

## Sources checked on 2026-09-24

- Anthropic: the `claude-api` skill (models, effort defaults, forced tool choice, caching fields, stop reasons) and https://platform.claude.com/docs/en/about-claude/pricing.
- OpenAI:
  - https://developers.openai.com/api/docs/models/gpt-5.6-luna
  - https://developers.openai.com/api/docs/pricing
  - https://developers.openai.com/api/docs/guides/reasoning
  - https://developers.openai.com/api/docs/guides/function-calling
  - https://developers.openai.com/api/docs/guides/structured-outputs
  - https://developers.openai.com/api/docs/guides/prompt-caching
  - https://github.com/openai/openai-python (README)

## Consequences

- ADR-0001 is superseded. Its rule that an older model swept for comparison is a separate variant still holds, for every model.
- `docs/tech-stack.md` lists both SDKs and drops "a second model provider" from "Not allowed". A third provider would need its own ADR.
- #43 adds the `openai` dependency, the OpenAI loop and the price table, and flips the default. Until it merges, the tech stack's default stays `anthropic` / `claude-opus-5-5`.
- #44 records the provider, model and effort in every eval result, and reports every rate and cost per model and effort level.
- The Anthropic path keeps the Tool Runner. The OpenAI path has a hand-written loop, because its SDK has no runner. Both share the tools, the prompt, the output schema, the validator and the verifier.
