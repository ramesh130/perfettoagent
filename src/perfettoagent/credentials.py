"""API keys, from the environment or a git-ignored `.env` (ADR-0020 "Credentials").

A variable already set in the environment wins over `.env`. Only the names in KEYS are
read from the file; every other line is ignored. A key is returned to the caller that
builds the SDK client and goes nowhere else: never printed, logged, put in an error
message or written to a result.
"""

import os
import re
from pathlib import Path

KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY")

# ADR-0020: the `.env` in the working directory, the one `.gitignore` excludes.
DOTENV = Path(".env")

# Both providers' keys start `sk-` (OpenAI `sk-proj-…`, Anthropic `sk-ant-…`), and an
# API error can quote a masked piece of the key it was sent (OpenAI's 401 says
# "Incorrect API key provided: sk-proj-…abcd"). Any such run of characters is removed.
_KEY_LIKE = re.compile(r"sk-[A-Za-z0-9_\-.*…]*")


def api_key(name: str, *, environ=None, dotenv: Path = DOTENV) -> str | None:
    """The key `name` (one of KEYS), or None when neither place has it."""
    if name not in KEYS:
        raise ValueError(f"not a key this reads: {name!r}")
    environ = os.environ if environ is None else environ
    if environ.get(name):
        return environ[name]
    return _read_dotenv(dotenv).get(name)


def _read_dotenv(path: Path) -> dict[str, str]:
    """KEYS's entries in a `.env` file: `NAME=value` lines, optionally after `export`,
    with the value optionally in single or double quotes. `#` starts a comment line."""
    try:
        lines = path.read_text().splitlines()
    except (FileNotFoundError, IsADirectoryError):
        return {}
    found = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        line = line.removeprefix("export ").lstrip()
        name, sep, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if not sep or name not in KEYS:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        if value:
            found[name] = value
    return found


def redact(message: str, *, environ=None, dotenv: Path = DOTENV) -> str:
    """`message` with every key this reads, and anything shaped like a key or a
    masked piece of one, replaced: for text about to be printed or logged."""
    for name in KEYS:
        key = api_key(name, environ=environ, dotenv=dotenv)
        if key:
            message = message.replace(key, "[redacted]")
    return _KEY_LIKE.sub("[redacted]", message)
