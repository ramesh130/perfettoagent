# Decisions

ADR-style log. One entry per non-obvious choice or divergence from `PRD.md`. Newest last.

## D1 — Model ID `claude-opus-5-5` instead of `claude-opus-5`

- **Date:** 2026-09-23
- **PRD section:** §8.1 Stack
- **Context:** The PRD pins `claude-opus-5`. The current Opus model is `claude-opus-5-5`.
- **Decision:** Use `claude-opus-5-5` as the default agent model.
- **Why:** Latest and most capable Opus; the PRD predates it.
- **Consequences:** Cost/quality figures in the eval table are for `claude-opus-5-5`. If an
  older model is swept for comparison, record it as a separate variant.
