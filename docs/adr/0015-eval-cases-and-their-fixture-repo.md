# Eval cases: model inputs apart from answers, in a fixture repo built to match the traces

Roadmap item 5 and issue #10 turn the devicelab captures into eval cases. Each case needs two traces, a git range with the culprit inside it among at least 8 unrelated commits, and the expected answer. No input the model sees may name or hint at the plant. The captures come from superPlayer, whose public history holds the plant patches and their README. So the ranges cannot be superPlayer's own history: they are built. Affects `evals/`, `src/perfettoagent/evalcases.py`, `tests/test_eval_cases.py`, `.gitattributes`, `.lfsconfig` and roadmap item 5.

## Layout: what the model sees, and apart from it, what it should answer

- **`evals/cases/<id>/`** holds only what the model is given: `baseline.perfetto-trace.gz`, `current.perfetto-trace.gz` and `inputs.json`. `inputs.json` holds the range as two shas and the name of the fixture repo. A test checks that the directory holds these three files and nothing else.
- **`evals/answers/<id>.json`** holds the expected verdict, the expected metrics, the culprit sha, the plant's name, and where the traces came from. `evals/answers/patches/` holds each plant's patch. This diverges from the roadmap's first wording, which put everything in the case directory. The issue asks for the answers to live apart, and a directory the prompt builder never reads is the simplest form of apart.
- **Opaque ids** are 8 random hex digits (`secrets.token_hex(4)`), assigned in no meaningful order and listed sorted.
- **`perfettoagent.evalcases`** reads one side at a time. `load_inputs` returns `CaseInputs`: the traces, the range, and a `checkout(dest)` that materialises the repo. `load_expected` returns `Expected`: the verdict, the metrics and the culprit. Code that builds the prompt from `load_inputs` has no answer to leak.
- **The expected metrics** are the ones roadmap item 5 names, after ADR-0011. A diagnosis naming any of them counts as the right metric. Clean pairs expect `no_regression`, no metric and no culprit.

## The fixture repo: synthetic history that matches the traces

A range's two ends have to be the builds its two traces measured. Otherwise a trace would describe code outside its range. So each case's history is built as follows.

1. **The root commit is a snapshot of the exact superPlayer commit the baseline trace was built from**, as recorded in its `run.json`. It leaves out the measurement harness itself and every document that names the plants or describes the captures: `devicelab/`, `docs/`, `PRD.md`, `CLAUDE.md`, `CONTEXT.md`, `CHANGELOG.md`, `.github/`, `benchmark/` and `third-party/`. The root is the range's base.
   - The app's own references to its harness stay: comments that say what devicelab measures, a Gradle task that runs it, `.gitignore`'s entry for its output. A real app with a perf alert has such references. They say the app is measured, not what changed.
2. **Neutral commits** are drawn per case from a fixed pool, 9 to 12 of them. The range's length, the plant's commit included, is drawn from 10 to 12 for planted and clean cases alike, so the length gives the verdict away in neither. There are two kinds:
   - **Refactors**, which change nothing the app does:
     - comment and KDoc rewording;
     - renames of private identifiers;
     - one equivalent rewrite (`if/else` to `takeIf`);
     - one Gradle daemon heap setting.
   - **Decoys** (two or three per case), which change behaviour in code no scenario runs.
     - For the startup and jank snapshots, these are screens the scenarios never open (TV, MoQ, downloads).
     - For the leak snapshot, they are the test kit, which is not in the app at all.
     - Without them, the first review found that `git log --oneline` alone gave the culprit away. Every other message said "Rename…", "Say…" or "Reword…", and the plant's was the only one describing a new behaviour.
   Some sit in the plant's own file: `FeedScreen.kt` for the feed plants, `SuperPlayer.kt` for the listener plant, the demo's `MainActivity.kt` beside the startup plant. None touches a line a plant's hunks use, and none renames an identifier a plant's lines use. So each plant applies at any position.

   **Nor may one contradict the case's traces.** A trace records some of its build's source:
   - a heap dump names classes and fields, such as `PlayerPool.inUse` and `SuperPlayer$lastKnownPositions$1`;
   - a monitor-contention slice names a method with its file and line;
   - thread names, stack frames and log messages can name more.

   A rename of a name a trace records, or a moved line in a file a trace cites by line, would leave the range's head at code the trace does not match. The builder asks trace processor for every slice, thread, process, heap class, heap field and stack frame name, and every log message, in both of a case's traces, and leaves out any edit that renames one of them or changes a file they cite by line.
   - The leak case loses its four field renames.
   - The jank-scenario cases lose one method rename (`isObjectMethod`), which their traces also record.
   - Every case keeps at least 14 edits to draw from, 3 of them decoys.
3. **A planted case adds the plant as one more commit**, at a position drawn per case. The commit message describes the change the way its author would, e.g. "Check the catalog cache at launch", never as a regression.

The range's last commit is therefore the current trace's build plus changes that cannot move a trace. Attribution is still a search: every commit in the range has to be ruled out by its diff.

