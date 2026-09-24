"""`symbolize`: one frame of a trace's callstacks, as a Java/Kotlin class and method the
target repo can be grepped for (roadmap item 6, issue #25, ADR-0019).

A frame is a row of `stack_profile_frame`, named by its id in one of the run's two
traces. The row is read through `query_trace`, so the lookup is one SELECT that the
result carries as `sql_used`, and a claim citing it can be re-run by the verifier.

ART names a Java frame `package.Class.method`; in a minified build that is R8's short
name, `aj0.b`. With the build's `mapping.txt` the name is read back to its source
(`perfettoagent.r8_mapping`). Without one, or for a name the mapping lacks, it comes
back as the trace has it, and `deobfuscated` says so: an obfuscated name passed on
unmarked would read as source. If the trace itself carries a deobfuscated name
(`stack_profile_frame.deobfuscated_name`, filled when a capture embedded the mapping),
that is used as it is.

A native frame (C/C++, the kernel, ART's own runtime) has no class or method, so its
`symbol` is null. Which kind a frame is comes from the file its code was mapped from,
`stack_profile_mapping.name`, not from its name: ART runs Java code from `.oat`,
`.odex` and `.vdex` files, dex inside an `.apk` or `.jar`, or its JIT cache; native
code runs from `.so` files and the kernel. A frame in one of ART's files whose name is
not a method's (`art_jni_trampoline`) is ART's own glue: its `symbol` is null too.
ref: https://perfetto.dev/docs/quickstart/callstack-sampling
ref: https://source.android.com/docs/core/runtime/jit-compiler
"""

import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from perfettoagent.diagnosis import SIDES
from perfettoagent.query import query_trace
from perfettoagent.r8_mapping import Mapping, Method
from perfettoagent.tools import INTEGER, Tool, ToolInputError, described, strict_input

# The file names ART runs Java code from: compiled ahead of time (`.oat`, `.odex`,
# `.vdex`), or interpreted from dex (in an `.apk`, a `.jar` or a bare `.dex`).
# ref: https://source.android.com/docs/core/runtime/configure#how_art_works
_JAVA_FILE = re.compile(r"\.(oat|odex|vdex|apk|jar|dex)$")

# ART's JIT cache: an anonymous mapping, not a file. Its name depends on how the
# release creates it: `dalvik-jit-code-cache` for anonymous shared memory (API 36, in
# the fixture), `jit-cache` for a memfd, and `jit-zygote-cache` for the cache the
# zygote fills before forking an app.
# ref: https://cs.android.com/android/platform/superproject/main/+/main:art/runtime/jit/jit_memory_region.cc
_JIT_CACHE = re.compile(r"jit-(zygote-)?cache|dalvik-jit-code-cache")

# `/proc/<pid>/maps` appends this to the path of a file unlinked while mapped, which is
# how a memfd (a JIT cache) shows.
# ref: https://man7.org/linux/man-pages/man5/proc_pid_maps.5.html
_DELETED = " (deleted)"

# How ART names a Java method in a frame: `package.Class.method`, with no signature.
# Kotlin adds `$` (`draw$ui`, an internal member) and `-` (`paint-LG529CI`, a function
# taking an inline class) to JVM names; constructors are `<init>` and `<clinit>`. In the
# same files ART also runs code that is no one method: its trampolines
# (`art_jni_trampoline`) and code shared by several methods, named `[DEDUPED] ?`. Those
# names do not match, and their frames get no symbol.
# ref: https://kotlinlang.org/docs/inline-classes.html#mangling
_JAVA_NAME = re.compile(
    r"(?P<class>[A-Za-z_$][\w$-]*(?:\.[A-Za-z_$][\w$-]*)*)"
    r"\.(?P<method><init>|<clinit>|[A-Za-z_$][\w$-]*)"
)

# Where a Java frame's candidates came from, as `symbol.source`. The first three are
# source names; with the other two the trace's name is returned as it is.
FROM_TRACE = "trace"  # the trace carried `deobfuscated_name`
FROM_MAPPING = "mapping"
CLASS_ONLY = "class_only"  # the class was mapped, and the method kept its name
NO_MAPPING = "no_mapping"  # the run has no mapping for this side
NOT_IN_MAPPING = "not_in_mapping"  # not the app's code, or another build's
_DEOBFUSCATED = {FROM_TRACE, FROM_MAPPING, CLASS_ONLY}


@dataclass(frozen=True)
class TraceContext:
    """What a run binds for the trace tools, and the model never names: the two traces
    by side (`baseline`, `current`), and for each side whose build was minified, its
    R8 mapping. Each side has its own, because each build has its own names."""

    traces: dict[str, Path]
    mappings: dict[str, Mapping] = field(default_factory=dict)
    binary: Path | None = None


