# Large trace fixtures are gzipped, and LFS now holds about 129 MB

This ADR extends ADR-0004. That record put large traces in Git LFS, and its consequence was the free quota: 1 GB of storage and 1 GB of bandwidth a month, about 20 downloads of the 45 MB of fixtures it then covered. The startup metrics (issue #7) need three more traces: a baseline, a current capture and a clean re-run. Each is 20 cold starts and 70–75 MB raw, 216 MB for the three. That alone would cut the bandwidth to about 4 full downloads a month.

So new trace fixtures are stored gzipped (`gzip -9`), as `tests/fixtures/large/<name>.perfetto-trace.gz`. The pinned trace processor (58.2) reads gzip directly, so nothing decompresses them and the tests pass the `.gz` path as they are. The three startup traces are 26.8–28.8 MB each gzipped, 82.5 MB together, 2.6 times smaller than raw. Of the eight startup captures, only three are committed. The other five were used only to settle Q4 (ADR-0009), and their numbers are recorded there.

The existing heap fixtures stay as they are in this change, which is scoped to the startup metrics. They compress far better: `heap-a-baseline` goes from 23.2 MB to 4.9 MB. Re-compressing both would save about 37 MB on every fetch, but it would add about 10 MB of storage, because LFS keeps every version that has been pushed. That is a follow-up for whoever next needs bandwidth headroom.

## Consequences

- **The LFS total is 129.2 MB** (129,248,706 bytes over five files): 46.7 MB of heap dumps and 82.5 MB of startup traces. The 1 GB bandwidth quota now allows about 7 full fetches a month: CI runs, plus fresh clones with LFS. CI is still manual-only. The storage quota is 13% used.
- Each query decompresses its trace first. `select count(*) from slice` on the startup baseline took 2.8 s gzipped and 2.4 s raw.
- Issues #8 and #9 add their fixtures the same way. They should re-check this total against the quota and record the new figure.
