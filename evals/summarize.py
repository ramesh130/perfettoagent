"""Write evals/results/summary.md from the results sets (ADR-0031).

uv run python evals/summarize.py
"""

import sys

from perfettoagent.summary import main

if __name__ == "__main__":
    sys.exit(main())
