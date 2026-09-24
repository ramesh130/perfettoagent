# Agent tools are plain functions with hand-written strict schemas

Issue #24 adds the first agent tools, the four git tools, and leaves open how a tool's schema is declared. `symbolize` (#25) and the agent loop (#29) follow whatever is chosen here, so it is recorded. It also settles three details of the tool surface that `docs/tech-stack.md` did not. Affects `src/perfettoagent/tools.py`, `src/perfettoagent/repo_tools.py`, `src/perfettoagent/git.py` and `docs/tech-stack.md` ("Model and SDK", and the tool table).

## Declaring a tool: a `Tool` beside a plain function

The two options were:

- **The SDK's `@beta_tool` on each function**, with the schema generated from its signature and docstring. This adds the `anthropic` dependency now.
- **A plain function, and next to it a hand-written schema dict**, which the agent loop (#29) wraps.

Hand-written, for these reasons. They come from reading `anthropic` 0.122.0's `lib/tools/_beta_functions.py`:

- **The generated schema is not strict.** `beta_tool(strict=True)` adds `strict: true` to the tool definition, but the `input_schema` comes from pydantic's JSON schema of the signature. That schema has no `additionalProperties: false`, and it adds `title` and `default` keys, which `docs/tech-stack.md` does not ask for. Getting a strict schema from `@beta_tool` means passing `input_schema=` anyway.
- **`beta_tool(func, input_schema=..., strict=True)` sends a hand-written dict unchanged.** So choosing hand-written schemas does not rule out the Tool Runner. #29 still uses it, as `docs/tech-stack.md` says. It passes each `Tool`'s schema and description to `beta_tool` instead of letting it generate them.
- **The schema is data we can test without the SDK.** The tests check that each schema is strict, lists every property as required, and matches the function's parameters. They run with no `anthropic` import. The dependency arrives with #29, the first code that calls the API.
- **One schema subset, one validator.** Tool schemas use the JSON Schema subset that `diagnosis.validate` interprets (ADR-0006). That is also the subset strict tool use supports: no `minimum`, `maximum` or string lengths. `Tool.call` validates the model's arguments against the schema before the function runs. For a hand-written schema, the SDK checks only as far as the function's type hints go.

So a tool is a `perfettoagent.tools.Tool`, with a `name`, a `description`, an `input_schema` and a `function(context, **arguments)`, and the function returns a JSON-serialisable dict. `context` is what the run binds and the model never names: the target repo's path for the git tools, and the trace for `symbolize`. `Tool.definition()` is the Messages API's tool dict, with `strict: true`.

## Optional arguments are required and nullable

Like the diagnosis output schema, every property is required, and an optional one is `anyOf [..., null]`, where null means "the default". The model always says what it wants, and there is one convention across the model's inputs and its output.

## Caps are ceilings, and each result says when one applied

- `max_lines` (400) and `max_hits` (100) are the defaults. They are also the most a call returns: a larger value is lowered to the cap, and the description says so.
- `git_blame` gets a cap that `docs/tech-stack.md` did not set: 200 lines, the size of a `query_trace` result.
- Each capped result has `truncated`, and the true total (`commit_count`, `line_count`, `hit_count`) whether it was cut or not.

## `grep_repo` takes `at`

`docs/tech-stack.md` had `grep_repo(pattern, paths, max_hits=100)`. A grep must read a commit, not the working tree. The working tree is whatever was last checked out, and neither trace need match it. So `grep_repo` gains `at`, the commit to search, as `git_blame` already has. The model gives the range's head, or its base to compare.

## `git blame` gets no `--end-of-options`

`perfettoagent.git`'s rule is `--end-of-options` before revisions and `--` before paths. Under git 2.50, `git blame --end-of-options <rev> -- <path>` no longer treats `--` as the end of revisions. It hands the path to the revision parser, so a path of `--output=<file>` wrote that file. The blame call leaves `--end-of-options` out. Its revision is always a full hex sha, resolved first, so it can never be an option anyway. A test tries each of five option-shaped strings as a pattern, a path and a revision on every tool, and checks that nothing was written.

## Consequences

- `symbolize` (#25) declares a `Tool` in the same way, with the trace as its context.
- #29 adds `anthropic`, wraps each `Tool` in `beta_tool(..., input_schema=tool.input_schema, strict=True)`, and returns each result as JSON. A `ToolInputError` or a `GitError` becomes an error `tool_result` the model can read and correct.
- `docs/tech-stack.md` cites this ADR for how tools are declared, for `grep_repo`'s `at` and for `git_blame`'s cap.
