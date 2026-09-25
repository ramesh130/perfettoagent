# perfettoagent

**Two Perfetto traces and a git range in, a cited diagnosis out: which metric regressed, by
how much, which commit caused it, and the trace rows that show it.**

Every claim cites a trace query or a commit. A deterministic verifier re-runs each citation
before anything is written, and drops any claim whose citation fails.

## What it's for

A perf alert fires: startup is slower, scrolling janks, memory keeps climbing. You have a trace
from before and a trace from after, and a merge range of 5 to 50 commits in between. Finding
the culprit by hand means switching between trace queries, `git log` and `git blame`, and it
takes hours. perfettoagent runs that loop and hands back an answer where every claim can be
checked.

The kinds of regression it looks for, each with the metric that measures it:

| Regression | What the user sees | Typical cause | Metric |
|---|---|---|---|
| Slow startup | The app takes longer to show its first or full frame | Disk or network I/O, or heavy setup, on the main thread in `Application.onCreate` or the first Activity | `startup_ttid_ms`, `startup_ttfd_ms` |
| Jank from allocation churn | Scrolling stutters, and GC runs often | Objects allocated per frame in a draw or layout pass | `frame_ui_time_p95_ms`, `gc_time_ms` |
| Main-thread blocking | Taps feel stuck; frames are dropped around input | `Thread.sleep`, lock waits or synchronous binder calls on the UI thread | `main_thread_blocked_ms`, `binder_wait_ms` |
| Layout thrash | Scrolling janks while nothing visibly changes | Re-measuring or recomposing every visible item on every frame | `frame_ui_time_p95_ms`, `jank_frames_pct`, `frame_p95_ms`, `frame_p99_ms` |
| Memory leaks | Heap keeps growing across repeated navigation | Listeners or callbacks registered and never removed | `heap_growth_objects_by_class`, `native_unfreed_bytes` |

The answer names the metric and how far it moved, the commit that caused it, and the trace
rows and commits that show it. When the evidence cannot attribute a change, it says so.

It does not capture traces (devicelab or the `perfetto` CLI does), fix the code, or run on
non-Android traces.

## A real diagnosis

The start of [`diagnosis.md`](evals/results/gpt-5.6-luna-high-auto/runs/69dc18c7/1/diagnosis.md)
from an eval run. The case is superPlayer's feed, with a synchronous sleep planted in a tap
handler somewhere in a 12-commit range.

> # Regression
>
> - **Metric:** `main_thread_blocked_ms` +706.25 ms (25.28 → 731.53 ms)
> - **Culprit:** `c70fd55eea99` (direct); `demo/src/main/kotlin/com/superplayer/demo/FeedScreen.kt`
> - **Verified:** 5 claims kept, 1 dropped; 9 of 11 citations passed
> - **Model's confidence:** high (never scored)
>
> ### c5. Commit c70fd55eea9930f42380069d9b1f0a3f22bc403b added Thread.sleep(TAP_HOLD_MS) to FeedScreen's onFeedTapped handler and set TAP_HOLD_MS to 120L; blame at the range head attributes both lines to that commit.

The full report goes on to give:
- each claim's SQL and verified row count, or the commit it cites;
- the caveats, such as one capture per side;
- the claim the verifier dropped, because its SQL would not run;
- the run's cost: 43 tool calls and $0.0242.

## Measured

Every number below is from [`evals/results/summary.md`](evals/results/summary.md). That file
is generated from the per-run results beside it.

