"""symbolize (issue #25, ADR-0019): a trace's frame as a Java/Kotlin class and method,
deobfuscated with the build's R8 mapping, and null for a native frame.

The fixture is a short callstack-sampling capture of a minified build, with that build's
mapping, trimmed to the classes and methods its frames name (ADR-0019).
"""

import pytest
from test_eval_cases import HINT_WORDS

from perfettoagent.query import query_trace
from perfettoagent.r8_mapping import Mapping
from perfettoagent.symbolize import SYMBOLIZE, TraceContext, is_java, symbolize
from perfettoagent.tools import ToolInputError

# --- The schema --------------------------------------------------------------------


def test_the_schema_is_strict():
    definition = SYMBOLIZE.definition()
    assert definition["strict"] is True
    schema = definition["input_schema"]
    assert schema["additionalProperties"] is False
    assert schema["required"] == list(schema["properties"]) == ["frame", "which"]
    assert schema["properties"]["which"]["enum"] == ["baseline", "current"]


def test_the_schema_matches_the_function():
    code = SYMBOLIZE.function.__code__
    params = list(code.co_varnames[1 : code.co_argcount])
    assert list(SYMBOLIZE.input_schema["properties"]) == params


def test_the_description_says_what_it_cannot_tell_and_that_native_is_null():
    description = SYMBOLIZE.description
    assert "cannot" in description
    assert "native frame" in description and "null" in description
    for word in HINT_WORDS:
        assert word not in description.lower()


def test_call_refuses_a_frame_that_is_not_an_integer_or_an_unknown_side():
    context = TraceContext(traces={})
    with pytest.raises(ToolInputError, match="expected integer"):
        SYMBOLIZE.call(context, {"frame": "aj0.b", "which": "current"})
    with pytest.raises(ToolInputError, match="which"):
        SYMBOLIZE.call(context, {"frame": 1, "which": "after"})


def test_a_side_the_run_lacks_is_refused():
    with pytest.raises(ToolInputError, match="no 'baseline' trace"):
        symbolize(TraceContext(traces={}), 1, "baseline")


# --- Which frames are Java ---------------------------------------------------------


@pytest.mark.parametrize(
    "mapped_file",
    [
        "/data/app/~~x==/com.example-y==/oat/arm64/base.odex",
        "/data/app/~~x==/com.example-y==/oat/arm64/base.vdex",
        "/data/app/~~x==/com.example-y==/base.apk",
        "/system/framework/arm64/boot-framework.oat",
        "/system/framework/framework.jar",
        "/memfd:jit-cache (deleted)",
        "/memfd:jit-zygote-cache (deleted)",
        "[anon:dalvik-jit-code-cache]",
    ],
)
def test_code_from_art_files_is_java(mapped_file):
    assert is_java(mapped_file)


@pytest.mark.parametrize(
    "mapped_file",
    [
        "/apex/com.android.art/lib64/libart.so",
        "/system/lib64/libc.so",
        "/data/app/~~x==/com.example-y==/lib/arm64/libmoq.so",
        "[kernel.kallsyms]",
        "[vdso]",
        "",
        None,
    ],
)
def test_native_code_is_not_java(mapped_file):
    assert not is_java(mapped_file)


# --- Against the fixture -----------------------------------------------------------

# Frame ids in callstacks-a, read with the pinned trace processor (58.2). The app's code
# ran from the install's base.vdex (interpreted) and from the JIT cache.
MAPPED = 53  # gf1.z, base.vdex
MERGED = 261  # p.b: R8 merged two classes' lambdas into one method
UNMINIFIED = 255  # d6.dispatchDraw: an override keeps its name, its class does not
FRAMEWORK = 242  # android.view.Choreographer.doFrame, boot-framework.oat
NATIVE = 551  # __epoll_pwait, libc.so
ART_RUNTIME = 308  # ExecuteNterpImpl, libart.so: ART's interpreter, native code
ART_STUB = 25  # art_jni_trampoline, boot-core-libart.oat


@pytest.fixture(scope="module")
def fixture_mapping(callstacks_a) -> Mapping:
    return Mapping.read(callstacks_a[1])


@pytest.fixture
def run(callstacks_a, fixture_mapping, trace_processor):
    """symbolize on the fixture as the `current` trace, with its mapping or none."""
    trace, _ = callstacks_a

    def call(frame: int, *, mapping: Mapping | None = fixture_mapping) -> dict:
        context = TraceContext(
            traces={"current": trace},
            mappings={} if mapping is None else {"current": mapping},
            binary=trace_processor,
        )
        return SYMBOLIZE.call(context, {"frame": frame, "which": "current"})

    return call


