# Manual triage baseline: assumed, not measured

Issue #27 asks for the five planted superPlayer cases to be triaged by hand and timed. That has
not been done. At the project owner's direction, the sweep (#36) goes ahead with an assumed
baseline instead, and every table that uses it says so.

| Case | Minutes (assumed) | Culprit found (assumed) |
|---|---:|---|
| `275adbfb` | 60 | yes |
| `462439ff` | 60 | yes |
| `69dc18c7` | 60 | yes |
| `c89d5055` | 60 | yes |
| `f21c443c` | 60 | yes |

- **Why 60 minutes.** The mission puts getting from a perf alert to the culprit by hand at
  "hours". One hour a case is the conservative end, so a comparison cannot make the agent look
  better by overstating the manual time.
- **What replaces it.** Measured times, from opening the staged traces to naming a commit (or
  giving up), triaged from the staged inputs only. Then `triage.json`'s `measured` becomes
  true, and #27 closes.
