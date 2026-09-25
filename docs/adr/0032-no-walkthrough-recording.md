# No walkthrough recording

Roadmap item 11 (#37), the Phase 2 exit and v1's definition of done each asked for a
two-minute walkthrough recording, from trace in to diagnosis out, linked from the README. The
project owner dropped it. This is a divergence from the roadmap, so it is recorded here.
Affects `docs/roadmap.md` (the Phase 2 exit, item 11 and the definition of done), `README.md`
and issue #37.

## Decision

- **No recording.** The README shows the same path in text instead:
  - the kinds of regression the tool is for;
  - the head of a real `diagnosis.md` from an eval run, linked in full;
  - the eval table from `evals/results/summary.md`;
  - the commands that produce each of them.
- **Item 11 is done, and so is v1.** The README and `docs/postmortem.md` are written from
  `evals/results/`, and #37's remaining criteria are met.

## Consequences

- The README no longer promises a recording.
