# symbolize reads a frame id, and deobfuscates with R8's text mapping

Issue #25 adds `symbolize(frame)`. The issue leaves open three things: what `frame` is, how a minified name is read back to its source name, and which fixture it is tested on. None of the ten large fixtures had a `stack_profile_frame` row, so a new capture was needed. This ADR records all three, and the new LFS total. Affects `src/perfettoagent/symbolize.py`, `src/perfettoagent/r8_mapping.py`, `tests/fixtures/large/`, `tests/conftest.py` and `docs/tech-stack.md` (the tool table, and the Large fixtures row).

## `frame` is a `stack_profile_frame` id, with `which`

`docs/tech-stack.md` had `symbolize(frame)`. The tool takes `frame`, an integer id, and `which`, `baseline` or `current`, as `query_trace` does. The alternative was a frame name, the text the model sees in a query result.

- **An id names one row, and a name does not.** In the fixture, `qh0.handleMessage` is two frames: one interpreted from `base.vdex` and one compiled into the JIT cache. Whether a frame is Java at all comes from its mapping (below), and a name alone does not have one.
- **The result can be cited.** It carries `sql_used`, a SELECT on that id, which the verifier re-runs like any other query.
- **Ids are per trace.** So `which` is required, and the description says the two traces' ids differ.
- **The model finds ids where it finds samples.** `perf_sample.callsite_id` → `stack_profile_callsite.frame_id`. The description names that path.

## Deobfuscation parses R8's `mapping.txt` in Python

The two options were:

- **Trace processor's own deobfuscation.** It fills `stack_profile_frame.deobfuscated_name` from `DeobfuscationMapping` packets in the trace. We would have to write those packets ourselves, as protobuf, and append them to a copy of each trace. Perfetto's own converter for that (`traceconv deobfuscate`) is a second native binary to download, pin and verify. Either way, the trace we query is no longer the trace the user gave.
- **Parse the mapping file here.** `mapping.txt` is R8's documented text format, not protobuf, so `docs/tech-stack.md`'s rule that nothing parses the protobuf still holds.

Parsed here, for these reasons:

- **No new binary, and the trace stays as captured.** `sql_used` re-runs on the user's own file.
- **The answer can be honest about ambiguity.** A sampled frame has no line number. Trace processor keeps one name per frame, and R8 can give one short name to several source methods. The fixture has examples: `p.b` is two lambdas from different classes, which R8 merged. The parser keeps every candidate and picks none. A wrong pick would send the model to grep for the wrong method.

The rules, in `r8_mapping.py`, follow R8's retrace:

- Lines with the same obfuscated line range form one inline stack, and the outermost method in it is the frame's method.
- Inlined callees are not candidates.
- A method R8 synthesized is a candidate only when no source method is.

If a trace does carry `deobfuscated_name`, that name is used as it is.

## One mapping per side

