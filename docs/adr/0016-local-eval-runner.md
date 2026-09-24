# evalharness cannot score these runs (Q2), so the eval runner is local

Open question Q2 asked whether `evalharness` (`pareto-eval`) accepts a per-case tool-call transcript as a quality input, or whether this repo needs a local runner. It blocks roadmap item 9, and `docs/tech-stack.md` allows a local runner if integrating costs more than a day. The answer is a local runner, `evals/run_eval.py`. Its scorer sees a transcript but not its results, and it turns a run into one number per task, where item 9 needs several rates over different denominators. What it lacks for item 9 would take two to three days of changes, most of them in `evalharness` itself. Affects `docs/roadmap.md` (Q2), `docs/tech-stack.md` (Evaluation) and roadmap item 9.

## What was checked

`evalharness` was read at commit `7801443` (version 0.1.0), without changing it. The scorer interface was then called from a throwaway script outside both repos, using that repo's own environment:
- `pareto_eval.scorers.Scorer` is `Callable[[Output, Mapping[str, Any]], float]`.
- `Output` (in `types.py`) has two fields: `text` and `tool_calls`.
- `score_with("tool_call", …)` on a three-call transcript returned `1.0`.
- `score_with("diagnosis", …)` raised `unknown scorer 'diagnosis'`.
- `aggregate()` on three rows for one case raised `duplicate rows for task(s)`.
- `provider_for_model("claude-opus-5-5")` raised `no provider prices model`.

## What in the scorer interface decided it

- **A transcript without results.** `Output.tool_calls` is a tuple of `ToolCall(name, arguments)`. It holds no tool results, no order of turns and no stop reason. `runner.run_suite` builds one `Request` per task and calls `Provider.complete` once. Its providers send one user message, and nothing runs a tool and returns its result. So a whole diagnosis could reach a scorer only by wrapping the agent loop in a custom `Provider` and returning the final `diagnosis.json` as `text`.
- **Only the built-in scorers.** `SCORERS` in `scorers/__init__.py` is a closed dict: `exact_match`, `tool_call` and `llm_judge`. `suite.py` checks names against it at load time, so a suite cannot name a scorer of its own. `tool_call.score` answers one question: did some call match `expected_tool` and `expected_args`? That is not attribution. The culprit is in the diagnosis, not in a tool's arguments.
- **One float per task.** A scorer returns one float. `aggregate.aggregate` makes `quality` their mean, `cost_usd` their sum and `latency_p95_ms` their 95th percentile. Item 9's rates do not share a denominator:
  - detection counts planted cases;
  - attribution counts only the detected ones;
  - the false-positive rate counts clean pairs;
  - citation validity counts citations, not cases.
  A mean over all cases gives none of them.
- **One run per case.** `aggregate._reject_duplicate_tasks` refuses a second row for the same task. Item 9 runs every case three times and reports the spread. `evalharness`'s own `ROADMAP.md` and `docs/eval-framework.md` list repeated runs as not built.

## The gap it leaves

A local runner has to do each of these, and `evalharness` does none of them today:
- run the Tool Runner loop per case, streamed, with `max_tokens` 64000 (`AnthropicProvider` calls `messages.create` without streaming and refuses `max_tokens` above 16000);
- stage each case with `CaseInputs.stage` (ADR-0015), because a `Task.input` is a single string;
- score from `load_expected` and the verifier's output, and not from the model's confidence field;
- compute detection, attribution and false-positive rates and citation validity, each over its own denominator;
- run each case three times and report the spread;
- record USD, input, output and cache-read tokens per effort level. `evalharness` does carry cache counters on `Completion`, but its price table has no `claude-opus-5-5`.

Two things it does fit. Per-row cost, tokens and latency map onto `RunResult`. Its task files hold the expected answers, but the runner sends only `Task.input` to the model, so answers would not leak. A suite would still have to be generated from `evals/answers/`, to keep the answers apart (ADR-0015).

## What integrating would cost

An estimate, not a measurement:
- a `Provider` that runs `diagnose` on a staged case: half a day;
- in `evalharness`, a way to register a scorer from outside, repeated runs per task with their spread, several quality rates per point, and a `claude-opus-5-5` price entry: about two days, and each is a change to another project, reviewed there;
- pinning it (below): an hour.

That is well past the one-day limit. And what would still come from `evalharness` is a loop over tasks and a JSONL file, which the local runner needs anyway.

## How it would have been pinned

`pareto-eval` is public on GitHub (`ramesh130/pareto-eval`, MIT) but not on PyPI. A pin would be a git dependency at a commit sha in `pyproject.toml`, locked in `uv.lock`. `uv sync` would fetch it from GitHub, and the tests would still run with `--disable-socket` once it was installed. A path dependency on a sibling checkout would break a standalone clone. The tech stack's ban on superPlayer and devicelab does not cover `evalharness`, so nothing forbids it. It is simply not worth it now.

## Consequences

- Roadmap item 9 writes `evals/run_eval.py`. `docs/tech-stack.md` gains no dependency.
- **Revisit** if `evalharness` gains custom scorers, repeated runs and several quality rates per point. Then the runner could hand it its rows. Its Pareto frontier over (quality, cost, latency) would fit the effort-level sweep.
