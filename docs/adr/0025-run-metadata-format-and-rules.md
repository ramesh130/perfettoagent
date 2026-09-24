# Run metadata: this project's own format, checked against the range, and sanitised for the eval cases

Issue #31 adds `diagnose --run-json` and the `read_run_metadata()` tool. It is the input rule roadmap item 7 lists: a commit outside `--range` is refused, and a dirty tree or a debuggable build becomes a caveat. The issue leaves open what the file is. Affects `src/perfettoagent/run_metadata.py`, `agent.py`, `cli.py`, `report.py`, `verify.py` and `evalcases.py`, `evals/build_cases.py`, every eval case, `docs/tech-stack.md` and roadmap items 6 and 7.

## The file is a small format of its own, not a capture tool's `run.json`

The two capture harnesses record the same facts under different keys:

| Fact | devicelab (superPlayer) | jetnews-perf's harness |
|---|---|---|
| Built from | `superplayer.commit` | `base_commit` |
| Uncommitted changes | `superplayer.tree_dirty` | not recorded |
| Debuggable | `demo.debuggable` | `app.debuggable` |

Both also record the plant, the scenario and paths, which no model input may name. So `--run-json` takes run metadata schema 1: `schema`, `commit`, `tree_dirty`, `debuggable`, `build_type` and `device` (`model`, `sdk`, `emulator`), with the last two null when not recorded. Every property is required and no other is allowed, so a raw `run.json` passed by mistake is refused, and it is refused before it could show the model its `plant` field. A harness writes this file, or a user writes it by hand from its `run.json`. Accepting each harness's shape would put app-specific keys (`superplayer`) into this repo.

It describes the **current** trace's capture. A baseline file would add nothing the rules use: the baseline's build is the range's base.

## The rules

- **The commit must be inside the range**, by the rule a commit citation is held to (ADR-0006): what `git log base..head` lists. `verify.commit_in_range` is that rule, shared. A commit outside it, or naming no commit, is refused before any request (`RunMetadataInvalid`, exit 2): the range cannot explain a trace built outside it.
- **A dirty tree or a debuggable build is a caveat** that `diagnose` adds to the diagnosis before the verifier. The model does not write it, so it cannot leave it out. The report's first ten lines name it: `Current build: uncommitted changes, debuggable; see Caveats`. `diagnosis.json` schema 1 is unchanged: the caveats are fixed strings, and the report recognises them.
- **`read_run_metadata()` is bound only when `--run-json` was passed.** It takes no arguments, has a strict schema, and returns the file as loaded. Its description says it tells the model nothing about the baseline's build or what changed between the builds.

## Each eval case gets a sanitised `run.json`

`evals/cases/<id>/run.json` is written by `build_cases.py` from the current trace's devicelab `run.json`, and `stage` hands it to the runner beside the traces.

- **`commit` is the range's head**, not the superPlayer commit, which is in no case's history. The head is the build's app source (ADR-0015).
- **`tree_dirty` is always false, for the same reason.** Copying devicelab's flag would give the answer away: it is true for exactly the planted runs, whose plant sat uncommitted in the tree while it was built. A test checks that, apart from its commit, no planted case's metadata differs from every clean pair's.
- `debuggable`, `build_type` and `device` are copied. Every superPlayer capture is a non-debuggable benchmark build on the same emulator.
- The hint scan covers the file, and `build_cases.py --check` compares it with a rebuild.

## Consequences

- `docs/tech-stack.md`'s `read_run_metadata` row cites this ADR. Roadmap items 6 and 7 no longer list it as open.
- #35 writes the JetNews cases' `run.json` the same way. Its captures are debuggable debug builds (ADR-0021), so every JetNews diagnosis carries the debuggable caveat, clean or planted alike.
- The eval runner (#33) passes each case's metadata to `diagnose`.
