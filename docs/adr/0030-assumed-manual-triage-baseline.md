# An assumed manual-triage baseline, until #27 measures one

Roadmap item 9 compares the agent's time to diagnosis with timed manual triage of the same five planted superPlayer cases (#27). That triage needs a person at the keyboard, and it has not been done. The project owner directed that the sweep (#36) go ahead with an assumed number rather than wait. That is a divergence from the mission's "measured numbers are the deliverable", so it is recorded here. Affects `evals/results/manual-triage/` and roadmap item 9.

## Decision

- **Assumed: 60 minutes a case, culprit found**, for each of the five planted superPlayer cases, in `evals/results/manual-triage/triage.json` with `"measured": false` and the reason.
- **Why that number.** The mission puts the manual path at "hours". Taking the low end means the comparison can only understate the agent's speed-up, never inflate it. Assuming the culprit is always found likewise favours the manual side.
- **Labelled wherever it is used.** `summary.md` and the README call it assumed, next to the number, and never "measured". CLAUDE.md's rule that every README number comes from `evals/results/` still holds: this file is there, and says what it is.

## Consequences

- #27 stays open. When it is done, measured times replace the file, `measured` becomes true, and the time-to-diagnosis comparison is regenerated.
