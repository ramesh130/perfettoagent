# Mission

## What

perfettoagent takes a Perfetto trace and a git range and returns a **cited diagnosis**:

> startup regressed 180 ms at p95, caused by commit `abc123`, evidence: these trace slices.

It is not a dashboard that a person still has to read. Every claim cites a trace row or a
commit, and code rejects any claim without a citation before the user sees it.

## Why

When a perf alert fires, the Android engineer has a "before" and an "after" trace and a merge
range of 5–50 commits. Getting from there to the culprit means switching between trace
queries, `git log` and `git blame` by hand, which takes hours. An agent can run that loop.
Its answer is only useful if every step can be checked, and if the tool's accuracy has been
measured rather than asserted.

## Who it serves

- **An Android engineer with a red perf alert.** Wants the culprit in minutes, with evidence
  they can paste into a PR comment.
- **A reviewer reading the repo.** Wants to see within two minutes that this is an agent with
  a real tool surface, a real guardrail and measured results.

## Goals

1. **Diagnose, not summarise.** Name the regressed metric, the size of the change, and the
   culprit commit. If no culprit can be attributed, say so. Show the evidence either way.
2. **No uncited claims.** A deterministic verifier enforces this by re-running the cited SQL
   and checking the cited commit. It is not left to a prompt instruction.
3. **Measured on planted regressions.** Report detection rate and false-positive rate on at
   least four kinds of regression across at least two apps.
4. **Reproducible cost.** Record tokens and USD per trace on every run.
5. **Public-repo quality.** Clonable standalone under MIT or Apache-2.0, with a README that
   opens with the one-liner and a real diagnosis.

## Principles

- **No citation, no claim.** "Likely" and "probably" are allowed only inside a claim that
  still cites what makes it likely. The agent does not speculate.
- **Measured numbers are the deliverable.** No README figure without a matching file in
  `evals/results/`. Report the spread across runs, not the best run. A verdict that flips
  between runs is a finding to publish.
- **The tools are the whole contract.** If the agent needs information no tool provides, add
  a tool. Don't let it guess.
- **Read-only toward the world.** The agent reads traces and the target repo. It never edits
  the target repo.

## Non-goals

- Capturing traces. devicelab and the `perfetto` CLI produce them; this tool consumes them.
- A UI. Output is CLI plus Markdown and JSON only.
- Fixing the regression. The agent may point to where to look, with a commit citation.
- Non-Android traces, Windows hosts, or any Perfetto version other than the pinned one.
- Running on a schedule, a server, or the target app's CI. v1 is a local CLI.
