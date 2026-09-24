# `review` records answers by content, and `diagnosis.json` records its inputs by hash

Issue #32 adds `perfettoagent review <out-dir> accept | reject <reason> | partial <claim-ids>` (roadmap item 10), which appends each answer to `evals/feedback.jsonl` "with hashes of the inputs (both traces, range, diagnosis)". Two things were open: where the trace hashes come from, since `review` is given only an output directory, and what `partial` names. Affects `src/perfettoagent/review.py`, `diagnosis.py`, `agent.py` and `cli.py`, and roadmap item 10.

## `diagnosis.json` records its inputs by content

`run` gains `inputs`: `baseline_sha256`, `current_sha256` and `range`, the range as the full shas `diagnose` resolved. `diagnose` fills it and the model never sees it.

- **Why at diagnose time.** The traces may have moved or been deleted by the time someone reviews. Hashing takes about 15 ms for a 23 MB trace (ADR-0006). `review` then needs nothing but the output directory, and never reads a trace or the target repo.
- **Never a path.** A path can say what a run was about (ADR-0022), and a hash names the bytes wherever they are. An eval case's traces hash the same wherever they are staged, so a rejected diagnosis can be matched back to its case.
- **Schema 1, extended.** `run` is required and strict, so a `diagnosis.json` written before this change no longer validates. As with ADR-0023's `provider`, `model` and `effort`, no such file exists outside tests: the live runs' outputs were scratch files. The first eval results (#33) are written after this change.

## A feedback line

One JSON object per line, schema 1:
- `reviewed_at`, `answer` and `reason` (for `reject`, else null);
- `claims_accepted` and `claims_rejected`, as claim ids;
- `inputs`: the diagnosis's `run.inputs` plus `diagnosis_sha256`, the sha256 of the `diagnosis.json` bytes reviewed;
- `diagnosis`: the verdict, culprit, metric name, provider, model and effort, so the file can be read without the diagnosis at hand.

## What each answer means

- `accept`: every kept claim is right.
- `reject <reason>`: the diagnosis is wrong. A reason is required; it is what makes a rejection usable as a candidate eval case.
- `partial <claim-ids>`: the named claims are right and the other kept claims are not. Naming every kept claim, or none, is refused (use `accept` or `reject`). So is an id the diagnosis does not have, and so is the id of a dropped claim: the verifier removed it, so it was never presented as a finding.
- A `diagnosis.json` with `run: null` (a re-verification outside an agent run) is refused, because nothing in it names the traces.

## Consequences

- Roadmap item 10 is done.
- `review` writes only the feedback file. It never edits the diagnosis, never reads the target repo, and makes no network call. A test checks that the feedback file is the only file it creates or changes.