Each build has its own mapping, because R8 renames each build afresh. So the tool context, `TraceContext`, holds a mapping per side, and a side without one gets `no_mapping`. The `--mapping` CLI flag arrives with the agent loop (#29), and it has to accept one mapping per side too.

## What the tool returns

- **`kind: java`.** The frame is in a file ART runs Java from, and its name is `Class.method`. Those files are `.oat`, `.odex`, `.vdex`, `.apk`, `.jar`, `.dex`, and the JIT cache. `symbol` holds the candidates and their `source`:
  - `mapping` or `class_only` when they were deobfuscated;
  - `trace` when the trace carried the source name;
  - `no_mapping` or `not_in_mapping` otherwise. Then the name is returned exactly as the trace has it, and `deobfuscated` is false.
- **`kind: native`.** Code from a `.so` file, the kernel or ART's interpreter. `symbol` is null.
- **`kind: art_stub`.** A frame in an ART file whose name is not a method's: `art_jni_trampoline`, `QuickImtConflictTrampoline`, and `[DEDUPED] ?` for code shared by several methods. `symbol` is null. These appeared in the capture, and without this kind they would have come back as a class `""` and a method `art_jni_trampoline`.

## The fixture: `callstacks-a`

It was captured on 2026-09-24 on AVD `superplayer_verify_36`: API 36, arm64, userdebug, `sdk_gphone64_arm64` build `BE4B.251210.005`, with the device's Perfetto v51.2.

- **The build.** A scratch clone of superPlayer at `9fdd93c`, with one change to the demo's `benchmark` build type: `isMinifyEnabled = true` with `proguard-android-optimize.txt`. It is still profileable, not debuggable, as devicelab builds it. R8 9.4.14 wrote a 48 MB `mapping.txt`. Nothing depends on superPlayer at test time: the trace and the trimmed mapping are copied in.
- **The capture.** `./gradlew --max-workers=2 assembleBenchmark` in `demo/`, then `adb install -r` of the APK and `adb shell am start -W -n com.superplayer.demo/.MainActivity` (a cold start). Then `adb shell "cat /data/local/tmp/perf.pbtxt | perfetto --txt -c - -o /data/misc/perfetto-traces/cap.pftrace"` ran for 8 s with the config below. Meanwhile `adb shell input swipe 540 1800 540 600 300`, and the same swipe reversed, scrolled the feed up and down six times, 0.6 s apart.

  ```
  data_sources { config { name: "linux.perf" perf_event_config {
    timebase { counter: SW_CPU_CLOCK frequency: 100 timestamp_clock: PERF_CLOCK_MONOTONIC }
    callstack_sampling { scope { target_cmdline: "com.superplayer.demo" } kernel_frames: false } } } }
  data_sources { config { name: "linux.process_stats" process_stats_config { scan_all_processes_on_start: true } } }
  ```

  `SW_CPU_CLOCK` needs no hardware PMU. The first capture worked.
- **What trace processor 58.2 reads from it.**
  - 3,184 `perf_sample` rows, 554 frames and 47 mappings.
  - About 70 frames come from the app's `base.vdex` and 22 from the JIT cache, all with R8 names (`gf1.z`, `qh0.handleMessage`), and none deobfuscated.
  - Framework frames keep their names (`android.view.Choreographer.doFrame`).
  - Native frames carry their mangled or plain C names.
- **Size.** 212,005 bytes raw, and 74,746 bytes after `gzip -9 -n` (ADR-0010, ADR-0012), as `tests/fixtures/large/callstacks-a.perfetto-trace.gz`.
- **The mapping, trimmed.** The full 48 MB file is cut down to the header, plus each class that a Java frame in the fixture names. Each such class keeps its class line and the member lines of the method names those frames use.
  - That is 87 classes, 8,171 lines and 1,231,863 bytes. It is still too large for plain git, so it is in LFS next to its trace, gzipped like it (`gzip -9 -n`), at 73,316 bytes: `tests/fixtures/large/callstacks-a.mapping.txt.gz`. `Mapping.read` opens a `.gz` file as it is.
  - Every Java frame in the fixture symbolizes the same with the trimmed file as with the full one. That was checked when it was cut, with a one-off script that was not committed; the tests pin the results for the frames they name.
  - The file's header says it is trimmed.
- **The name.** It says what the capture is, never what it shows (ADR-0004).

## Consequences

- **The LFS total grows by 148,062 bytes, over two files.**
  - The test fixtures, which are what a default fetch downloads, are now 209.9 MB (209,898,944 bytes over twelve files).
  - All stored objects, test fixtures and eval cases alike, counted once per object, are now 324.3 MB (324,341,464 bytes) of the 1 GB storage quota.
  - Both figures are summed from the pointer files' `size` lines. Before this change, the same sums give 209.8 MB (209,750,882 bytes) and 324.2 MB (324,193,402 bytes). The first matches ADR-0013. ADR-0015 gives 197.9 MB and 312.3 MB instead, figures that leave out ADR-0013's sleep capture of 11.8 MB. The sums above are the ones to carry forward.
- **The sampled frames have no line numbers.** So `symbolize` cannot say which of several candidates ran, nor whether the sample landed in inlined code. The description says so.
- **Mapping names are the only test of which frames are Java.** The fixture covers `.vdex`, `.oat`, `.jar` and the JIT cache; AOT-compiled app code (`.odex`) is covered by a unit test only.
