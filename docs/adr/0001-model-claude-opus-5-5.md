# Use `claude-opus-5-5` as the agent model

**Status: superseded by ADR-0020.** There are now two providers, and the model is chosen per run. `claude-opus-5-5` stays available as a compared variant, and `gpt-5.6-luna` becomes the default.

The original product plan pinned `claude-opus-5`. We use `claude-opus-5-5` instead: it is the current, most capable Opus model, and the plan was written before it existed. Affects `docs/tech-stack.md` (Model and SDK).

## Consequences

All cost and quality figures in the eval table are for `claude-opus-5-5`. If an older model is swept for comparison, record it as a separate variant.
