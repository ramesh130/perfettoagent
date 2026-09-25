# Postmortem: what the agent got wrong, and why

Every count here comes from `evals/results/`: the four `gpt-5.6-luna-<effort>-auto` sets,
which run both apps' 20 cases three times each at four effort levels, and
`gpt-5.6-luna-high-expected` for Q3. The tables are in
[`evals/results/summary.md`](../evals/results/summary.md). Over the four `auto` sets, that is
120 runs of planted cases and 120 runs of clean pairs.

## Misses: mostly the wrong metric, rarely the wrong commit

20 of the 120 planted-case runs were not detections. By the roadmap's definition, a
detection is a `regression` verdict judged by a metric the case expects.

| App | Case | What the run said | Named the planted commit | Runs |
|---|---|---|---|---:|
| JetNews | Synchronous sleep | `regression`, by `frame_ui_time_p95_ms` | yes | 6 |
| superPlayer | Main-thread I/O on startup | `regression`, by `startup_ttfd_ms` | yes | 4 |
| superPlayer | Main-thread I/O on startup | `regression`, by `frame_ui_time_p95_ms` | yes | 2 |
| JetNews | Layout thrash | `regression`, by `gc_time_ms` | yes | 2 |
| superPlayer | Layout thrash | `regression`, by `gc_time_ms` or `frame_p95_ms` | yes | 2 |
| superPlayer | Synchronous sleep | `no_regression`, by `frame_p95_ms` | no | 2 |
| superPlayer | Synchronous sleep | `regression`, by `gc_time_ms` | no | 1 |
| JetNews | Allocation storm | `inconclusive` | no | 1 |

**16 of the 20 found the culprit but chose another metric to judge by.** Each is a metric
the plant really does move:
- a 120 ms sleep in a tap handler delays that frame;
- startup I/O delays the full display as well as the first;
- a thrashing layout allocates.

With `--metric auto`, the model sometimes judges by one of those, not by the one the case
expects. With the
expected metric named instead (Q3, ADR-0031), all 30 runs at `high` detected and attributed.
The fault is in the metric choice, not in the search for the commit.

**4 runs really missed.** Three were superPlayer's sleep case. Two judged it by frame
latency, where one 120 ms stall per tap barely moves a p95, and said `no_regression`. The
third judged it by `gc_time_ms` and blamed another commit. The fourth ended inconclusive on
JetNews's storm. In each, the model never measured the metric that carries the change.

## False positives: two noisy clean pairs, and commits that cannot explain them

23 of the 120 clean-pair runs said `regression`. **21 of the 23 come from two pairs:**

- **JetNews `d18a09bc`, a clean pair of the bookmarks scenario: 11 of 12 runs.** The
  scenario draws few frames, so a percentile of them is noisy. `frame_p95_ms` moved from
  19.9 ms to 36.0 ms, and `frame_ui_time_p95_ms` from 8.5 ms to 12.0 ms, between two clean
  runs. Every false positive blamed "Make the topic selection button 40 dp", as `correlated`.
  That commit is a decoy: it changes the Interests screen, which the scenario never opens
  (ADR-0028). The model read the frame delta as real, and blamed the one commit in the
  range that changes how something is drawn.
- **superPlayer `65f39dfe`, a clean pair of the jank scenario: 10 of 12 runs.** It moved
  +5.4 ms on `frame_p95_ms` (from 67.8), +24 ms on `frame_p99_ms`, and +2.6 ms on UI time.
  Most runs blamed "Acquire the watched row's player with takeIf". That commit is an
  equivalent rewrite in the feed's own file, which the traces do exercise, but it cannot
  change what runs. Two blamed a TV-screen decoy.

**Causes:**
- **One capture per side.** Nothing tells the model how far a clean run moves. The prompt
  says a small delta may be noise, and the model still calls one. At `xhigh` it did so least:
  3 of 30 runs, against 6 to 8 of 30 at the lower levels.
- **`correlated` attribution is too easy.** It lets a claim blame a commit with no trace row
  pointing into its diff. 22 of the 23 false positives named a `correlated` culprit, and
  one named a `direct` one. The verifier checks that a cited commit is in the range and changes the cited path. It does
  not check that a trace row points into the change, and the decoys are built to fail
  exactly that.
- The model's confidence was often `low` on these runs. It is never scored, so that is not
  a defence.

## Citations the verifier dropped: long SQL copied wrong

102 of the 1,956 citations across the four `auto` sets failed. 82 of those are one mistake,
repeated. The metric library's SQL picks the app with
`GROUP BY package ORDER BY count(*) DESC, package LIMIT 1`, and the model, copying a
metric's `sql_used` into a citation, wrote it back as `GROUP BY count(*) DESC` or
`GROUP BY count(*) ORDER BY …`. That fails to parse ("syntax error near 'DESC'"), or fails
because an aggregate is not allowed in `GROUP BY`. It happened with both the startup and
the frame metrics. The verifier dropped every such claim before anything was written,
which is its job. But the model lost true claims to transcription errors.

**Fix to try:** let a citation name a tool result (a metric's `sql_used` by metric and side)
instead of retyping its text. The verifier would re-run the stored SQL, and nothing would
be copied.

## Flips

Between 7 and 10 of the 20 cases disagreed across their three runs at each effort level.
The flips were on verdict, detection, attribution or false positive (`scores.json`,
`per_case`). One run per case would have hidden them, which is why every case runs three
times.

## Around the agent

- **Opus's history is not cached.** The one live `claude-opus-5-5` run found the leak's
  culprit, with every claim kept. But it read only 29K input tokens from the cache,
  against 105K uncached: the Tool Runner re-sends the growing history without a cache
  breakpoint (ADR-0023). That, not the list price alone, is why an Opus sweep was
  estimated at about $0.55 a run.
- **Provider limits ended 35 runs.** An exhausted quota and a rate limit ended 35 `xhigh`
  runs. They were first recorded as errors, which would have scored as misses. They were
  deleted and run again, and the runner now stops unrecorded instead (ADR-0031).

## What would change the numbers most

1. **Measure the noise.** Give the agent more than one capture per side, or each scenario's
   clean spread, so a delta can be judged against it. This targets the false positives.
2. **Make `direct` the only attribution that names a culprit.** Require a trace row that
   points into the culprit's diff; otherwise, no culprit.
3. **Cite tool results by reference,** so no SQL is copied.
4. **Steer the metric choice.** Tell the model to prefer the metric whose change is largest
   against its noise, or accept every metric a plant moves. Q3 shows the commit search is
   already right.