def frame_sql(frame: int) -> str:
    """The SELECT that reads one frame and the file its code was mapped from."""
    return (
        "SELECT f.id, f.name, f.deobfuscated_name, m.name AS mapped_file\n"
        "FROM stack_profile_frame AS f\n"
        "LEFT JOIN stack_profile_mapping AS m ON m.id = f.mapping\n"
        f"WHERE f.id = {int(frame)}"
    )


def symbolize(context: TraceContext, frame: int, which: str) -> dict:
    """Frame `frame` of the `which` trace, as a class and method, or a null `symbol`
    for a native frame."""
    trace = context.traces.get(which)
    if trace is None:
        raise ToolInputError(f"which: this run has no {which!r} trace")
    sql = frame_sql(frame)
    rows = query_trace(sql, trace, binary=context.binary)["rows"]
    if not rows:
        raise ToolInputError(
            f"frame: {frame} is not a stack_profile_frame id in the {which} trace"
        )
    _, name, deobfuscated_name, mapped_file = rows[0]
    result = {
        "which": which,
        "frame": frame,
        "name": name,
        "mapped_file": mapped_file,
        "sql_used": sql,
    }
    if not is_java(mapped_file):
        return {**result, "kind": "native", "symbol": None}
    java_name = _JAVA_NAME.fullmatch(name or "")
    if java_name is None:
        return {**result, "kind": "art_stub", "symbol": None}
    raw = Method(java_name["class"], java_name["method"], signature=None)
    r8 = context.mappings.get(which)
    return {
        **result,
        "kind": "java",
        "symbol": _java_symbol(raw, deobfuscated_name, r8),
    }


def is_java(mapped_file: str | None) -> bool:
    """Whether code mapped from this file is Java/Kotlin run by ART."""
    if not mapped_file:
        return False
    path = mapped_file.removesuffix(_DELETED)
    return bool(_JAVA_FILE.search(path) or _JIT_CACHE.search(path))


def _java_symbol(raw: Method, from_trace: str | None, r8: Mapping | None) -> dict:
    """A Java frame's class and method: its candidates, and where they came from."""
    if from_trace:
        class_name, _, method = from_trace.rpartition(".")
        return _symbol(FROM_TRACE, [Method(class_name, method, signature=None)])
    if r8 is None:
        return _symbol(NO_MAPPING, [raw])
    methods = r8.methods(raw.class_name, raw.method)
    if methods:
        return _symbol(FROM_MAPPING, methods)
    original = r8.original_class(raw.class_name)
    if original is not None:
        return _symbol(CLASS_ONLY, [replace(raw, class_name=original)])
    return _symbol(NOT_IN_MAPPING, [raw])


def _symbol(source: str, candidates: list[Method]) -> dict:
    return {
        "candidates": [m.as_dict() for m in candidates],
        "deobfuscated": source in _DEOBFUSCATED,
        "source": source,
    }


SYMBOLIZE = Tool(
    name="symbolize",
    description=(
        "Turn one frame of a trace's callstacks into the Java/Kotlin class and method "
        "it ran, a name you can grep the target repo for. `frame` is an id from "
        "stack_profile_frame (reach it from a sample through stack_profile_callsite's "
        "frame_id; a sample's callsite_id is the top of its stack) in the `which` "
        "trace; ids differ between the two traces. When the run was given the build's "
        "R8 mapping, an obfuscated name like `aj0.b` is read back to its source name. "
        "`symbol.source` says how: `mapping`; `class_only` (the class was mapped, the "
        "method kept its name); `trace` (the trace carried the name already); "
        "`no_mapping` or `not_in_mapping`, where the name is returned exactly as the "
        "trace has it and `deobfuscated` is false (the Android framework's code is not "
        "in the app's mapping). A minified method can stand for several source methods;"
        " all are listed in `candidates`, none is picked. For a native frame (C/C++, "
        "ART's runtime, the kernel; `kind` native) or one of ART's stubs (`kind` "
        "art_stub) `symbol` is null. It cannot tell you the source line, which of "
        "several candidates ran, nor what code was inlined into the frame's method; nor"
        " how hot the frame is: count samples with query_trace. Cite `sql_used` for the"
        " frame's raw name."
    ),
    input_schema=strict_input(
        frame=described(INTEGER, "A stack_profile_frame id."),
        which=described(
            {"type": "string", "enum": list(SIDES)}, "The trace the id is from."
        ),
    ),
    function=symbolize,
)
