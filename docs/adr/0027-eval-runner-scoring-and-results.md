# The eval runner: how runs are staged, scored and written

Issue #33 builds the local runner that ADR-0016 chose. It stages every case, runs `diagnose` on it three times, and scores the runs against the expected answers. The issue leaves open how a run that raises is scored, what "the spread" is, and how results are laid out. Affects `src/perfettoagent/evalrun.py`, `scoring.py` and `cli.py`, `evals/run_eval.py`, `evals/results/`, `docs/tech-stack.md` (Evaluation) and roadmap item 9.

## Running

- **`perfettoagent eval`, and `evals/run_eval.py`,** which ADR-0016 named, as the same command. The tech stack already listed `eval` among the subcommands.
- **Each run is staged afresh** by `CaseInputs.stage`, into a temporary directory named `run-…/inputs`, and removed afterwards. So the model's paths run through neither `evals/` nor the case id (ADR-0015), and no run can see another's scratch. `diagnose` gets the case's run metadata (ADR-0025) and `--metric auto`.
- **The answers are read after the runs, only to score.** A test checks that no run starts once they have been read.
- **A run that raises is recorded, not retried:** the provider's errors, `RunFailed`, `DiagnosisInvalid`, git failing to run, and trace processor errors. Its error is redacted like the CLI's. Any other exception, such as a range the verifier refuses or an unpriced model, is the runner's own mistake, and stops the sweep.
- **Resumable.** A run whose `result.json` exists is not run again, so an interrupted sweep continues where it stopped, and adding repetitions runs only the new ones.
- **`--jobs`** runs cases in parallel. Each run already streams and waits on the API most of the time.

## Scoring (`perfettoagent.scoring`)

Each run becomes an `Outcome`: the verdict, the metric's name, the culprit, the citation counts, usage, USD and wall time. It has no confidence field, so nothing can score on it. The rates are the roadmap's, each over its own denominator:

| Rate | Counts | Over |
|---|---|---|
| Detection | verdict `regression` and a metric the case expects | runs of planted cases |
| Attribution | culprit equals the planted commit | detected runs |
| False positives | verdict `regression` | runs of clean pairs |
| Citation validity | citations the verifier passed | citations it checked |

- **A run that raised** counts as a miss on a planted case. On a clean pair it is left out of the false-positive rate, since calling it "no false positive" would flatter the rate. Either way it is counted, and the report shows how many there were. Its cost is unknown, so it adds no USD.
- **The spread.** Each rate is also computed per repetition: every case's first run, then every case's second, and so on. The report shows the overall rate with its lowest and highest repetition, never the best alone. Per case, it lists every run's verdict, detection and attribution. A case whose runs disagree on any of them is marked as flipped. The mission counts a flipping verdict as a finding to publish, not noise to average away.

## Results

`evals/results/<model>-<effort>-<metric>/`:
- `runs/<case>/<n>/diagnosis.json` and `diagnosis.md`, the run's verified output;
- `runs/<case>/<n>/result.json`: provider, model, effort, metric choice, and the `Outcome`, or the error;
- `scores.json` and `scores.md`: the rates with their spread, each case's runs, and the cost.

Results are committed, every run of them. Until now `.gitignore` tracked only `evals/results/summary.md`. But a summary number is checkable only against the runs it came from, and the README may quote only what `evals/results/` contains (CLAUDE.md). A set of 30 runs is about 0.8 MB of JSON and Markdown, and no trace is copied into it. Results for different models, effort levels or metric choices are never pooled: each set has its own directory and its own scores (ADR-0020).

## The first results

`gpt-5.6-luna-high-auto`: every superPlayer case, three runs each, at effort `high`. It cost $0.97 in all, and no run ended in an error.

| Rate | Overall | Lowest repetition | Highest repetition |
|---|---:|---:|---:|
| Detection | 14/15 | 80% | 100% |
| Attribution | 14/14 | 100% | 100% |
| False positives | 5/15 | 20% | 40% |
| Citation validity | 240/257 | 90% | 99% |

- **The one miss** is a run of the layout-thrash case. It blamed the right commit, but judged by `gc_time_ms`, which is not one of the metrics the case expects (ADR-0011). Under the roadmap's definition, a wrong metric is not a detection.
- **False positives** are the finding to publish.
  - One clean pair (`65f39dfe`) was called a regression every time: a 5.4 ms `frame_p95_ms` rise, at confidence `low`.
  - Two clean pairs flipped between runs. On one, runs split between `inconclusive` and `regression` over a 205 ms `startup_ttfd_ms` gap. On the other, one run of three called a 9 ms rise in main-thread blocking a regression.

  A single capture per side cannot tell noise from a change of that size. The prompt tells the model so, and the model still sometimes calls the change.
- Runs averaged 311 s (154 to 1,009 s) and $0.032, and read 340K cached input tokens each.

## Consequences

- Roadmap item 9 is in progress. The effort sweep and `summary.md` are #36; running other providers and models is #44.
- `docs/tech-stack.md` "Evaluation" names the command and the results layout.
