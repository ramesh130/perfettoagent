"""The agent's tools over the target repo: `get_git_log`, `get_git_diff`, `git_blame`
and `grep_repo` (roadmap item 6, docs/tech-stack.md "Agent tool surface and limits").

Every git call goes through `perfettoagent.git.run_git`, so only the read-only
subcommands it allows can run, and each carries its guards (`--no-optional-locks`,
`--literal-pathspecs`). On top of those, text the model wrote never reaches argv where
git could read it as an option:

- a revision is resolved to a full sha first (`resolve_commit`, which reads it on
  stdin), and only the sha is passed, after `--end-of-options`;
- a path is passed after `--`, where `--output=/tmp/x` is a file name;
- a grep pattern is passed as the value of `-e`, which git never reads as an option.

Every diff turns off what repo config could turn on: colour (`--no-color`), external
diff drivers and textconv filters (`--no-ext-diff`, `--no-textconv`), which would run
commands the target repo's config names.

Each result is a JSON-serialisable dict, and each cap is said twice: in the tool's
description, and in the result as `truncated` with the true total.
ref: https://git-scm.com/docs/gitcli (--end-of-options)
"""

import re
from datetime import UTC, datetime
from pathlib import Path

from perfettoagent.git import commit_message, diff_base, resolve_commit, run_git
from perfettoagent.tools import (
    INTEGER,
    STRING,
    Tool,
    ToolInputError,
    array,
    described,
    nullable,
    strict_input,
)

# docs/tech-stack.md. A range in a merge alert is 5 to 50 commits; 200 covers a
# release's worth, and past that the model should narrow by path, not page.
MAX_COMMITS = 200

# docs/tech-stack.md: `max_lines=400`. It is the default and also the ceiling: a larger
# diff costs context the model is better off spending on one file at a time.
MAX_DIFF_LINES = 400

# docs/tech-stack.md: `max_hits=100`, the default and the ceiling, for the same reason.
MAX_GREP_HITS = 100

# docs/tech-stack.md sets no cap for blame; this one keeps a single call to the size of
# a query_trace result. A function or a class body fits; a whole file may not.
MAX_BLAME_LINES = 200

# A grep hit's text is cut to this many characters: one minified or generated line can
# be megabytes, and the hit's path and line number are what the model cites.
MAX_HIT_CHARS = 300

# A backslash before a letter or digit. POSIX extended regexes define `\` only before
# a special character; `\b`, `\w` and the like are extensions that glibc's regex has and
# macOS's does not, where `\bfoo` silently matches nothing. Refused, so a pattern means
# the same on every host and a zero is never an artefact of the platform.
# ref: https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap09.html#tag_09_04_02
_CLASS_ESCAPE = re.compile(r"\\[0-9A-Za-z]")

# Separators for `git log --format`: ASCII record and unit separators, which no commit
# subject or author name contains. ref: https://git-scm.com/docs/pretty-formats
_RECORD = "\x1e"
_UNIT = "\x1f"

# The flags every diff-producing call carries (see the module docstring).
_NO_CONFIG_DIFF = ["--no-color", "--no-ext-diff", "--no-textconv"]


def get_git_log(repo: Path, range: str, paths: list[str] | None) -> dict:
    """The commits in `range` ("base..head"), newest first, at most MAX_COMMITS.
    (`range` shadows the builtin because it is the schema's name for it.)"""
    base, head = _resolve_range(repo, range)
    # `log.showSignature` in the repo's config would run its `gpg.program`.
    selection = [
        "--no-show-signature",
        "--end-of-options",
        f"{base}..{head}",
        "--",
        *_paths(paths),
    ]
    out = run_git(
        repo,
        [
            "log",
            "-z",
            "--name-only",
            # With `paths`, list each commit's every file, not only the matching ones.
            "--full-diff",
            "--no-renames",
            *_NO_CONFIG_DIFF,
            f"--max-count={MAX_COMMITS + 1}",
            f"--format={_RECORD}%H{_UNIT}%an{_UNIT}%aI{_UNIT}%s",
            *selection,
        ],
    )
    commits = [_log_record(r) for r in out.split(_RECORD)[1:]]
    truncated = len(commits) > MAX_COMMITS
    if truncated:
        # Only now is the true count worth a second pass: a sha per line, no files.
        count = run_git(repo, ["log", "--format=%H", *selection])
        commit_count = len(_lines(count))
    else:
        commit_count = len(commits)
    return {
        "range": {"base": base, "head": head},
        "commits": commits[:MAX_COMMITS],
        "commit_count": commit_count,
        "truncated": truncated,
    }