The eval covers 20 cases over two apps, [superPlayer](docs/adr/0015-eval-cases-and-their-fixture-repo.md)
and [JetNews](docs/adr/0028-jetnews-eval-cases.md), whose plants and captures are in
[`jetnews-perf`](https://github.com/ramesh130/jetnews-perf):
- **Planted:** each app has five regressions (main-thread I/O on startup, allocation storm,
  synchronous sleep, layout thrash, listener leak), each in a range of 10 to 12 commits with
  decoys.
- **Clean:** each app has five clean pairs, two clean captures of the same build.

Every case ran three times with `gpt-5.6-luna`. Each rate is over runs, and the range in
brackets is the lowest and highest of the three repetitions.

| Effort | Detection | Attribution | False positives | Citation validity | USD / trace | Wall time / trace |
|---|---:|---:|---:|---:|---:|---:|
| low | 73% (22/30; 70%–80%) | 91% (20/22) | 20% (6/30) | 96% (347/363) | $0.0074 | 84 s |
| medium | 80% (24/30; 70%–100%) | 92% (22/24) | 20% (6/30) | 92% (379/414) | $0.0134 | 145 s |
| high | 87% (26/30; 80%–90%) | 100% (26/26) | 27% (8/30) | 95% (525/552) | $0.0289 | 264 s |
| xhigh | 93% (28/30; 80%–100%) | 100% (28/28) | 10% (3/30) | 96% (603/627) | $0.0441 | 319 s |

- **Detection:** a planted case called a regression, judged by a metric the case expects.
- **Attribution:** of those detections, the share that name the planted commit.
- **False positives:** clean pairs called a regression.
- **Citation validity:** citations the verifier passed. The model's own confidence is never
  scored.
- **Time to diagnosis:** the agent took 1.3 to 5.0 minutes per case on superPlayer's planted
  cases, depending on effort. The manual baseline of 60 minutes is **assumed, not measured**
  ([ADR-0030](docs/adr/0030-assumed-manual-triage-baseline.md)).
- **`claude-opus-5-5`,** the compared model, was not swept. One live run of the leak case
  found the culprit, with every claim kept.

What it gets wrong, and why, is in [`docs/postmortem.md`](docs/postmortem.md). In short:
- False positives come from two noisy clean pairs, where one capture per side cannot tell a
  small change from noise.
- Most misses name the right commit but judge it by a metric the case does not expect.

## How it works

The agent works in the order an engineer would. It measures the metric delta, localises it
in the trace, correlates it with the range, then blames. Its tools:

| Tool | What it does |
|---|---|
| `list_metrics`, `compute_metric` | canned Perfetto stdlib metrics, each returning the SQL behind its number |
| `query_trace` | read-only SQL on either trace, at most 200 rows |
| `symbolize` | trace frames to Java/Kotlin names, through R8 mappings |
| `get_git_log`, `get_git_diff`, `git_blame`, `grep_repo` | the target repo, read at commits, never written |
| `read_run_metadata` | the capture's build facts, when `--run-json` is given |

The model answers in a strict JSON schema. Then the [verifier](docs/adr/0006-diagnosis-schema-and-verifier-semantics.md):
- re-runs every cited query, which must return a row;
- checks that every cited commit is inside the range and changes the cited path;
- drops any claim with a failed citation;
- drops a culprit that no surviving claim cites;
- makes the verdict `inconclusive` when no claim survives.

Only then are `diagnosis.json` and `diagnosis.md` written.

Two providers are supported ([ADR-0020](docs/adr/0020-two-model-providers.md)):
- OpenAI's Responses API with `gpt-5.6-luna`, the default;
- Anthropic's Tool Runner with `claude-opus-5-5`.

## Use it

Requires macOS or Linux, Python 3.12 and [`uv`](https://docs.astral.sh/uv/). The pinned
Perfetto trace processor (58.2) is downloaded and checked on first use.

```sh
uv sync
echo 'OPENAI_API_KEY=…' > .env        # or ANTHROPIC_API_KEY; git ignores .env

mkdir -p out
uv run perfettoagent diagnose \
  --baseline before.perfetto-trace --current after.perfetto-trace \
  --repo ../my-app --range <base-sha>..<head-sha> \
  [--run-json run.json] [--provider anthropic] [--effort xhigh] \
  --out out/diagnosis.json           # writes out/diagnosis.json and out/diagnosis.md

uv run perfettoagent review out accept         # or: reject <reason>, partial <claim-ids>
uv run perfettoagent tp --trace after.perfetto-trace --sql "SELECT count(*) FROM slice"
```

To reproduce the eval, fetch the traces, then run and summarise:

```sh
git lfs pull --include="evals/cases/**" --exclude=""
uv run perfettoagent eval --effort high --jobs 3
uv run python evals/summarize.py
```

## Limits

- **The captures.** All of them are from one API 36 emulator, with a single capture per side.
  JetNews's builds are debuggable, and every JetNews diagnosis says so.
- **Deliberately out of scope.** Android traces only. No UI, no capture, and no fixes: the
  agent points at a commit and stops ([mission](docs/mission.md)).

## More

- [Mission](docs/mission.md), [tech stack](docs/tech-stack.md) and [roadmap](docs/roadmap.md).
- Every decision and divergence is recorded as an ADR in [`docs/adr/`](docs/adr/).

Licensed under [Apache-2.0](LICENSE).
