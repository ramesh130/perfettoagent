"""CLI entry point. Subcommands (diagnose, review, eval, tp) land per PRD §10."""

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="perfettoagent",
        description="Perfetto trace + git range in, cited diagnosis out.",
    )
    parser.add_subparsers(dest="command")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
    return 0