def get_git_diff(repo: Path, sha: str, path: str | None, max_lines: int | None) -> dict:
    """What commit `sha` changed (at or under `path`), cut to `max_lines` lines."""
    limit = _limit(max_lines, MAX_DIFF_LINES, "max_lines")
    commit = _resolve(repo, sha, "sha")
    before = diff_base(repo, commit)
    out = run_git(
        repo,
        [
            "diff",
            "--no-renames",
            *_NO_CONFIG_DIFF,
            "--end-of-options",
            before,
            commit,
            "--",
            *_paths(None if path is None else [path]),
        ],
    )
    lines = _lines(out)
    return {
        "sha": commit,
        "diffed_against": before,
        "message": commit_message(repo, commit),
        "path": path,
        "diff": "\n".join(lines[:limit]),
        "line_count": len(lines),
        "truncated": len(lines) > limit,
    }


def git_blame(repo: Path, path: str, line_start: int, line_end: int, at: str) -> dict:
    """The commit that last changed each line of `path` from `line_start` to `line_end`
    (1-based, inclusive) as of commit `at`, at most MAX_BLAME_LINES lines."""
    if line_start < 1 or line_end < line_start:
        raise ToolInputError(
            f"lines {line_start}..{line_end}: need 1 <= line_start <= line_end"
        )
    commit = _resolve(repo, at, "at")
    truncated = line_end - line_start + 1 > MAX_BLAME_LINES
    last = line_start + MAX_BLAME_LINES - 1 if truncated else line_end
    out = run_git(
        repo,
        [
            "blame",
            "--line-porcelain",
            "--no-textconv",
            f"-L{line_start},{last}",
            # No `--end-of-options` here, unlike every other call: blame's own
            # argument parsing then no longer sees `--` as the end of revisions, and
            # hands the path to the revision parser, where a path of
            # `--output=<file>` is an option and writes that file (git 2.50; a test
            # pins it). `commit` is a full sha from `_resolve`, hex, never an option.
            commit,
            "--",
            *_paths([path]),
        ],
    )
    return {
        "at": commit,
        "path": path,
        "lines": _blame_lines(out, line_start),
        # The span asked for; `lines` holds all of it unless `truncated`.
        "line_count": line_end - line_start + 1,
        "truncated": truncated,
    }


def grep_repo(
    repo: Path, pattern: str, paths: list[str] | None, max_hits: int | None, at: str
) -> dict:
    """The lines matching `pattern` (a POSIX extended regex) in the tree of commit
    `at`, at most `max_hits` of them."""
    if not pattern:
        raise ToolInputError("pattern: must not be empty")
    if _CLASS_ESCAPE.search(pattern):
        raise ToolInputError(
            f"pattern: {pattern!r} uses a backslash-letter escape (\\b, \\d, \\w, "
            "\\s...), which POSIX extended regexes do not define; use [[:digit:]], "
            "[[:alnum:]_], [[:space:]], or spell the boundary out"
        )
    limit = _limit(max_hits, MAX_GREP_HITS, "max_hits")
    commit = _resolve(repo, at, "at")
    out = run_git(
        repo,
        [
            "grep",
            "-z",
            "--line-number",
            "-I",
            "--no-color",
            "--no-textconv",
            "--extended-regexp",
            "-e",
            pattern,
            "--end-of-options",
            commit,
            "--",
            *_paths(paths),
        ],
        ok_returncodes=(0, 1),  # 1: nothing matched
    )
    hits = [_grep_hit(line, commit) for line in _lines(out)]
    return {
        "at": commit,
        "hits": hits[:limit],
        "hit_count": len(hits),
        "truncated": len(hits) > limit,
    }


