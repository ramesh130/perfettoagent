# The JetNews eval cases: built like superPlayer's, from jetnews-perf's captures

Issue #35 turns #34's JetNews captures (ADR-0021) into eval cases, the way ADR-0015 built superPlayer's: opaque ids, answers kept apart, a synthetic range with decoys, its own fixture bundle, and a builder whose `--check` reproduces every sha. This records what differs for the second app, and the Git LFS use. Affects `evals/build_jetnews_cases.py`, `evals/build_cases.py`, `evals/cases/`, `evals/answers/`, `evals/repos/jetnews.bundle`, `tests/test_eval_cases.py` and roadmap item 8.

## The builder

`evals/build_jetnews_cases.py --jetnews-perf <clone>` writes the cases, and `--check` compares a rebuild with what is committed. It is the only code that reads jetnews-perf, a private repo, and it runs by hand. It reuses `build_cases.py`'s history code: `Repo`, `Edit`, `unseen_edits`, and `lay_out_history`, which the two builders now share. That code was factored out of superPlayer's `build_history` without changing its draws: `build_cases.py --check` still reproduces every superPlayer sha.

- **The root commit is `JetNews/` as every capture was built**, the tree `f756bb2` that all 37 runs record as `app.source_tree`. It leaves out upstream's `screenshots/`, 8.3 MB of README images that the app does not build, which cut the bundle from 9.1 MB to 0.9 MB. jetnews-perf's `harness/`, `plants/`, `runs/` and `NOTICE.md`, which name the plants, lie outside `JetNews/`, and so outside every case.
- **The culprit applies the patch its current run recorded,** `runs/<id>/plant.patch`, after checking it against the run's `plant.patch_sha256`. Its paths lose their `JetNews/` prefix (`git apply -p2`). The answer stores the patch with the fixture repo's paths, so the patch-id test compares like with like.
- **The traces are copied as captured.** jetnews-perf already stores them gzipped, so no bytes change.
- **Run metadata (ADR-0025).** The commit is the range's head, and `tree_dirty` is false. `debuggable` (true) and `build_type` (`debug`) are copied. jetnews-perf's device record has no model or emulator field, so the model is the build fingerprint's device name, and `emulator` means the serial starts `emulator-`. The values are the same as superPlayer's.

## The pool of commits

There are 19 edits, fictional authors at `jetnews.invalid`, and the same range lengths, decoy counts and dating as ADR-0015.

- **Decoys**, changing behaviour in code none of the four scenarios runs:
  - the home-screen widget's refresh period;
  - the Interests screen's thumbnails and its topic button;
  - the padding of the fewer-stories dialog, a history row's menu that no scenario opens. It sits in `PostCards.kt`, the feed plants' own file.
- **Neutral edits:** comments and KDoc, three private renames, and the Gradle daemon's heap.
- **What they avoid:**
  - every line a plant's hunks use, context included (`openDialog` is in the bookmark plant's context, so it is not renamed);
  - the three repository files the listener plant changes (ADR-0021).
- **The filters.** `unseen_edits` drops any edit a case's traces could contradict. The hint scan caught one of the first draft's rewordings, "dependency injection", on its word `inject`, and it was reworded.

## The cases

| Kind | Plant | Expected metrics | Runs (baseline → current) |
|---|---|---|---|
| planted | startup I/O | `startup_ttid_ms` | `123421Z` → `125501Z` |
| planted | allocation storm | `frame_ui_time_p95_ms`, `gc_time_ms` | `115742Z` → `120949Z` |
| planted | synchronous sleep | `main_thread_blocked_ms` | `112957Z` → `114105Z` |
| planted | layout thrash | `frame_ui_time_p95_ms` | `112635Z` → `115456Z` |
| planted | listener leak | `heap_growth_objects_by_class` | `113026Z` → `114136Z` |
| clean | startup | none | `123421Z` → `125758Z` |
| clean | scroll | none | `115742Z` → `121218Z` |
| clean | scroll | none | `121218Z` → `122522Z` |
| clean | bookmarks | none | `122745Z` → `124436Z` |
| clean | leak | none | `113026Z` → `113151Z` |

All runs are from 2026-09-24. Each is ADR-0021's first pair for its plant, and each clean pair is two clean runs of one session.

**Layout thrash expects UI time only.** Roadmap item 5 lists `frame_ui_time_p95_ms` and `jank_frames_pct` for it, and superPlayer's case accepts both. On JetNews, jank does not clear the clean runs' spread (ADR-0021), so a diagnosis resting on it would be right by luck. This is a divergence from the roadmap's table, for this app only.

## Tests

`tests/test_eval_cases.py` now covers both apps. A case's app is its `inputs.json` `repo`. Five planted cases and at least five clean pairs are counted per app, and the plants are distinct per app. Every other test (hint scan, patch-id match, checkout isolation, range lengths, run metadata) already ran over every case. The hint scan looks for the two apps' shared regression names once each.

## Git LFS

The JetNews cases add 16 trace objects, 182.6 MB, since pairs share runs. With ADR-0015's 312.3 MB, LFS storage is about 495 MB of the 1 GB quota. `.lfsconfig` still leaves `evals/cases/**` out of a default fetch, so a clone and CI's checkout download nothing more. The bundle, 0.9 MB, is plain git, like superPlayer's.

## Consequences

- Roadmap item 8 is done.
- Every JetNews diagnosis carries the debuggable caveat (ADR-0025), clean or planted alike.
- The eval runner runs all 20 cases by default. `results/gpt-5.6-luna-high-auto` holds only the 10 superPlayer cases until it is run again: a run with a result is skipped (ADR-0027).
