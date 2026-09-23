# Large trace fixtures live in Git LFS

A metric is tested against a fixture trace with a known answer (roadmap item 3), and some of those traces are large: the first pair, two Java heap dumps, is about 45 MB (22–23 MB each). Plain git would keep every version of every such fixture in every clone forever. So traces that are too large for plain git go in `tests/fixtures/large/`, which `.gitattributes` stores in Git LFS. Smaller fixtures, like the 126 KB `tests/fixtures/tiny.perfetto-trace`, stay in plain git, so a clone without LFS still runs most of the suite. Affects `docs/tech-stack.md` (Language and tooling) and `.github/workflows/ci.yml`, whose checkout now fetches LFS objects.

The alternatives were plain git (every clone pays for every fixture version) and downloading fixtures at test time (the suite runs with sockets disabled, and a download is one more thing to pin and verify).

## Consequences

- GitHub's free LFS quota is 1 GB of storage and 1 GB of bandwidth a month. Each CI run and each fresh clone with LFS downloads every large fixture, about 45 MB today, so the bandwidth allows roughly 20 of them a month. CI is manual-only for now (`workflow_dispatch`), so this is not yet a constraint. Adding fixtures makes it one sooner.
- A clone made without LFS gets pointer files in place of the traces. The tests that need a large fixture detect a pointer and skip with a message saying how to fetch it (`git lfs pull`), rather than hand a pointer to the trace processor.
- Fixtures are named neutrally (`heap-a-baseline`, `heap-a-current`), never for what differs between them (CLAUDE.md, eval integrity).
