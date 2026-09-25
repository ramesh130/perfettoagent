"""The eval runner: every case, run N times, scored (roadmap item 9, issue #33,
ADR-0016, ADR-0027). `perfettoagent eval` and `evals/run_eval.py` run it.

For each case and each repetition, the case is staged afresh in a temporary directory
(`CaseInputs.stage`), so the model is handed paths that run through neither `evals/`
nor the case id (ADR-0015), and `diagnose` runs on it with the case's run metadata.
Each run writes, under `<out>/runs/<case>/<n>/`:

- `diagnosis.json` and `diagnosis.md`, for a run that gave a diagnosis;
- `result.json`: the provider, model and effort, and the run's `Outcome` (or the error
  that ended it, redacted).

A run whose `result.json` exists is not run again, so an interrupted sweep resumes
where it stopped. It must have been run with the same provider, model, effort and
metric choice: results from different settings are never pooled (ADR-0020). Once
every run has a result, the runs are scored against `evals/answers/`
(`perfettoagent.scoring`) and written as `scores.json` and `scores.md`. The answers
are read only to score, after the runs.

One exception, for roadmap Q3 (ADR-0031): with `metric="expected"`, each planted case
is run with `--metric` set to the first metric its answer expects, and clean pairs are
not run, having no metric to name. The model is then told which metric to judge by,
which is the condition Q3 compares against `auto`; it is never told the culprit.
"""

import json
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

import anthropic
import openai

from perfettoagent import models, run_metadata
from perfettoagent.agent import AUTO, RUN_ERRORS, diagnose
from perfettoagent.credentials import redact
from perfettoagent.evalcases import EVALS_DIR, list_cases, load_expected, load_inputs
from perfettoagent.report import render
from perfettoagent.scoring import Outcome, outcome_of, score

# CLAUDE.md: every case three times, and the spread reported.
RUNS = 3

# The provider declining to serve at all: an exhausted quota, a rate limit, a key it
# refuses. The run says nothing about the model, so it is not recorded; the eval stops,
# and a resume runs it again (ADR-0031). OpenAI reports a streamed failure as a plain
# APIError, so its `code` is read too.
_UNAVAILABLE = (
    anthropic.AuthenticationError,
    anthropic.PermissionDeniedError,
    anthropic.RateLimitError,
    openai.AuthenticationError,
    openai.PermissionDeniedError,
    openai.RateLimitError,
)
_UNAVAILABLE_CODES = {"insufficient_quota", "rate_limit_exceeded"}


class ProviderUnavailable(RuntimeError):
    """The provider would not serve a run; nothing was recorded for it."""


# `run_eval(metric=EXPECTED)`: each planted case judged by the metric it expects.
EXPECTED = "expected"

# Where results go: one directory per model, effort and metric choice.
RESULTS_DIR = EVALS_DIR / "results"

# The first bytes of a Git LFS pointer: a case whose traces were never fetched.
_LFS_POINTER = b"version https://git-lfs"


def results_name(model: str, effort: str, metric: str) -> str:
    """A results directory's name: what the runs in it share."""
    return f"{model}-{effort}-{metric}"


