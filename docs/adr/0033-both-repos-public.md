# Both repositories are public

ADR-0021 put JetNews's plants and captures in a private repo, `ramesh130/jetnews-perf`, and this repo was private too. At the project owner's direction, both are now public, with descriptions and topics so that search engines and GitHub search can find them. Affects `docs/roadmap.md` (item 8), `README.md` and `evals/build_jetnews_cases.py`, which called jetnews-perf private.

## What was checked first

A repo made public publishes its whole history, so both histories were scanned first:
- **Secrets:** no key-like string (the only matches are fake values in tests), and no `.env` ever committed.
- **Private material:** no `PRD.md`, `CLAUDE.local.md` or career material in any commit, no local paths, and no provider org id.
- **The one sensitive-looking file,** `JetNews/debug_2.keystore`, is the Android debug keystore from Google's public `android/compose-samples`, byte-identical to upstream's.
- **superPlayer's source,** which this repo's fixture bundle snapshots and whose devicelab jetnews-perf's harness adapts, is already public.

## What becomes readable

- **The eval answers.** `evals/answers/` and the plant patches were always kept apart from what the model sees (ADR-0015). A model is never given this repo, so publishing the answers changes nothing for the eval. A future model trained on the public repo could have seen them, though. Results from such a model should be read with that in mind, and a fresh set of cases would be the fix.
- **jetnews-perf's commit messages and `plants/`,** which name each plant, as ADR-0021 said.
