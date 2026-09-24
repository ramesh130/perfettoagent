"""`diagnosis.md`: the verified diagnosis as a report a person reads (roadmap item 7,
issue #30, ADR-0024).

It is rendered from `diagnosis.json` alone, after the verifier: nothing here reads a
trace, the repo or the model's raw output, so the report cannot say what the verifier
dropped, except under "Dropped claims", where it says it was dropped and why.

The first ten lines carry the point: the verdict, the metric and its change, the
culprit or that there is none, and what the verifier kept. Then the metric table, each
claim followed by its evidence in fenced blocks, the caveats, the dropped claims and
the run's cost.

A trace citation's evidence is its SQL and the row count the verifier got re-running
it. Schema 1 keeps no rows (ADR-0006), and a row count is what the verifier checked;
`perfettoagent tp` re-runs the SQL for anyone who wants the rows. A commit citation's
evidence is the full sha the verifier resolved, and the path it checked.
"""

from perfettoagent import run_metadata
from perfettoagent.diagnosis import check_diagnosis

# Headline words for each verdict: what a reader skimming the first line needs.
_VERDICT_WORDS = {
    "regression": "Regression",
    "no_regression": "No regression",
    "inconclusive": "Inconclusive",
}

# The run-metadata caveats the header names, in the words it uses (ADR-0025).
_BUILD_CAVEATS = {
    run_metadata.CAVEAT_DIRTY: "uncommitted changes",
    run_metadata.CAVEAT_DEBUGGABLE: "debuggable",
}

# How many characters of a sha the prose shows; the evidence blocks show it in full.
_SHORT_SHA = 12


def render(diagnosis: dict) -> str:
    """`diagnosis` (DIAGNOSIS_SCHEMA) as Markdown. Raises DiagnosisInvalid for
    anything else, so a report is never rendered from an unverified output."""
    check_diagnosis(diagnosis)
    sections = [
        _headline(diagnosis),
        _metric_table(diagnosis["metric"]),
        _claims(diagnosis["claims"]),
        _caveats(diagnosis),
        _dropped(diagnosis["dropped_claims"]),
        _run(diagnosis["run"]),
    ]
    return "\n\n".join(s for s in sections if s) + "\n"


def _headline(d: dict) -> str:
    """The first ten lines: title, metric, culprit, verifier, the current build's
    caveats, a changed verdict, confidence."""
    v = d["verification"]
    lines = [
        f"# {_VERDICT_WORDS[d['verdict']]}",
        "",
        f"- **Metric:** {_metric_line(d['metric'])}",
        f"- **Culprit:** {_culprit_line(d['culprit'], v['culprit_dropped'])}",
        f"- **Verified:** {_count(len(d['claims']), 'claim')} kept, "
        f"{len(d['dropped_claims'])} dropped; {v['citations_passed']} of "
        f"{_count(v['citations_checked'], 'citation')} passed",
    ]
    build = [word for caveat, word in _BUILD_CAVEATS.items() if caveat in d["caveats"]]
    if build:
        lines.append(f"- **Current build:** {', '.join(build)}; see Caveats")
    if v["verdict_before"] != d["verdict"]:
        lines.append(
            f"- **Verdict changed** by the verifier from "
            f"`{v['verdict_before']}`: {v['explanation']}"
        )
    confidence = (
        f"{d['confidence']} (never scored)"
        if d["confidence"]
        else "none; the verifier changed what it was given for"
    )
    lines.append(f"- **Model's confidence:** {confidence}")
    return "\n".join(lines)


def _metric_line(metric: dict | None) -> str:
    if metric is None:
        return "none measured"
    unit = metric["unit"]
    change = (
        "no change measured"
        if metric["delta"] is None
        else f"{_signed(metric['delta'])} {unit}"
    )
    return (
        f"`{metric['name']}` {change} "
        f"({_number(metric['baseline'])} → {_number(metric['current'])} {unit})"
    )


