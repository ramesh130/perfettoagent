"""Scoring eval runs against the expected answers (roadmap item 9, issue #33, ADR-0027).

Each run of a case is reduced to an `Outcome`: what the verified diagnosis said
(verdict, metric, culprit), its citation counts and its cost, or the error that ended
it. The model's confidence is not carried, so nothing here can score on it
(CLAUDE.md).

The rates, each over its own denominator (ADR-0016):

- **Detection:** planted-case runs whose verdict is `regression` and whose metric is
  one the case expects.
- **Attribution:** detected runs whose culprit is the planted commit.
- **False positives:** clean-pair runs whose verdict is `regression`.
- **Citation validity:** citations that passed the verifier, of all it checked.

A run that raised has no diagnosis. On a planted case it counts as a miss; on a clean
pair it is left out of the false-positive rate, since counting it as "no false
positive" would flatter the rate. Either way it is counted and reported.

The spread: every rate is also computed per repetition (all cases' first runs, then
their second, ...), and the report gives the lowest and highest, never only the best.
A case whose runs disagree on verdict, or on whether they detected or attributed, is
listed as flipping.

The cache check (docs/tech-stack.md, ADR-0020): from the second repetition on, every
run that gave a diagnosis must have read its prompt from the cache. `usage` is already
in one shape for both providers (ADR-0023): `cache_read_input_tokens` is Anthropic's
own field and OpenAI's `cached_tokens`. A run that read nothing from the cache is
listed, not scored.
"""

from dataclasses import dataclass, field
from statistics import mean

from perfettoagent.evalcases import Expected
from perfettoagent.models import USAGE_FIELDS


@dataclass(frozen=True)
class Outcome:
    """One run of one case, as scoring sees it."""

    case_id: str
    run: int
    verdict: str | None = None
    metric: str | None = None
    culprit: str | None = None
    citations_checked: int = 0
    citations_passed: int = 0
    usd: float = 0.0
    wall_time_s: float = 0.0
    usage: dict = field(default_factory=lambda: dict.fromkeys(USAGE_FIELDS, 0))
    # Why the run gave no diagnosis, or None when it gave one.
    error: str | None = None


def outcome_of(case_id: str, run: int, diagnosis: dict) -> Outcome:
    """The outcome of a run that wrote `diagnosis` (DIAGNOSIS_SCHEMA)."""
    v = diagnosis["verification"]
    cost = diagnosis["run"]
    return Outcome(
        case_id=case_id,
        run=run,
        verdict=diagnosis["verdict"],
        metric=diagnosis["metric"]["name"] if diagnosis["metric"] else None,
        culprit=diagnosis["culprit"]["commit"] if diagnosis["culprit"] else None,
        citations_checked=v["citations_checked"],
        citations_passed=v["citations_passed"],
        usd=cost["usd"],
        wall_time_s=cost["wall_time_s"],
        usage=dict(cost["usage"]),
    )


def detected(outcome: Outcome, expected: Expected) -> bool:
    return (
        expected.verdict == "regression"
        and outcome.verdict == "regression"
        and outcome.metric in expected.metrics
    )


def attributed(outcome: Outcome, expected: Expected) -> bool:
    return detected(outcome, expected) and outcome.culprit == expected.culprit


def false_positive(outcome: Outcome, expected: Expected) -> bool:
    return expected.verdict == "no_regression" and outcome.verdict == "regression"


def score(outcomes: list[Outcome], expected: dict[str, Expected]) -> dict:
    """The scores of `outcomes`, each a run of a case in `expected`: the four rates
    over all runs and per repetition, each case's runs, the flips, and the cost."""
    unknown = {o.case_id for o in outcomes} - expected.keys()
    if unknown:
        raise ValueError(f"no expected answer for {sorted(unknown)}")
    repetitions = sorted({o.run for o in outcomes})
    rates = {
        name: _rate(outcomes, expected, rule, repetitions)
        for name, rule in _RATES.items()
    }
    return {
        "runs": len(outcomes),
        "errors": sum(o.error is not None for o in outcomes),
        "repetitions": repetitions,
        "cases": {
            kind: sum(e.verdict == verdict for e in _scored(outcomes, expected))
            for kind, verdict in (("planted", "regression"), ("clean", "no_regression"))
        },
        "rates": rates,
        "per_case": _per_case(outcomes, expected),
        "cost": _cost(outcomes),
        "cache": _cache(outcomes),
    }


