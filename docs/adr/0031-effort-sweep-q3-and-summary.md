# The effort sweep, Q3 settled, and how `summary.md` is made

Issue #36 publishes the results. It covers every case from both apps, three runs each, at four effort levels, and it settles roadmap Q3: whether `--metric auto` loses attribution against a named metric. This records how the sweep was run, what it found, and how the summary is generated. Affects `src/perfettoagent/summary.py`, `evalrun.py` and `cli.py`, `evals/summarize.py`, `evals/results/`, `docs/tech-stack.md` (Evaluation) and roadmap item 9 and Q3.

## How it was run

- **`gpt-5.6-luna` at `low`, `medium`, `high` and `xhigh`,** with `--metric auto`: 20 cases × 3 runs each, in four results sets. Then `--metric expected` at `high` on the 10 planted cases, 3 runs each. In all, 270 runs and $6.41.
- **`claude-opus-5-5` was not swept, by the owner's decision.** At about $0.55 a run, a sweep would have cost about $130 for the full table, or $30 at one level. One live run of the listener-leak case was made instead (ADR-0023). `summary.md` says so, and keeps that run out of its tables, because one run is not a rate.
- **The provider running out.** Partway through `xhigh`, the account ran out of credits and then hit its 500K tokens-per-minute limit. Those 35 runs were recorded as errors, which would have scored as misses. They said nothing about the model, so they were deleted and run again. The runner now stops on such a failure without recording the run, so a resume redoes it. The failures it treats this way are an exhausted quota, a rate limit, a refused key, and OpenAI's `insufficient_quota` and `rate_limit_exceeded` codes. `xhigh` finished one run at a time; the other levels ran 3 to 5 at once.
- **Wall times are an upper bound.** Runs shared the machine and the rate limit with each other.

## What it found

All figures are from `evals/results/summary.md`, over both apps' 20 cases:

| Effort | Detection | Attribution | False positives | USD / trace | Wall time |
|---|---:|---:|---:|---:|---:|
| low | 22/30 | 20/22 | 6/30 | $0.0074 | 84 s |
| medium | 24/30 | 22/24 | 6/30 | $0.0134 | 145 s |
| high | 26/30 | 26/26 | 8/30 | $0.0289 | 264 s |
| xhigh | 28/30 | 28/28 | 3/30 | $0.0441 | 319 s |

- **Detection rises with effort.** Once a run detects the regression, it names the planted commit almost always: attribution is perfect at `high` and above.
- **False positives are the weakness.** A single capture per side cannot separate noise from a small change, and the model sometimes calls the change anyway. Only `xhigh` brings the rate down, to 10%.
- **Verdicts flip.** Between 7 and 10 of the 20 cases disagree across their three runs at each level. The mission counts that as a finding, not noise to average away.
- **The cache check passes** on every set: every run from the second repetition on read cached tokens.
- **The time-to-diagnosis baseline is assumed** (ADR-0030). The table labels it so.

## Q3: `--metric auto` stays, alone

Roadmap Q3: ship `auto`, and if attribution drops more than 10 points against a named metric, report both. The named-metric set runs each planted case with the first metric its answer expects, at `high`.

- **Attribution is the same:** 26/26 with `auto`, and 30/30 named.
- **Detection is not:** 26/30 with `auto` against 30/30 named. `auto` sometimes judges by a metric the case does not expect, such as `gc_time_ms` for layout thrash, even when it blames the right commit. Every run in both sets named the planted commit.

So by Q3's rule `auto` stands alone. The detection gap is in the summary beside it, since it is how `auto` loses.

## `summary.md` is generated, not written

`evals/summarize.py` (`perfettoagent.summary`) reads every results set's per-run `result.json` and scores it again against `evals/answers/`. It then writes:
- one row per effort level, for both apps together and for each app;
- time to diagnosis against `manual-triage/triage.json`;
- the Q3 comparison, with the verdict worked out by Q3's rule;
- the cache check, and what was not run.

No number in it is typed by hand, so it cannot disagree with the runs (CLAUDE.md).

## Consequences

- Roadmap item 9 is done, and Q3 is resolved.
- The README (#37) quotes `summary.md`, with the manual baseline marked assumed.
- **For future re-runs:** `xhigh` is the most accurate level and costs about 1.5× `high`. A Tool Runner cache breakpoint on the growing history would make an Opus sweep far cheaper (ADR-0023).