def run_eval(
    out: Path,
    *,
    cases: list[str] | None = None,
    runs: int = RUNS,
    provider: str = models.DEFAULT_PROVIDER,
    model: str | None = None,
    effort: str = models.DEFAULT_EFFORT,
    metric: str = AUTO,
    jobs: int = 1,
    root: Path = EVALS_DIR,
    diagnose_fn: Callable[..., dict] = diagnose,
    log: Callable[[str], None] = print,
) -> dict:
    """Runs every case in `cases` (default: all) `runs` times, writes each run's
    result under `out`, and returns the scores, also written to `out`."""
    model = model or models.DEFAULT_MODELS[provider]
    models.check_model(provider, model, effort)
    chosen = cases is not None
    cases = cases if chosen else list_cases(root)
    named = _named_metrics(cases, root) if metric == EXPECTED else {}
    if metric == EXPECTED:
        clean = [c for c in cases if c not in named]
        if chosen and clean:
            raise SystemExit(
                f"--metric {EXPECTED} runs planted cases only, not {', '.join(clean)}"
            )
        cases = [c for c in cases if c in named]
    for case_id in cases:
        _check_fetched(load_inputs(case_id, root))
    settings = {
        "provider": provider,
        "model": model,
        "effort": effort,
        "metric": metric,
    }

    def one(job: tuple[str, int]) -> Outcome:
        case_id, n = job
        directory = out / "runs" / case_id / str(n)
        result = directory / "result.json"
        if result.is_file():
            recorded = json.loads(result.read_text())
            ran_with = {k: recorded.get(k) for k in settings}
            if ran_with != settings:
                raise SystemExit(
                    f"{result} was run with {ran_with}, not {settings}: results from "
                    "different settings are never pooled; use another --out"
                )
            return Outcome(**recorded["outcome"])
        asked = {**settings, "metric": named.get(case_id, metric)}
        outcome = _run_once(case_id, n, directory, asked, root, diagnose_fn)
        judged_by = {"named_metric": asked["metric"]} if metric == EXPECTED else {}
        _write_json(result, {**settings, **judged_by, "outcome": asdict(outcome)})
        log(_line(outcome))
        return outcome

    todo = [(case_id, n) for case_id in cases for n in range(1, runs + 1)]
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        outcomes = list(pool.map(one, todo))

    # The answers, read only now: nothing above could pass them to a run.
    expected = {case_id: load_expected(case_id, root) for case_id in cases}
    scores = {**settings, **score(outcomes, expected)}
    _write_json(out / "scores.json", scores)
    (out / "scores.md").write_text(render_scores(scores))
    return scores


def _named_metrics(cases: list[str], root: Path) -> dict[str, str]:
    """Each planted case's first expected metric. Clean pairs have none."""
    named = {}
    for case_id in cases:
        expected = load_expected(case_id, root)
        if expected.metrics:
            named[case_id] = expected.metrics[0]
    return named


def _run_once(case_id, n, directory: Path, settings: dict, root, diagnose_fn):
    inputs = load_inputs(case_id, root)
    with tempfile.TemporaryDirectory(prefix="run-") as scratch:
        staged = inputs.stage(Path(scratch) / "inputs")
        try:
            diagnosis = diagnose_fn(
                baseline=staged.baseline,
                current=staged.current,
                repo=staged.repo,
                git_range=f"{staged.range_base}..{staged.range_head}",
                metric=settings["metric"],
                provider=settings["provider"],
                model=settings["model"],
                effort=settings["effort"],
                metadata=run_metadata.load(staged.run_metadata),
            )
        except RUN_ERRORS as e:
            if _unavailable(e):
                raise ProviderUnavailable(
                    f"{case_id} run {n}: the provider would not serve it: "
                    f"{redact(str(e))[:300]}. Nothing was recorded for it; run the "
                    "eval again, once the provider serves, to resume."
                ) from e
            # Recorded, and the sweep goes on. Anything else (a refused range, an
            # unpriced model) is the runner's own mistake, and raises.
            return Outcome(
                case_id=case_id, run=n, error=redact(f"{type(e).__name__}: {e}")
            )
    directory.mkdir(parents=True, exist_ok=True)
    _write_json(directory / "diagnosis.json", diagnosis)
    (directory / "diagnosis.md").write_text(render(diagnosis))
    return outcome_of(case_id, n, diagnosis)


def _unavailable(e: Exception) -> bool:
    return isinstance(e, _UNAVAILABLE) or getattr(e, "code", None) in _UNAVAILABLE_CODES


def _check_fetched(inputs) -> None:
    for trace in (inputs.baseline, inputs.current):
        with trace.open("rb") as f:
            if f.read(len(_LFS_POINTER)) == _LFS_POINTER:
                raise SystemExit(
                    f"{trace} is a Git LFS pointer. Fetch the eval traces with: "
                    'git lfs pull --include="evals/cases/**" --exclude=""'
                )


