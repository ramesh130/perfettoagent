# `diagnose` on OpenAI: what the API confirmed, and what the loop settles

Issue #43 builds the OpenAI path that ADR-0020 decided on, and makes `gpt-5.6-luna` the default. ADR-0020 left three questions for this issue to check against the API. This ADR records the answers and the choices #43 made where ADR-0020 is silent. Affects `src/perfettoagent/agent.py`, `openai_loop.py`, `anthropic_loop.py`, `loop.py`, `models.py`, `credentials.py`, `diagnosis.py` and `cli.py`, `docs/tech-stack.md` ("Model and SDK") and roadmap item 7.

## What the API confirmed

Checked on 2026-09-25 with the user's key, loaded from `.env` inside a subshell and never printed.

- **`const` in strict schemas.** It is accepted. A request with a strict function tool whose parameter was `{"type": "string", "const": "secret"}`, and a strict `text.format` schema with a `const` property, completed. The model called the tool with the constant and answered with it. The schemas stay as ADR-0006 wrote them.
- **Tools and structured output in one request.** They combine. The same request carried the function tool and `text.format`. The first turn was a `function_call`, and the second, after its output, a `message` that matched the schema. So the answer is structured output on the turn with no tool call, as on Anthropic. There is no forced final tool call.
- **Usage fields.** OpenAI's `input_tokens` is the whole input. `input_tokens_details.cached_tokens` (read from cache) and `cache_write_tokens` (written to it) are parts of it. Two calls with the same 3,879-token prompt reported:
  - first call: 3,876 tokens written, 0 cached;
  - second call: 3,863 cached, 13 written, 3 neither.

  `run.usage` keeps Anthropic's shape (ADR-0006), where `input_tokens` is the uncached rest. So `openai_loop.usage_of` subtracts both parts, and each kind of token is priced at its own rate.

## The first live diagnosis passes the verifier

This is roadmap item 7's done criterion, carried from #29 (ADR-0022). On 2026-09-25, `gpt-5.6-luna` diagnosed eval case `462439ff`, the listener leak. The model was given the staged case, as the eval runner will give it, at effort `high`, the default.

| | |
|---|---|
| Verdict | `regression`, confidence `high` |
| Culprit | `6efb841e56d8`, attribution `direct`: the case's expected culprit |
| Metric | `heap_growth_objects_by_class`, the expected one: 432,751 → 434,935 reachable objects (+2,184), re-measured by `compute_metric` |
| Claims | 4 kept, 1 dropped. The dropped claim cited `6efb841e…2797`, a mistyped sha, which "names no commit" |
| Citations | 10 checked, 9 passed |
| Tool calls | 48 |
| Usage | 33 uncached input, 221,104 cache-read and 44,528 cache-written input, 8,663 output tokens |
| Cost and time | $0.026, 174 s |

The dropped claim is the verifier working: the model's other claims cite the right commit correctly. A second run, on the code as committed after review, gave the same verdict, culprit and metric: 4 claims kept, none dropped, 7 of 7 citations passed, 40 tool calls, $0.023, 136 s. Two runs say the path works end to end, not what the detection rate is. That is roadmap item 9's three-runs-per-case measurement. The live `claude-opus-5-5` run is deferred until an Anthropic key is available (#43's "Deferred" section).

## What the loop settles

- **One loop per provider, one run.** `agent.diagnose` owns everything the providers share:
  - the frozen prompt, the tools, the output schema and its check;
  - the metric re-measure and the verifier.

  Each loop (`AnthropicLoop`, `OpenAILoop`) only runs the conversation. It returns an `Ending`: the answer's text, or why there is none. `loop.py` holds what both loops share: the limits, the tool errors the model gets back (ADR-0022), `call_tool`, the cost tracker, and the wording of an ending with no answer. The Anthropic loop is #29's, moved, and behaves as before.
- **The history is replayed.** Every request replays the whole history, including the reasoning items with their `encrypted_content`. Requests set `store: false`, as ADR-0020 decided, and send no `previous_response_id`.
- **Tool errors on OpenAI.** A mistake the model can correct comes back as a `function_call_output` of `{"error": "<message>"}`. The Responses API has no `is_error` flag. The loop also checks what Anthropic's runner checks for it:
  - arguments that are not JSON, or not a JSON object;
  - a tool that does not exist.

  Each of these is an error the model reads, and the run continues. A failure of the run (ADR-0022) raises `RunFailed` before another request.
- **How an OpenAI response can end.** Each outcome is handled once and never retried:
  - `incomplete` at `max_output_tokens`: `inconclusive`, like Anthropic's `max_tokens`.
  - `incomplete` for another reason (`content_filter`, and so on): `inconclusive`, with that reason as a caveat.
  - A response that `failed`: the provider's error, not an answer. It raises `RunFailed`, and nothing is written.
  - A refusal: its text is the caveat's reason, collapsed to one line and cut at 300 characters, since OpenAI gives no category.
- **Turns.** `MAX_TURNS` (60) counts requests on OpenAI, as `max_iterations` does on Anthropic.
- **The long-context price is per request.** `gpt-5.6-luna`'s higher prices apply to a request whose whole input, cached or not, is above 272K tokens (ADR-0020). So each loop prices each response as it arrives, and `run.usd` is their sum, rounded once.
- **`run` records the provider, the model and the effort.** `diagnosis.json`'s `run` gains three required strings. Results from different models or levels are never pooled (ADR-0020), so a file must say which it is. This is an addition to schema 1, not a new version: no `diagnosis.json` existed outside tests before this change.
- **One refusal before any request.** `models.check_model` refuses three things, and the CLI exits 2:
  - a model with no price row;
  - a model named under the other provider (`--provider openai --model claude-opus-5-5`);
  - an effort the model does not list.

  The price table records each model's provider and its effort levels. Both models list `low`, `medium`, `high` and `xhigh`, the levels swept.
- **Credentials.** `credentials.api_key` reads `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` from the environment, else from `./.env`, and the environment wins. Only those two names are read from the file. The key goes to the SDK client and nowhere else. With no key, the SDK's own error names the variable. An Anthropic client with no key still falls back to an `ant auth login` profile. Reading `ANTHROPIC_API_KEY` from `.env` too is an addition to ADR-0020, which named `.env` for OpenAI's key only. An API error can quote a masked piece of the key it was sent (OpenAI's 401 does), so the CLI prints every error through `credentials.redact`, which removes the keys and anything shaped like one.
- **The default is flipped.** `--provider` defaults to `openai` and `--model` to the provider's own model, `gpt-5.6-luna` on OpenAI (ADR-0020).

## Consequences

- `docs/tech-stack.md` "Model and SDK" states the default as shipped and cites this ADR.
- **Roadmap item 7** moves to in progress. Its done criterion is met. What is left:
  - `diagnosis.md` (#30);
  - the `--run-json` rules (#31);
  - an `--effort` flag, which #44's sweep needs.
- The `openai` SDK (3.19.2) is a dependency. It shares `httpx2` with `anthropic`, and the tests fake it the same way: a real client over an in-process transport, in `tests/fake_openai.py`, playing the same scripts as the Anthropic fake. Most loop tests run once per provider.
