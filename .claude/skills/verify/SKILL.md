---
name: verify
description: Run the offline quality gate for perfettoagent (ruff lint, ruff format check, pytest with no network). Use before declaring a change done or before committing.
---

Run the gate that matches the PRD week-1 exit criterion: "`pytest` is green with no network".

1. If `pyproject.toml` does not exist yet, say so and stop. There is nothing to verify.
2. Run these in order from the repo root and capture each one's output:
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run pytest -q $ARGUMENTS`
3. Tests must not need network access or `ANTHROPIC_API_KEY`. If a test fails because it
   tried to download (e.g. `trace_processor_shell`) or call the API, that is a bug in the
   test. Fixtures and the pinned binary cache belong in the repo or under
   `~/.cache/perfettoagent`. Report it as a bug, and don't "fix" it by skipping the test.
4. Report results as they are: pass/fail per step, with the failing output. Do not
   summarise a failure as a pass. Never weaken, skip, or delete a verifier test
   (`tests/…verifier…`) to make the gate pass.
