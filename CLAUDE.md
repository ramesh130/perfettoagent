# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Spec-driven development

The product is defined by three docs:
- `docs/mission.md`: what and why, goals, principles, non-goals. @docs/mission.md
- `docs/tech-stack.md`: tools, pins, SDK rules, agent tool limits, what's forbidden. @docs/tech-stack.md
- `docs/roadmap.md`: features in build order, with done criteria and open questions. Read it
  before starting any feature.

Workflow for each roadmap item:
1. The item's GitHub issue is its spec (ADR-0003): its acceptance criteria are the tests.
2. Implement on the item's issue branch (`issue-<number>-<short-slug>`). The PR body records
   the interfaces it introduces and argues any decision the issue leaves open.
3. When done, flip the item's status in `docs/roadmap.md`.

Diverging from these docs is fine; silent divergence is not. Log every divergence and every
settled open question by recording an ADR in `docs/adr/` (`NNNN-slug.md`, next number),
then update the affected doc to cite it.

## Hard rules

- **No uncited claims.** The verifier (roadmap item 4) is deterministic Python. It is never
  replaced by a prompt instruction and never skipped. If it's slow, cache SQL results by hash.
- **Nothing in the README may claim a number that `evals/results/` does not contain.**
- Eval integrity: case dirs are opaque IDs. Never name the planted regression in any prompt,
  path or fixture the model sees. Never score on the model's confidence field. Run each case
  3 times and report the spread.
- The target app repo is read-only, through `git` subprocess calls only.

## Agent skills

### Issue tracker

GitHub Issues on ramesh130/perfettoagent via `gh`, with native blocked-by dependencies. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `CONTEXT.md` (created lazily) plus ADRs in `docs/adr/`. See `docs/agents/domain.md`.
