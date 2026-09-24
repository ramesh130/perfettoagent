"""CLI entry point. Subcommands (diagnose, review, eval, tp): docs/tech-stack.md."""

import argparse
import json
import sys
from pathlib import Path

from perfettoagent import models, run_metadata
from perfettoagent.agent import AUTO, RUN_ERRORS, diagnose
from perfettoagent.credentials import redact
from perfettoagent.evalrun import RESULTS_DIR, RUNS, results_name, run_eval
from perfettoagent.git import GitError
from perfettoagent.metrics import UnknownMetric
from perfettoagent.query import MAX_ROWS, QueryRejected, query_trace
from perfettoagent.report import render
from perfettoagent.review import FEEDBACK, ReviewRefused, review
from perfettoagent.trace_processor import TraceProcessorError
from perfettoagent.verify import RangeError

# Exit statuses. 2 matches argparse's own usage errors: the input was refused as given.
EXIT_OK = 0
EXIT_FAILED = 1
EXIT_REJECTED = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="perfettoagent",
        description="Perfetto trace + git range in, cited diagnosis out.",
    )
    commands = parser.add_subparsers(dest="command")

    dx = commands.add_parser(
        "diagnose",
        help="diagnose a trace pair against a git range, and write diagnosis.json",
        description=(
            "Run the agent on a baseline and a current trace and a range of the target "
            "repo, verify every claim it makes, and write diagnosis.json (schema 1). "
            "Calls the OpenAI API (OPENAI_API_KEY) or the Anthropic API "
            "(ANTHROPIC_API_KEY, or an `ant auth login` profile); a key is read from "
            "the environment, else from ./.env."
        ),
    )
    dx.add_argument("--baseline", required=True, help="the trace before the change")
    dx.add_argument("--current", required=True, help="the trace after the change")
    dx.add_argument("--repo", required=True, help="the target app's git repo")
    dx.add_argument(
        "--range", required=True, dest="git_range", help="base..head, two commits"
    )
    dx.add_argument(
        "--metric",
        default=AUTO,
        help=f"a library metric, or {AUTO} (default) for the agent to choose",
    )
    dx.add_argument(
        "--provider",
        choices=models.PROVIDERS,
        default=models.DEFAULT_PROVIDER,
        help=f"the model provider (default: {models.DEFAULT_PROVIDER})",
    )
    dx.add_argument(
        "--model",
        help="a model id with a price row (default: the provider's own: "
        + ", ".join(f"{m} on {p}" for p, m in models.DEFAULT_MODELS.items())
        + ")",
    )
    dx.add_argument(
        "--effort",
        default=models.DEFAULT_EFFORT,
        help=(
            f"how hard the model reasons: {', '.join(models.SWEPT_EFFORTS)} "
            f"(default: {models.DEFAULT_EFFORT}); a level the model does not list is "
            "refused, never rounded"
        ),
    )
    dx.add_argument(
        "--run-json",
        type=Path,
        help=(
            "the current capture's run metadata (schema 1): its commit must be inside "
            "--range; a dirty tree or a debuggable build becomes a caveat"
        ),
    )
    dx.add_argument(
        "--out",
        type=Path,
        default=Path("diagnosis.json"),
        help=(
            "where to write the diagnosis (default: diagnosis.json); the report, "
            "diagnosis.md, goes beside it with the suffix .md"
        ),
    )

    rv = commands.add_parser(
        "review",
        help="record a person's answer to a diagnosis in evals/feedback.jsonl",
        description=(
            "Accept, reject or partly accept the diagnosis.json in OUT_DIR, and append "
            "the answer, with the sha256 of both traces, the range and the diagnosis, "
            "to the feedback file. Nothing else is written."
        ),
    )
    rv.add_argument("out_dir", type=Path, help="the directory holding diagnosis.json")
    rv.add_argument(
        "--feedback",
        type=Path,
        default=FEEDBACK,
        help="the file to append to (default: this repo's evals/feedback.jsonl)",
    )
    answers = rv.add_subparsers(dest="answer", required=True)
    answers.add_parser("accept", help="every kept claim is right")
    reject = answers.add_parser("reject", help="the diagnosis is wrong")
    reject.add_argument("reason", nargs="+", help="why, in words")
    partial = answers.add_parser("partial", help="some kept claims are right")
    partial.add_argument(
        "claim_ids", nargs="+", metavar="CLAIM_ID", help="the claims that are right"
    )

    ev = commands.add_parser(
        "eval",
        help="run every eval case N times and score the runs",
        description=(
            "Stage each eval case, diagnose it --runs times, write each run's result "
            "under --out, and score the runs against evals/answers/ (ADR-0027). A run "
            "with a result already is not run again, so an interrupted run resumes. "
            "Calls the model provider's API, like diagnose."
        ),
    )
    ev.add_argument(
        "--cases", nargs="+", metavar="CASE_ID", help="the cases to run (default: all)"
    )
    ev.add_argument(
        "--runs", type=int, default=RUNS, help=f"runs per case (default: {RUNS})"
    )
    ev.add_argument("--jobs", type=int, default=1, help="runs at once (default: 1)")
    ev.add_argument(
        "--out",
        type=Path,
        help="the results directory (default: evals/results/<model>-<effort>-<metric>)",
    )

    tp = commands.add_parser(
        "tp",
        help="run one SELECT on a trace through the pinned trace processor",
        description=(
            "Run one SELECT (or WITH ... SELECT) query on a trace, exactly as the "
            f"agent's query_trace tool does: at most {MAX_ROWS} rows are shown, and "
            "the true row count is always reported."
        ),
    )
    tp.add_argument("--trace", required=True, help="path to a Perfetto trace file")
    tp.add_argument("--sql", required=True, help="a single SELECT or WITH query")
    tp.add_argument(
        "--json",
        action="store_true",
        help="print the query_trace result as JSON, as the agent sees it",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return EXIT_OK
    if args.command == "diagnose":
        return _diagnose(args)
    if args.command == "review":
        return _review(args)
    if args.command == "eval":
        return _eval(args)
    return _tp(args)


def _diagnose(args: argparse.Namespace) -> int:
    if _report_path(args.out) == args.out:
        # The report would overwrite the diagnosis it is rendered from.
        print(
            f"perfettoagent diagnose: rejected: --out {args.out} ends in .md, the "
            "report's suffix; name the diagnosis .json",
            file=sys.stderr,
        )
        return EXIT_REJECTED
    try:
        metadata = run_metadata.load(args.run_json) if args.run_json else None
        diagnosis = diagnose(
            baseline=args.baseline,
            current=args.current,
            repo=args.repo,
            git_range=args.git_range,
            metric=args.metric,
            provider=args.provider,
            model=args.model,
            effort=args.effort,
            metadata=metadata,
        )
    except (
        FileNotFoundError,
        RangeError,
        UnknownMetric,
        GitError,
        models.ModelRefused,
        run_metadata.RunMetadataInvalid,
    ) as e:
        # Refused before any request: the inputs as given cannot be diagnosed.
        print(f"perfettoagent diagnose: rejected: {e}", file=sys.stderr)
        return EXIT_REJECTED
    except RUN_ERRORS as e:
        # Nothing is written: a diagnosis.json that exists has been verified. An API
        # error can quote part of the key it was sent; none is printed.
        print(f"perfettoagent diagnose: {redact(str(e))}", file=sys.stderr)
        return EXIT_FAILED
    args.out.write_text(json.dumps(diagnosis, indent=2) + "\n")
    _report_path(args.out).write_text(render(diagnosis))
    print(_summary(diagnosis, args.out))
    return EXIT_OK


def _report_path(out: Path) -> Path:
    """Where diagnosis.md goes: beside `out`, with the suffix .md."""
    return out.with_suffix(".md")


def _summary(diagnosis: dict, out: Path) -> str:
    """One line: the verdict, what survived the verifier, and what the run cost."""
    run = diagnosis["run"]
    culprit = diagnosis["culprit"]
    commit = f", commit {culprit['commit'][:12]}" if culprit else ""
    return (
        f"{diagnosis['verdict']}{commit}: {len(diagnosis['claims'])} claims kept, "
        f"{len(diagnosis['dropped_claims'])} dropped; {run['tool_calls']} tool calls, "
        f"${run['usd']:.4f}, {run['wall_time_s']:.0f} s -> {out}"
    )


def _review(args: argparse.Namespace) -> int:
    try:
        line = review(
            args.out_dir,
            args.answer,
            reason=" ".join(args.reason) if args.answer == "reject" else None,
            claim_ids=args.claim_ids if args.answer == "partial" else (),
            feedback=args.feedback,
        )
    except ReviewRefused as e:
        print(f"perfettoagent review: rejected: {e}", file=sys.stderr)
        return EXIT_REJECTED
    print(
        f"{line['answer']}: {len(line['claims_accepted'])} claims accepted, "
        f"{len(line['claims_rejected'])} rejected -> {args.feedback}"
    )
    return EXIT_OK


def _eval(args: argparse.Namespace) -> int:
    if args.runs < 1 or args.jobs < 1:
        print("perfettoagent eval: rejected: --runs and --jobs are at least 1",
              file=sys.stderr)  # fmt: skip
        return EXIT_REJECTED
    provider, effort, metric = models.DEFAULT_PROVIDER, models.DEFAULT_EFFORT, AUTO
    model = models.DEFAULT_MODELS[provider]
    out = args.out or RESULTS_DIR / results_name(model, effort, metric)
    scores = run_eval(
        out,
        cases=args.cases,
        runs=args.runs,
        provider=provider,
        model=model,
        effort=effort,
        metric=metric,
        jobs=args.jobs,
    )
    rates = scores["rates"]
    print(
        f"detection {rates['detection']['hits']}/{rates['detection']['of']}, "
        f"attribution {rates['attribution']['hits']}/{rates['attribution']['of']}, "
        f"false positives {rates['false_positive']['hits']}/"
        f"{rates['false_positive']['of']}; {scores['errors']} errors; "
        f"${scores['cost']['usd']:.4f} -> {out}"
    )
    return EXIT_OK


def _tp(args: argparse.Namespace) -> int:
    try:
        result = query_trace(args.sql, args.trace)
    except QueryRejected as e:
        print(f"perfettoagent tp: rejected: {e}", file=sys.stderr)
        return EXIT_REJECTED
    except TraceProcessorError as e:
        print(f"perfettoagent tp: {e}", file=sys.stderr)
        return EXIT_FAILED
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(_format_table(result))
    return EXIT_OK


def _format_table(result: dict) -> str:
    """Renders a query_trace result as an aligned text table with a row-count footer."""
    header = [str(c) for c in result["columns"]]
    body = [[_cell(v) for v in row] for row in result["rows"]]
    widths = [max(len(cell) for cell in col) for col in zip(header, *body, strict=True)]

    def line(cells: list[str]) -> str:
        return "  ".join(
            c.ljust(w) for c, w in zip(cells, widths, strict=True)
        ).rstrip()

    lines = [line(header), line(["-" * w for w in widths])]
    lines += [line(row) for row in body]
    count = result["row_count"]
    footer = f"({count} row{'' if count == 1 else 's'}"
    if result["truncated"]:
        footer += f"; showing the first {len(result['rows'])}"
    lines.append(footer + ")")
    return "\n".join(lines)


def _cell(value) -> str:
    # One line per row: a newline inside a value would break the table.
    return "NULL" if value is None else str(value).replace("\n", "\\n")
