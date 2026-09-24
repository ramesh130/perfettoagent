# `diagnosis.md` is rendered from the verified `diagnosis.json`, and shows row counts, not rows

Issue #30 adds `diagnosis.md`, the report roadmap item 7 describes. The issue asks for each claim to be followed by "the SQL and rows, or the commit", and for the report to be rendered from `diagnosis.json` alone. Schema 1 keeps no rows, so the two conflict. This ADR records how they are reconciled. Affects `src/perfettoagent/report.py` and `cli.py`, and roadmap item 7.

## Decisions

- **Rendered from `diagnosis.json` alone.** `report.render` takes the file's contents and checks them against `DIAGNOSIS_SCHEMA` first. It reads no trace, no repo and nothing the model wrote before the verifier. So the report can only say what the verifier kept, plus what it dropped, under "Dropped claims" with the reason.
- **A trace citation's evidence is its SQL and its verified row count.** Schema 1 has no rows (ADR-0006), and fetching them would mean re-reading the traces, which the first criterion rules out. The row count is exactly what the verifier checked, and anyone who wants the rows runs the SQL with `perfettoagent tp`. Adding rows to schema 1 would need a version bump and a cap, which is not worth it for a report. A commit citation's evidence is the full sha the verifier resolved, and the path it checked.
- **The first ten lines.** The title is the verdict. Then one line each for the metric with its change and both values, the culprit (or "none attributed", with the verifier's reason when it dropped the model's), what the verifier kept, a line when the verifier changed the verdict, and the model's confidence, marked as never scored. At most seven lines.
- **Model and trace text cannot change the report's structure.** Prose goes on one line, so a newline cannot start a heading or a list. Every SQL string and sha goes in a fence longer than any run of backticks inside it.
- **Where it goes.** `diagnose` writes it beside `--out`, with the suffix `.md`, and only after `diagnosis.json` is written. An `--out` that already ends in `.md` is refused before any request (exit 2), since the report would overwrite the file it comes from.

## Consequences

- Roadmap item 7 no longer lists `diagnosis.md` as open.
- The golden files under `tests/fixtures/reports/` are regenerated with `UPDATE_GOLDEN=1 uv run pytest tests/test_report.py`, and the diff is reviewed by eye.