def _resolve(repo: Path, rev: str, what: str) -> str:
    full = resolve_commit(repo, rev)
    if full is None:
        raise ToolInputError(f"{what}: {rev!r} names no commit in the target repo")
    return full


def _resolve_range(repo: Path, spec: str) -> tuple[str, str]:
    base, sep, head = spec.partition("..")
    if not sep or not base or not head or head.startswith("."):
        raise ToolInputError(f"range: {spec!r} is not of the form base..head")
    return _resolve(repo, base, "range base"), _resolve(repo, head, "range head")


def _paths(paths: list[str] | None) -> list[str]:
    """Paths for after `--`. git refuses an empty pathspec with an unhelpful message."""
    for p in paths or ():
        if not p:
            raise ToolInputError("paths: an empty string is not a path")
    return list(paths or ())


def _limit(value: int | None, ceiling: int, what: str) -> int:
    if value is None:
        return ceiling
    if value < 1:
        raise ToolInputError(f"{what}: must be at least 1, or null for {ceiling}")
    return min(value, ceiling)


def _lines(out: str) -> list[str]:
    """git's output split at newlines only. `str.splitlines` also splits at form
    feeds and other separators a source line can hold, which would miscount a diff."""
    return out.removesuffix("\n").split("\n") if out else []


def _log_record(record: str) -> dict:
    """One commit of `git log -z --name-only`: the format line, then its files as
    NUL-separated names. Under `-z` git ends the format line with NUL, and may put a
    newline before the first file; a subject holds neither, so the header ends at the
    first of the two."""
    end = min(i for i in (record.find("\0"), record.find("\n"), len(record)) if i >= 0)
    header, files = record[:end], record[end + 1 :]
    sha, author, date, subject = header.split(_UNIT)
    return {
        "sha": sha,
        "author": author,
        "date": date,
        "subject": subject,
        "files": [f for f in files.strip("\n").split("\0") if f],
    }


def _blame_lines(porcelain: str, line_start: int) -> list[dict]:
    """`git blame --line-porcelain`: per line, a `<sha> <orig> <final>` header, then
    `key value` lines, then the line's text after a TAB.
    ref: https://git-scm.com/docs/git-blame#_the_porcelain_format
    """
    lines: list[dict] = []
    fields: dict[str, str] = {}
    for row in _lines(porcelain):
        if row.startswith("\t"):
            lines.append(
                {
                    "line": line_start + len(lines),
                    "sha": fields["sha"],
                    "author": fields.get("author", ""),
                    "date": datetime.fromtimestamp(
                        int(fields["author-time"]), UTC
                    ).isoformat(),
                    "summary": fields.get("summary", ""),
                    "text": row[1:],
                }
            )
            fields = {}
        elif not fields:
            fields["sha"] = row.split(" ", 1)[0]
        else:
            key, _, value = row.partition(" ")
            fields[key] = value
    return lines


def _grep_hit(line: str, commit: str) -> dict:
    """One line of `git grep -z -n <commit>`: `<commit>:<path>`, the line number and
    the text, NUL-separated, so a path may hold any character but NUL."""
    name, number, text = line.split("\0", 2)
    return {
        "path": name.removeprefix(f"{commit}:"),
        "line": int(number),
        "text": text[:MAX_HIT_CHARS],
    }


_REV = "A commit: a sha or a unique sha prefix, a branch or a tag."

