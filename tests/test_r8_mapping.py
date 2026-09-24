"""R8's mapping.txt, read back (issue #25, ADR-0019). The lines below are the shapes R8
9.4 writes, copied from the demo build the symbolize fixture comes from, and renamed."""

import gzip

import pytest

from perfettoagent.r8_mapping import Mapping

MAPPING = """\
# compiler: R8
# {"id":"com.android.tools.r8.mapping","version":"2.2"}
com.example.Feed -> aj0:
# {"id":"sourceFile","fileName":"Feed.kt"}
    android.os.Handler mainThread -> a
    com.example.Pool pool -> d
      # {"id":"com.android.tools.r8.residualsignature","signature":"Lg42;"}
    1:3:void <init>(android.content.Context,java.util.List):239:239 -> <init>
    1:3:void Feed.<init>(android.content.Context,java.util.ArrayList):0 -> <init>
      # {"id":"com.android.tools.r8.synthesized"}
    4:5:com.example.Pool com.example.Pool$Builder.build():451:451 -> <init>
    4:5:void <init>(android.content.Context,java.util.List):271 -> <init>
    4:5:void Feed.<init>(android.content.Context,java.util.ArrayList):0 -> <init>
      # {"id":"com.android.tools.r8.synthesized"}
    6:6:void Feed.<init>(byte):0:0 -> <init>
      # {"id":"com.android.tools.r8.synthesized"}
    1:9:void bind(int):30:38 -> a
    10:12:void com.example.Clock.tick():40:42 -> a
    10:12:void unbind(java.lang.String):50 -> a
    void release() -> b
com.example.Feed$Lambda -> bj0:
# {"id":"com.android.tools.r8.synthesized"}
    1:2:void Feed$Lambda.invoke():0:0 -> invoke
      # {"id":"com.android.tools.r8.synthesized"}
"""


def test_a_class_maps_back_to_its_source_name():
    mapping = Mapping.parse(MAPPING)
    assert mapping.original_class("aj0") == "com.example.Feed"
    assert mapping.original_class("bj0") == "com.example.Feed$Lambda"


def test_a_method_is_the_outermost_of_its_inline_stack():
    # Range 4:5 inlines Pool$Builder.build into <init>; the frame is <init>'s. Range 6
    # is a constructor R8 made up, with no source: not a candidate beside a real one.
    methods = Mapping.parse(MAPPING).methods("aj0", "<init>")
    assert [m.as_dict() for m in methods] == [
        {
            "class": "com.example.Feed",
            "method": "<init>",
            "signature": "void <init>(android.content.Context,java.util.List)",
        }
    ]


def test_overloads_sharing_a_short_name_are_all_kept():
    # `a` is bind(int) at lines 1-9 and unbind(String) at 10-12; with no line number
    # neither can be picked. Clock.tick, inlined into unbind, is not a candidate.
    methods = Mapping.parse(MAPPING).methods("aj0", "a")
    assert [(m.class_name, m.method) for m in methods] == [
        ("com.example.Feed", "bind"),
        ("com.example.Feed", "unbind"),
    ]


def test_a_method_line_without_a_range_is_read():
    [release] = Mapping.parse(MAPPING).methods("aj0", "b")
    assert release.signature == "void release()"


def test_a_synthesized_method_stands_when_nothing_else_does():
    # A lambda class's own bridge has no source method behind it, but its class does.
    # R8 writes the owner without its package; it is the listing class's.
    [invoke] = Mapping.parse(MAPPING).methods("bj0", "invoke")
    assert (invoke.class_name, invoke.method) == ("com.example.Feed$Lambda", "invoke")


def test_names_the_mapping_lacks_come_back_empty():
    # The control: nothing is invented for a class or method the file never names.
    mapping = Mapping.parse(MAPPING)
    assert mapping.original_class("zz9") is None
    assert mapping.methods("zz9", "a") == []
    assert mapping.methods("aj0", "zz") == []


def test_fields_are_not_methods():
    assert Mapping.parse(MAPPING).methods("aj0", "d") == []


@pytest.mark.parametrize("name", ["mapping.txt", "mapping.txt.gz"])
def test_a_file_is_read_plain_or_gzipped(tmp_path, name):
    path = tmp_path / name
    data = MAPPING.encode()
    path.write_bytes(gzip.compress(data) if name.endswith(".gz") else data)
    assert Mapping.read(path).original_class("aj0") == "com.example.Feed"