def _culprit_line(culprit: dict | None, dropped: str | None) -> str:
    if culprit is not None:
        files = ", ".join(f"`{f}`" for f in culprit["files"]) or "no files named"
        return f"`{culprit['commit'][:_SHORT_SHA]}` ({culprit['attribution']}); {files}"
    if dropped is not None:
        return f"none attributed; the verifier dropped the model's: {dropped}"
    return "none attributed"


def _metric_table(metric: dict | None) -> str:
    if metric is None:
        return ""
    rows = [
        "## Metric",
        "",
        "| Metric | Unit | Baseline | Current | Delta |",
        "|---|---|---:|---:|---:|",
        f"| `{metric['name']}` | {metric['unit']} | {_number(metric['baseline'])} | "
        f"{_number(metric['current'])} | {_signed(metric['delta'])} |",
        "",
        "Measured by:",
        "",
        _fenced(metric["sql_used"], "sql"),
    ]
    return "\n".join(rows)


def _claims(claims: list) -> str:
    if not claims:
        return "## Claims\n\nNo claim survived the verifier."
    return "## Claims\n\n" + "\n\n".join(_claim(c) for c in claims)


def _claim(claim: dict, reason: str | None = None) -> str:
    parts = [f"### {claim['id']}. {_one_line(claim['text'])}"]
    if reason is not None:
        parts.append(f"Dropped: {_one_line(reason)}")
    parts += [_evidence(c) for c in claim["citations"]]
    return "\n\n".join(parts)


def _evidence(citation: dict) -> str:
    failed = f" Failed: {_one_line(citation['error'])}" if citation["error"] else ""
    if citation["kind"] == "trace":
        count = citation["row_count"]
        rows = "" if count is None else f" {_count(count, 'row')}."
        return (
            f"The `{citation['trace']}` trace:{rows}{failed}\n\n"
            f"{_fenced(citation['sql'], 'sql')}"
        )
    path = f", changing `{citation['path']}`" if citation["path"] else ""
    sha = citation["commit"] or citation["sha"]
    return f"Commit{path}:{failed}\n\n{_fenced(sha, 'text')}"


def _caveats(d: dict) -> str:
    notes = list(d["caveats"])
    if d["verification"]["metric_dropped"] is not None:
        notes.append(
            "the metric was dropped by the verifier: "
            + d["verification"]["metric_dropped"]
        )
    if not notes:
        return ""
    return "## Caveats\n\n" + "\n".join(f"- {_one_line(n)}" for n in notes)


def _dropped(dropped: list) -> str:
    if not dropped:
        return ""
    return "## Dropped claims\n\n" + "\n\n".join(
        _claim(c, reason=c["reason"]) for c in dropped
    )


def _run(run: dict | None) -> str:
    if run is None:
        return ""
    usage = run["usage"]
    return "\n".join(
        [
            "## Run",
            "",
            f"`{run['model']}` on {run['provider']}, effort {run['effort']}: "
            f"{run['tool_calls']} tool calls, ${run['usd']:.4f}, "
            f"{run['wall_time_s']:.0f} s.",
            f"Tokens: {usage['input_tokens']:,} input, "
            f"{usage['cache_read_input_tokens']:,} cache read, "
            f"{usage['cache_creation_input_tokens']:,} cache write, "
            f"{usage['output_tokens']:,} output.",
        ]
    )


def _fenced(text: str, language: str) -> str:
    """`text` in a code fence longer than any run of backticks inside it, so model-
    or trace-written text cannot close the fence early."""
    longest = run = 0
    for ch in text:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def _one_line(text: str) -> str:
    """Model-written prose on one line: a newline could start a heading or a list."""
    return " ".join(text.split())


def _count(n: int, noun: str) -> str:
    return f"{n:,} {noun}{'' if n == 1 else 's'}"


def _number(value: float | None) -> str:
    if value is None:
        return "no data"
    if isinstance(value, int):
        return f"{value:,}"
    # Two decimals at most: a metric's unit is ms, % or a count, and a finer digit is
    # noise to a reader, who has the SQL for the exact value.
    return f"{value:,.2f}".rstrip("0").rstrip(".")


def _signed(value: float | None) -> str:
    if value is None:
        return "–"
    return ("+" if value > 0 else "") + _number(value)
