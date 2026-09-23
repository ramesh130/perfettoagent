# `diagnosis.json` schema 1, and what the verifier's rules mean exactly

Issue #4 builds the verifier (roadmap item 4) and defines `diagnosis.json` schema 1 (roadmap item 7 lists its fields). Both are hard to change once diagnoses and eval results exist, so their shape and the exact meaning of each rule are recorded here. Affects `docs/roadmap.md` (items 4 and 7) and `src/perfettoagent/diagnosis.py`, `verify.py` and `git.py`.

## The schema

- **Defined once, as JSON Schema, in `perfettoagent.diagnosis`.** There are two schemas. `OUTPUT_SCHEMA` is what the model writes, and it is strict enough to pass to the API's `output_config.format` unchanged: every object has `additionalProperties: false`, every property is required, and an optional value is `anyOf [..., null]`. `DIAGNOSIS_SCHEMA` is the file we write.
- **The model fills** `verdict`, `metric`, `confidence`, `culprit`, `claims` (text and citations) and `caveats`. **Our code fills** `schema_version`, each claim's `id`, each citation's result (`row_count` or the resolved `commit`, and `error`), `dropped_claims`, `verification` and `run` (tool calls, usage, USD, wall time). None of the code-filled fields are in `OUTPUT_SCHEMA`, so a model that pre-fills one fails validation. It cannot be trusted by accident.
- **The validator is stdlib.** It is about 60 lines that interpret the nine JSON Schema keywords the schemas use, and it refuses any other keyword so that one can't be silently ignored. The API's structured outputs support that same subset. `jsonschema` would add a dependency and its own dependencies for the same check. `pydantic` would add a second definition that has to be kept in step with the JSON Schema the API needs.
- A trace citation is `{kind: "trace", trace: current|baseline, sql}`, and `sql` may start with `INCLUDE PERFETTO MODULE` lines (ADR-0005). A commit citation is `{kind: "commit", sha, path|null}`. The metric carries its `sql_used`. `confidence` is `low|medium|high`, because nothing is ever scored on it.

## The rules

- **Trace citations: runs and returns ≥ 1 row, and nothing more.** The rule says only that. Comparing a number the model wrote with the rows would need a citation shape that names a column and a tolerance, which is one more thing for the model to get wrong. The fresh `row_count` is recorded so that a reader, or a later stricter rule, can check. The metric's `sql_used` is checked the same way on each side it reports a value for. If it fails, `metric` becomes null and the reason goes in `verification.metric_dropped`.
- **Inside `base..head`** means what `git log base..head` lists: an ancestor of `head` (or `head` itself) that is not an ancestor of `base` (or `base` itself). Each is checked with `merge-base --is-ancestor`. The endpoints may be any revision. A citation's sha must be 7–64 lower-case hex digits, is resolved with `cat-file --batch-check` on stdin, and an ambiguous prefix fails, as does a ref named like the prefix that resolves to a commit not starting with it.
- **"Touches `path`"** means `git diff --name-only` against the commit's first parent lists a file at or under `path`. For a root commit the diff is against the empty tree. For a merge it is what the merge brought into the branch it merged into. `--literal-pathspecs`, `--end-of-options` and `--` stop citation text from ever being read as an option or as pathspec magic.
- **Culprit.** It survives only if a surviving claim has a commit citation that resolves to the same full sha, so short and full shas match.
- **Verdict.** If no claim survives, the verdict becomes `inconclusive` and `verification.explanation` says why. `metric` stays if it passed its own check, because a measured change with no attributable cause is still worth reporting. `confidence` becomes null whenever the verifier changes the verdict or drops the culprit, because the model's confidence was in a diagnosis that no longer stands. `verification.verdict_before` keeps the model's verdict, and `citations_checked` and `citations_passed` give the roadmap item 9 "citation validity" figure.
- **Failures of the run are errors, not verdicts.** A malformed range, an unreadable repo, git that cannot run or times out, a missing trace or a missing trace processor raises. None of these may look like a model that cited nothing. A cited query that times out (300 s) does fail its citation, since a runaway query is the citation's own doing, and that failure is never cached.

## Caching

Re-running a keyed metric's citation takes about 3.3 s per trace on the 23 MB heap dumps. A realistic diagnosis (the metric plus four claims) took 10.8 s to verify. Every eval case is run 3 times across 4 effort levels, and each run re-verifies the same citations on the same traces. So results are cached: within one call by (trace, SQL), and on disk when the caller passes `cache_dir` (the agent's is `~/.cache/perfettoagent/verified-queries`). The key is the sha256 of the trace's bytes, the trace processor's bytes, the statement and the modules. A changed input gets a new key, so an entry can't go stale, and hashing both files takes about 15 ms. Only a successful run's row count is cached, never a failure. A warm verify of the same diagnosis took 0.1 s.

## Consequences

- Roadmap item 7 passes `OUTPUT_SCHEMA` as `output_config.format`, calls `verify(..., run=..., cache_dir=QUERY_CACHE_DIR)`, and writes what it returns. It should fill `metric` from `compute_metric` rather than trust the model's copy.
- `culprit.files` are not checked against the culprit's diff. A later rule may add that.