def test_the_fixture_has_obfuscated_java_frames_from_the_app(
    callstacks_a, trace_processor
):
    # The premise: callstack sampling on ART gave the app's own Java frames, by their
    # R8 names, and nothing in the trace deobfuscated them already.
    result = query_trace(
        "SELECT count(*), sum(f.deobfuscated_name IS NOT NULL) "
        "FROM stack_profile_frame AS f "
        "JOIN stack_profile_mapping AS m ON m.id = f.mapping "
        "WHERE m.name GLOB '*/com.superplayer.demo-*/base.vdex'",
        callstacks_a[0],
        binary=trace_processor,
    )
    [[app_frames, deobfuscated]] = result["rows"]
    assert app_frames >= 50
    assert deobfuscated == 0


def test_a_java_frame_resolves_to_its_source_class_and_method(run, trace_processor):
    result = run(MAPPED)
    assert result["kind"] == "java"
    assert result["name"] == "gf1.z"
    assert result["symbol"] == {
        "candidates": [
            {
                "class": "androidx.media3.exoplayer.video.MediaCodecVideoRenderer",
                "method": "render",
                "signature": "void render(long,long)",
            }
        ],
        "deobfuscated": True,
        "source": "mapping",
    }


def test_sql_used_re_reads_the_frame(run, callstacks_a, trace_processor):
    result = run(MAPPED)
    rerun = query_trace(result["sql_used"], callstacks_a[0], binary=trace_processor)
    assert rerun["row_count"] == 1
    assert rerun["rows"][0][:2] == [MAPPED, "gf1.z"]


def test_without_a_mapping_the_obfuscated_name_comes_back_flagged(run):
    # The control: no mapping, so no source name, and the result says so rather than
    # passing `gf1` off as a class the repo has.
    symbol = run(MAPPED, mapping=None)["symbol"]
    assert symbol == {
        "candidates": [{"class": "gf1", "method": "z", "signature": None}],
        "deobfuscated": False,
        "source": "no_mapping",
    }


def test_a_frame_the_mapping_lacks_comes_back_unchanged_and_flagged(run):
    # Framework code is not in the app's mapping: its name is already the source's.
    symbol = run(FRAMEWORK)["symbol"]
    assert symbol == {
        "candidates": [
            {
                "class": "android.view.Choreographer",
                "method": "doFrame",
                "signature": None,
            }
        ],
        "deobfuscated": False,
        "source": "not_in_mapping",
    }


def test_a_merged_method_lists_every_candidate(run):
    symbol = run(MERGED)["symbol"]
    assert symbol["source"] == "mapping"
    assert [(c["class"], c["method"]) for c in symbol["candidates"]] == [
        (
            "com.superplayer.preload.PreloadCoordinator$attachment$1",
            "onEngineAssembled$lambda$0",
        ),
        ("kotlin.collections.AbstractCollection$$ExternalSyntheticLambda0", "invoke"),
    ]


def test_a_method_the_mapping_does_not_list_keeps_its_name(run):
    # A mapping naming the class but not the method: the class is read back, the
    # method, which R8 did not rename, is left as it is.
    mapping = Mapping.parse("androidx.compose.ui.platform.AndroidComposeView -> d6:\n")
    symbol = run(UNMINIFIED, mapping=mapping)["symbol"]
    assert symbol["source"] == "class_only"
    assert symbol["deobfuscated"] is True
    assert symbol["candidates"] == [
        {
            "class": "androidx.compose.ui.platform.AndroidComposeView",
            "method": "dispatchDraw",
            "signature": None,
        }
    ]


@pytest.mark.parametrize("frame", [NATIVE, ART_RUNTIME])
def test_a_native_frame_has_a_null_symbol(run, frame):
    result = run(frame)
    assert result["kind"] == "native"
    assert result["symbol"] is None
    assert result["mapped_file"].endswith(".so")


def test_an_art_stub_in_a_java_file_has_a_null_symbol(run):
    result = run(ART_STUB)
    assert (result["kind"], result["name"], result["symbol"]) == (
        "art_stub",
        "art_jni_trampoline",
        None,
    )


def test_each_side_uses_only_its_own_mapping(
    callstacks_a, fixture_mapping, trace_processor
):
    # A mapping is one build's names; the other side's build named things differently.
    trace, _ = callstacks_a
    context = TraceContext(
        traces={"baseline": trace, "current": trace},
        mappings={"baseline": fixture_mapping},
        binary=trace_processor,
    )
    assert symbolize(context, MAPPED, "baseline")["symbol"]["source"] == "mapping"
    assert symbolize(context, MAPPED, "current")["symbol"]["source"] == "no_mapping"


def test_an_id_the_trace_lacks_is_refused(run):
    with pytest.raises(ToolInputError, match="not a stack_profile_frame id"):
        run(100_000)
