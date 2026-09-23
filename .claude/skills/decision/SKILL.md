---
name: decision
description: Append an ADR entry to docs/decisions.md. Use whenever work diverges from PRD.md, or when one of the PRD §13 open questions is settled.
---

Record a decision in `docs/decisions.md`. The PRD (§12) requires this for every divergence;
silent divergence is not allowed.

1. Read `docs/decisions.md` and find the highest `D<n>` number. The new entry is `D<n+1>`.
2. If `$ARGUMENTS` is given, use it as the decision summary. Otherwise infer it from the
   current conversation, and ask the user only if the reason is unclear.
3. Append (newest last) using exactly this shape:

```
## D<n> — <short title>

- **Date:** <today, YYYY-MM-DD>
- **PRD section:** <§ number(s), or "§13 Q<k>" for an open question>
- **Context:** <what the PRD says, or what was unknown>
- **Decision:** <what we're doing instead / the answer>
- **Why:** <evidence — measurements, docs, constraints; cite them>
- **Consequences:** <what this changes for code, evals, or README claims>
```

4. Keep it factual. If the decision rests on a measurement, give the number and where it
   came from (a file under `evals/results/`, a command output). Do not invent figures.
5. If the decision changes a rule stated in `CLAUDE.md`, update `CLAUDE.md` too.