def _scored(outcomes, expected) -> list[Expected]:
    return [expected[c] for c in sorted({o.case_id for o in outcomes})]


def _detection(o: Outcome, e: Expected) -> tuple[int, int]:
    if e.verdict != "regression":
        return 0, 0
    return int(o.error is None and detected(o, e)), 1


def _attribution(o: Outcome, e: Expected) -> tuple[int, int]:
    if o.error is not None or not detected(o, e):
        return 0, 0
    return int(attributed(o, e)), 1


def _false_positive(o: Outcome, e: Expected) -> tuple[int, int]:
    if e.verdict != "no_regression" or o.error is not None:
        return 0, 0
    return int(false_positive(o, e)), 1


def _citation_validity(o: Outcome, e: Expected) -> tuple[int, int]:
    return o.citations_passed, o.citations_checked


# Each rate as (numerator, denominator) contributed by one run.
_RATES = {
    "detection": _detection,
    "attribution": _attribution,
    "false_positive": _false_positive,
    "citation_validity": _citation_validity,
}


def _rate(outcomes, expected, rule, repetitions) -> dict:
    def ratio(runs) -> tuple[int, int]:
        parts = [rule(o, expected[o.case_id]) for o in runs]
        return sum(n for n, _ in parts), sum(d for _, d in parts)

    hits, of = ratio(outcomes)
    by_run = []
    for r in repetitions:
        n, d = ratio([o for o in outcomes if o.run == r])
        by_run.append(None if d == 0 else n / d)
    known = [x for x in by_run if x is not None]
    return {
        "hits": hits,
        "of": of,
        "rate": None if of == 0 else hits / of,
        "by_run": by_run,
        "min": min(known) if known else None,
        "max": max(known) if known else None,
    }


def _per_case(outcomes, expected) -> list[dict]:
    cases = []
    for case_id in sorted({o.case_id for o in outcomes}):
        e = expected[case_id]
        runs = sorted(
            (o for o in outcomes if o.case_id == case_id), key=lambda o: o.run
        )
        marks = {
            "verdicts": [o.verdict for o in runs],
            "detected": [detected(o, e) for o in runs],
            "attributed": [attributed(o, e) for o in runs],
            "false_positive": [false_positive(o, e) for o in runs],
        }
        cases.append(
            {
                "case": case_id,
                "expected": e.verdict,
                **marks,
                "errors": [o.error for o in runs],
                "flipped": any(len(set(values)) > 1 for values in marks.values()),
            }
        )
    return cases


def _cache(outcomes: list[Outcome]) -> dict:
    """The runs from the second repetition on, and those that read no cached token."""
    checked = [o for o in outcomes if o.run >= 2 and o.error is None]
    missing = [
        f"{o.case_id}/{o.run}"
        for o in sorted(checked, key=lambda o: (o.case_id, o.run))
        if o.usage["cache_read_input_tokens"] == 0
    ]
    return {"checked": len(checked), "missing": missing}


def _cost(outcomes: list[Outcome]) -> dict:
    ran = [o for o in outcomes if o.error is None]
    usage = {f: sum(o.usage[f] for o in ran) for f in USAGE_FIELDS}
    return {
        "usd": round(sum(o.usd for o in outcomes), 6),
        "usd_per_run": round(mean(o.usd for o in ran), 6) if ran else None,
        "usage": usage,
        "usage_per_run": {f: round(n / len(ran), 1) for f, n in usage.items()}
        if ran
        else None,
        "wall_time_s": {
            "mean": round(mean(o.wall_time_s for o in ran), 1) if ran else None,
            "min": min((o.wall_time_s for o in ran), default=None),
            "max": max((o.wall_time_s for o in ran), default=None),
        },
    }
