"""R8's `mapping.txt`: the obfuscated names of a minified build, read back to the source
names the target repo can be grepped for (`symbolize`, issue #25, ADR-0019).

The file is text, one class per unindented line and its members indented under it:

    com.example.Player -> a.b:
        int state -> a
        1:4:void start(int):20:23 -> c
        5:5:void com.example.Clock.tick():40:40 -> c

Only classes and methods are read; fields never appear in a stack frame. A method line's
leading `a:b:` is the range of obfuscated line numbers it covers, and a trailing `:x:y`
the original lines. Lines sharing one range are one inline stack, innermost first: in
the example, `tick` was inlined into `start`, whose own body is at `c`'s lines 1 to 4.

A frame read from a trace has neither a line number nor a signature. So for an
obfuscated method, only the outermost method of each range stands for the frame: the
source method R8 compiled into it, with whatever it inlined. Inlined callees are left
out, since without a line nothing says the frame was in one. Overloads R8 gave the same
short name remain, and every one is kept, in file order; nothing picks one, because a
guess would send the model to grep for the wrong method.

A method R8 synthesized (`com.android.tools.r8.synthesized`: a bridge, a lambda's
constructor) has no source to grep, and retrace hides it too. So it is a candidate
only when no source method is: in a lambda class, say, whose own name still leads to
its file. R8 writes such a method's owner without its package; it is the package of
the class it is listed under.

Other lines starting with `#` are comments, or R8 metadata nothing here needs.
ref: https://r8.googlesource.com/r8/+/refs/heads/main/doc/retrace.md
"""

import gzip
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

# `original -> obfuscated:` at column 0.
_CLASS = re.compile(r"(?P<original>\S+) -> (?P<obfuscated>\S+):$")

# An indented method: optional `a:b:` obfuscated lines, the return type, the original
# name (qualified if inlined from another class), its arguments, optional `:x[:y]`
# original lines, then ` -> ` and the obfuscated name. A field has no `(`.
_METHOD = re.compile(
    r"\s+(?P<range>\d+:\d+:)?(?P<returns>\S+) (?P<name>[^\s(]+)\((?P<args>[^)]*)\)"
    r"(?::\d+(?::\d+)?)? -> (?P<obfuscated>\S+)$"
)

# The metadata R8 writes under a member it made up (a lambda's bridge, an outline).
_SYNTHESIZED = '{"id":"com.android.tools.r8.synthesized"}'


@dataclass(frozen=True)
class Method:
    """One original method an obfuscated name can stand for. `signature` is None when
    the name came from a trace, which gives none; `synthesized` when R8 made it up."""

    class_name: str
    method: str
    signature: str | None
    synthesized: bool = False

    def as_dict(self) -> dict:
        return {
            "class": self.class_name,
            "method": self.method,
            "signature": self.signature,
        }


@dataclass
class _Class:
    original: str
    # Per obfuscated method name: every candidate, in file order.
    methods: dict[str, list[Method]] = field(default_factory=dict)


class Mapping:
    """A parsed mapping file: obfuscated class and method names to original ones."""

    def __init__(self, classes: dict[str, _Class]):
        self._classes = classes

    @classmethod
    def read(cls, path: str | Path) -> "Mapping":
        """Reads `mapping.txt`, or a gzipped copy (`.gz`), as fixtures are stored."""
        path = Path(path)
        opener = gzip.open if path.suffix == ".gz" else open
        with opener(path, "rt", encoding="utf-8") as f:
            return cls.parse(f.read())

    @classmethod
    def parse(cls, text: str) -> "Mapping":
        classes: dict[str, _Class] = {}
        current: _Class | None = None
        # The inline stack being read: its (range, obfuscated name), and its methods,
        # innermost first.
        stack_key: tuple[str, str] | None = None
        stack: list[Method] = []

        def close_stack() -> None:
            nonlocal stack_key
            if current is not None and stack:
                sources = [m for m in stack if not m.synthesized]
                outermost = (sources or stack)[-1]
                candidates = current.methods.setdefault(stack_key[1], [])
                if outermost not in candidates:
                    candidates.append(outermost)
            stack.clear()
            stack_key = None

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                # Metadata under a member follows it, indented.
                if stack and line[0].isspace() and stripped.endswith(_SYNTHESIZED):
                    stack[-1] = replace(stack[-1], synthesized=True)
                continue
            m = None if not line[0].isspace() else _METHOD.match(line)
            key = (m["range"], m["obfuscated"]) if m else None
            # A line without a range is a whole method on its own.
            if m is None or key != stack_key or not m["range"]:
                close_stack()
            if not line[0].isspace():
                c = _CLASS.match(line)
                current = _Class(c["original"]) if c else None
                if c:
                    classes[c["obfuscated"]] = current
                continue
            if current is None or m is None:
                continue  # a field, or a member of a class line we could not read
            owner, _, name = m["name"].rpartition(".")
            if owner and "." not in owner:
                package = current.original.rpartition(".")[0]
                owner = f"{package}.{owner}" if package else owner
            method = Method(
                class_name=owner or current.original,
                method=name,
                signature=f"{m['returns']} {name}({m['args']})",
            )
            stack_key = key
            stack.append(method)
        close_stack()
        return cls(classes)

    def original_class(self, obfuscated: str) -> str | None:
        """The source name of an obfuscated class, or None if the mapping has none."""
        known = self._classes.get(obfuscated)
        return known.original if known else None

    def methods(self, obfuscated_class: str, obfuscated_method: str) -> list[Method]:
        """Every original method `obfuscated_class.obfuscated_method` can stand for,
        in file order; empty if the mapping names neither."""
        known = self._classes.get(obfuscated_class)
        candidates = known.methods.get(obfuscated_method, []) if known else []
        sources = [m for m in candidates if not m.synthesized]
        return sources or list(candidates)