- **Dated like a real range.** Each history ends one to three days before its current trace was captured. Commits are 40 minutes to 10 hours apart, by three fictional authors.
- **Reproducible.** The dates, the authors and each case's draw come from fixed data and a seed per case. Rebuilding from the same superPlayer commits gives the same shas, and `evals/build_cases.py --check` proves it.
  - `build_cases.py` is the only code that reads superPlayer, and it runs by hand. The tech stack bars a test-time dependency.
  - It refuses to build if a capture's `run.json` names a different base commit, or if a planted run's patch sha256 differs from the patch it builds the culprit from.
  - The listener leak cannot be checked that way. Its runs predate devicelab's `--plant`, so their `run.json` records no plant. Which run carried it rests on the run table in superPlayer's `devicelab/leak/README.md`.
- **One bundle, staged per run.** `evals/repos/superplayer.bundle` (1.9 MB, plain git) holds one branch per case, named by case id. `CaseInputs.stage(dest)` builds everything the model is given under a directory the runner names:
  - `repo/`: a clone of only that case's branch, renamed `main`, with no remote, no reflog and, after a prune, no other case's objects. A clone from a bundle copies its whole pack, hence the prune.
  - The two traces as `baseline.perfetto-trace.gz` and `current.perfetto-trace.gz`, as hard links or copies.

  No path the model sees runs through `evals/` or holds the case id. Staging writes, so its git calls do not go through `perfettoagent.git`, whose allow-list is read-only. They clear the same redirecting environment and use the same timeout. Tests check each of these.
- **The culprit is the captured change.** A test checks that the culprit commit's `git patch-id` equals the stored patch's.

## The listener-leak case

The listener leak was never a devicelab plant file. It is the negative test in superPlayer's `devicelab/leak/README.md`, which commented out the four lines of `SuperPlayer.resetForReuse` that remove a pooled player's listeners.

- **Base.** The runs were made from `abc232c` plus uncommitted devicelab changes; the leak procedure was being written. The app's source is `abc232c`'s.
- **Traces.** Each is a feed-phase final heap dump after six passes: clean run `20260911T151106Z` against planted run `20260911T144545Z`. The heap fixtures of #3 are two dumps from inside the one planted run, which is the wrong shape for a before-and-after pair.
- **What the metric shows.** On this pair `heap_growth_objects_by_class`'s breakdown puts the listener classes the plant keeps near the top. The row's listener (`FeedScreenKt$FeedRow$1$1$1$1`) goes from 4 reachable objects to 152. The two clean runs hold 4 and 5. The headline total moves little: +2184 here, against +1132 between the two clean runs. So the per-class breakdown carries the finding.
- **The culprit deletes the four lines** rather than commenting them out. It compiles to the same code, and reads like a commit someone made.

## Nothing the model sees names the plant

`tests/test_eval_cases.py` scans everything a model could be shown for plant names, the roadmap's regression names, and words that tell it what it is looking at. The words are `plant`, `regress`, `culprit`, `perfettoagent`, `devicelab`, `eval`, `inject`, `deliberate`, `on purpose`, `leak`, `jank`, `thrash` and `storm`. It scans:
- case ids, the case directory's file names, and `inputs.json`;
- the staged paths the model is handed;
- every commit message and author;
- every path the range touches, and every line it adds;
- the whole checkout, for `plant` and this project's name.
A control test checks the scan finds a planted name.

The plant's code is the evidence, not a hint, and is scanned like everything else. "slow" was dropped from the word list because one plant's own comment says "a slow breath on every row", about an animation.

## Consequences

- **LFS.** The cases add 8 new trace objects, 114.4 MB. The other 12 case traces are byte-identical to test fixtures and stored once. LFS storage is now 312.3 MB of the 1 GB quota.
  - `.lfsconfig` excludes `evals/cases/**` from a default fetch, so a clone and CI's checkout still fetch 197.9 MB. Nothing in the test suite reads the eval traces.
  - The eval runner fetches them with `git lfs pull --include="evals/cases/**" --exclude=""`.
    - That downloads 114.4 MB on top of a default fetch.
    - It downloads 277.5 MB on its own: 16 distinct traces, some of them also test fixtures.
  - ADR-0012's suggestion to re-compress the heap dumps first is not needed while the eval traces stay out of the default fetch.
- **Known limit: a decoy's code never runs.** A model that works out which code the scenario exercises can still set the decoys aside. That is attribution work the agent should do, not a lookup. Decoys that run and still do not move the metric would be harder, but each would need a capture of its own to show it does not move the trace. Worth adding if attribution rates come back near 100%.
- **Lint.** `pyproject.toml` exempts `evals/build_cases.py` from ruff's line length (E501). Its edits quote Kotlin lines verbatim, and a literal that must match the source exactly cannot be wrapped. It is the only change to the lint rules.
- **Shared captures.**
  - The three jank-scenario planted cases and one jank clean pair share one baseline capture (B1).
  - The startup planted case and one startup clean pair share theirs.
  - Each case is run separately, with no memory of the others, so this costs nothing but variety.
- **No `run.json` is given to the model.** devicelab's `run.json` and `report.md` name the plant. `read_run_metadata` (roadmap item 6) needs a sanitised one, made per case, when it is built.
