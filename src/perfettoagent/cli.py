"""CLI entry point. Subcommands (diagnose, review, eval, tp): docs/tech-stack.md."""

import argparse
import json
import sys
from pathlib import Path

import anthropic

from perfettoagent.agent import AUTO, RunFailed, diagnose
from perfettoagent.diagnosis import DiagnosisInvalid
from perfettoagent.git import GitError, GitUnavailable
from perfettoagent.metrics import UnknownMetric
from perfettoagent.query import MAX_ROWS, QueryRejected, query_trace
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
            "Calls the Anthropic API, with credentials from ANTHROPIC_API_KEY or an "
            "`ant auth login` profile."
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
        "--out",
        type=Path,
        default=Path("diagnosis.json"),
        help="where to write the diagnosis (default: diagnosis.json)",
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
    return _tp(args)


def _diagnose(args: argparse.Namespace) -> int:
    try:
        diagnosis = diagnose(
            baseline=args.baseline,
            current=args.current,
            repo=args.repo,
            git_range=args.git_range,
            metric=args.metric,
        )
    except (FileNotFoundError, RangeError, UnknownMetric, GitError) as e:
        # Refused before any request: the inputs as given cannot be diagnosed.
        print(f"perfettoagent diagnose: rejected: {e}", file=sys.stderr)
        return EXIT_REJECTED
    except (
        anthropic.AnthropicError,
        DiagnosisInvalid,
        RunFailed,
        GitUnavailable,
        TraceProcessorError,
    ) as e:
        # Nothing is written: a diagnosis.json that exists has been verified.
        print(f"perfettoagent diagnose: {e}", file=sys.stderr)
        return EXIT_FAILED
    args.out.write_text(json.dumps(diagnosis, indent=2) + "\n")
    print(_summary(diagnosis, args.out))
    return EXIT_OK


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