GET_GIT_LOG = Tool(
    name="get_git_log",
    description=(
        "List the commits in a range of the target repo, newest first: each commit's "
        "sha, author, author date, subject line and the files it changed. `range` is "
        "`base..head`: the commits reachable from head and not from base. `paths` "
        "keeps only commits that changed a file at or under one of these paths "
        "(literal paths from the repo root, not globs); each kept commit still lists "
        "all its files. At most "
        f"{MAX_COMMITS} commits come back; `commit_count` is always the true total and "
        "`truncated` says when the list stopped short, in which case narrow by path. "
        "It cannot tell you what a commit changed inside a file (use get_git_diff), "
        "nor anything about the running app: whether a commit affected performance is "
        "for the traces to show. A merge commit lists no files."
    ),
    input_schema=strict_input(
        range=described(STRING, "`base..head`, two commits."),
        paths=described(
            nullable(array(STRING)),
            "Repo-relative paths to filter by, or null for every commit.",
        ),
    ),
    function=get_git_log,
)

GET_GIT_DIFF = Tool(
    name="get_git_diff",
    description=(
        "Show what one commit changed, as a unified diff against its first parent (a "
        "root commit against the empty tree), with the commit's full message. `path` "
        "limits the diff to a file or directory. The diff is cut to `max_lines` lines "
        f"(null or anything above {MAX_DIFF_LINES} means {MAX_DIFF_LINES}); "
        "`line_count` is the full length and `truncated` says when it was cut, in "
        "which case ask again for one path. Binary files show as one line. It cannot "
        "tell you why a change was made beyond its message, nor how the changed code "
        "behaves at runtime, and it shows no rename as a rename."
    ),
    input_schema=strict_input(
        sha=described(STRING, _REV),
        path=described(
            nullable(STRING), "A repo-relative path, or null for the whole commit."
        ),
        max_lines=described(
            nullable(INTEGER), f"At most {MAX_DIFF_LINES}; null for {MAX_DIFF_LINES}."
        ),
    ),
    function=get_git_diff,
)

GIT_BLAME = Tool(
    name="git_blame",
    description=(
        "For each line of a file from `line_start` to `line_end` (1-based, inclusive) "
        "as it was at commit `at`, the commit that last changed it: sha, author, "
        f"author date (UTC), subject and the line's text. At most {MAX_BLAME_LINES} "
        "lines per call; `line_count` is the span asked for and `truncated` says when "
        "it was cut. It cannot see "
        "lines that were deleted, it does not follow code moved from another file, "
        "and a line can name a commit outside the range under study: check with "
        "get_git_log."
    ),
    input_schema=strict_input(
        path=described(STRING, "A repo-relative file path."),
        line_start=described(INTEGER, "First line, from 1."),
        line_end=described(INTEGER, "Last line, at least line_start."),
        at=described(STRING, _REV),
    ),
    function=git_blame,
)

GREP_REPO = Tool(
    name="grep_repo",
    description=(
        "Search the files of the target repo as they were at commit `at` (not any "
        "working tree) for lines matching `pattern`, a case-sensitive POSIX extended "
        "regular expression: no `\\b`, `\\d`, `\\w` or `\\s` (use [[:digit:]], "
        "[[:alnum:]_], [[:space:]]). `paths` limits the search to files at or under "
        "these repo-relative paths. Each hit gives its path, line number and text "
        f"(cut to {MAX_HIT_CHARS} characters). At most `max_hits` hits come back "
        f"(null or anything above {MAX_GREP_HITS} means {MAX_GREP_HITS}); "
        "`hit_count` is the true total and `truncated` says when the list was cut. "
        "Binary files are skipped. It cannot tell you which of the matches run, nor "
        "when a line was added (use git_blame)."
    ),
    input_schema=strict_input(
        pattern=described(STRING, "A POSIX extended regular expression."),
        paths=described(
            nullable(array(STRING)),
            "Repo-relative paths to search under, or null for the whole tree.",
        ),
        max_hits=described(
            nullable(INTEGER), f"At most {MAX_GREP_HITS}; null for {MAX_GREP_HITS}."
        ),
        at=described(STRING, _REV),
    ),
    function=grep_repo,
)

# In the order the agent is expected to reach for them.
REPO_TOOLS = (GET_GIT_LOG, GET_GIT_DIFF, GIT_BLAME, GREP_REPO)