def _line(o: Outcome) -> str:
    if o.error is not None:
        return f"{o.case_id} run {o.run}: error: {o.error[:200]}"
    culprit = f", {o.culprit[:12]}" if o.culprit else ""
    return (
        f"{o.case_id} run {o.run}: {o.verdict} ({o.metric}{culprit}); "
        f"${o.usd:.4f}, {o.wall_time_s:.0f} s"
    )


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


_RATE_NAMES = {
    "detection": "Detection",
    "attribution": "Attribution",
    "false_positive": "False positives",
    "citation_validity": "Citation validity",
}


def render_scores(scores: dict) -> str:
    """`scores.json` as Markdown: the rates with their spread, each case's runs, and
    the cost."""
    reps = len(scores["repetitions"])
    lines = [
        f"# {scores['model']}, effort {scores['effort']}, metric {scores['metric']}",
        "",
        f"{scores['cases']['planted']} planted cases and {scores['cases']['clean']} "
        f"clean pairs, {reps} runs each ({scores['runs']} runs, "
        f"{scores['errors']} ended in an error). Provider: {scores['provider']}.",
        "",
        "| Rate | Overall | Lowest run | Highest run |",
        "|---|---:|---:|---:|",
    ]
    for key, name in _RATE_NAMES.items():
        r = scores["rates"][key]
        lines.append(
            f"| {name} | {_pct(r['rate'])} ({r['hits']}/{r['of']}) | "
            f"{_pct(r['min'])} | {_pct(r['max'])} |"
        )
    lines += [
        "",
        "Lowest and highest are the rate over one repetition of every case: the "
        "spread, not the best run. The model's confidence is never scored.",
        "",
        "## Cases",
        "",
        "| Case | Expected | Verdicts | Detected | Attributed | False positive | "
        "Flipped |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in scores["per_case"]:
        verdicts = ", ".join(v if v else "error" for v in c["verdicts"])
        planted = c["expected"] == "regression"
        lines.append(
            f"| `{c['case']}` | {c['expected']} | {verdicts} | "
            f"{_marks(c['detected']) if planted else '–'} | "
            f"{_marks(c['attributed']) if planted else '–'} | "
            f"{'–' if planted else _marks(c['false_positive'])} | "
            f"{'yes' if c['flipped'] else ''} |"
        )
    cache = scores["cache"]
    read = cache["checked"] - len(cache["missing"])
    missed = (
        f"; none read by {', '.join(cache['missing'])}." if cache["missing"] else "."
    )
    lines += [
        "",
        f"Cache reads from the second run on: {read} of {cache['checked']} runs read "
        f"cached tokens{missed}",
    ]
    cost = scores["cost"]
    wall = cost["wall_time_s"]
    lines += ["", "## Cost", ""]
    if cost["usd_per_run"] is None:
        lines.append("No run gave a diagnosis.")
    else:
        u = cost["usage_per_run"]
        lines += [
            f"${cost['usd']:.4f} in all; per run ${cost['usd_per_run']:.4f}, "
            f"{wall['mean']:.0f} s (from {wall['min']:.0f} to {wall['max']:.0f} s).",
            f"Tokens per run: {u['input_tokens']:,.0f} input, "
            f"{u['cache_read_input_tokens']:,.0f} cache read, "
            f"{u['cache_creation_input_tokens']:,.0f} cache write, "
            f"{u['output_tokens']:,.0f} output.",
        ]
    return "\n".join(lines) + "\n"


def _pct(value: float | None) -> str:
    return "–" if value is None else f"{100 * value:.0f}%"


def _marks(values: list[bool]) -> str:
    return f"{sum(values)}/{len(values)}"


def main(argv: list[str] | None = None) -> int:
    """`evals/run_eval.py`: the same as `perfettoagent eval`."""
    from perfettoagent.cli import main as cli_main

    return cli_main(["eval", *(sys.argv[1:] if argv is None else argv)])
