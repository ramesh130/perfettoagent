# Size the jank plants from measured emulator noise, not the roadmap's defaults

The roadmap gave the allocation storm as 50k small objects per frame, and ADR-0007 gave layout thrash as a forced re-measure of each visible `LazyColumn` item. On the API 36 emulator, pilot runs for superPlayer PR #392 showed neither was visible above run-to-run noise:

- At 50k allocations only the GC count moved. With the allocations placed between frames, the trace just recorded fewer frames.
- The re-measure alone moved frame p50 but not p95.

A plant the metric can't see makes a useless eval case, so each plant is sized from measured noise, as the startup plant was:

- **Allocation storm:** 1,000,000 boxed floats in each scrolled frame's draw (a faint grain over the feed).
- **Layout thrash:** the ADR-0007 re-measure (each row's padding breathes by 4 dp), plus a title fitted to the row's width in 0.05 sp steps, so each measure does real text layout.

The pilot tables and the reasoning are in superPlayer's `devicelab/plants/README.md`.

**Consequence.** Layout thrash is still weak on `frame_p95_ms`: every planted run sits above every clean run, but the smallest gap is 2.7 ms, inside the 13.7 ms clean spread. Its strong signals are frame p50 (62–63 ms against 33–40 ms) and `Choreographer#doFrame` p95. The expected metric stays `frame_p95_ms` for now. Whether to add a p50 or doFrame metric to the library is for #8 to settle against this evidence. Affects `docs/roadmap.md` item 5 and issues #6, #8 and #10.
