# Four jank traces join the fixtures, and LFS now holds about 198 MB

ADR-0010 asked each issue that adds fixtures to recheck the LFS total against the quota and record the new figure. The frame metrics (issue #8, ADR-0011) add four of superPlayer PR #392's fifteen jank captures, gzipped with `gzip -9 -n` as ADR-0010 requires. Affects `tests/fixtures/large/` and `tests/conftest.py`.

| Fixture | Capture | Raw | Gzipped |
|---|---|---:|---:|
| `jank-a-baseline.perfetto-trace.gz` | B1, clean | 30.2 MB | 11.8 MB |
| `jank-a-rerun.perfetto-trace.gz` | C1, clean, same build as B1 | 31.6 MB | 12.2 MB |
| `jank-b-current.perfetto-trace.gz` | G1, one change | 34.0 MB | 11.9 MB |
| `jank-c-current.perfetto-trace.gz` | R1, another change | 184.3 MB | 32.8 MB |

- **Names.** They follow ADR-0004's rule: each says what role the capture plays, never what changed. `b` and `c` tell the two changed captures apart; both are compared against `jank-a-baseline`. `conftest.jank_traces` returns all four by role. Issue #9 can reuse them, for example `baseline`, `rerun` and `current_b` for `gc_time_ms`, rather than add more.
- **Only four are committed.** The other eleven captures were used only to measure the clean spread (ADR-0011), and their numbers are recorded there. That includes the tap-sleep plant: issue #9 adds that capture if it needs one.
- **`-n`.** It leaves the file name and time out of the gzip header, so re-compressing the same capture gives the same bytes and LFS does not store it twice.

## Consequences

- **The LFS total is 197.9 MB** (197,903,119 bytes over nine files): 46.7 MB of heap dumps, 82.5 MB of startup traces and 68.7 MB of jank traces. The 1 GB monthly bandwidth quota now allows about 5 full fetches: CI runs, plus fresh clones with LFS. CI is still manual-only. The storage quota is 20% used.
- A full fetch is now five times larger than when ADR-0004 was written. The next issue to add fixtures should first consider re-compressing the heap dumps, which would save about 37 MB (ADR-0010).
