"""Run the eval cases and score them (ADR-0016): the same as `perfettoagent eval`.

uv run python evals/run_eval.py [--cases ID ...] [--runs 3] [--jobs 1] [--out DIR]
"""

import sys

from perfettoagent.evalrun import main

if __name__ == "__main__":
    sys.exit(main())
