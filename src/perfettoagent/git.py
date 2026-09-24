"""Read-only access to the target app's repo, through `git` subprocess calls only.

CLAUDE.md and docs/tech-stack.md allow `log`, `diff`, `blame`, `grep`, `cat-file` and
`merge-base`, and nothing that writes. Every call here is one of those. Every call also
carries:

- `--no-optional-locks`, so even a read never refreshes the index as a side effect;
- `--literal-pathspecs`, so a path is a path: `:(glob)`, `:!x` and other pathspec
  magic in text the model wrote are not interpreted;
- `--end-of-options` before revisions and `--` before paths, so no text the model wrote
  can be read as an option (`--output=/tmp/x` is a path after `--`, not a flag).
  `git blame` is the exception: given `--end-of-options`, it stops honouring `--`
  (ADR-0018), so its caller passes a resolved sha without it.

Revisions the model supplies are resolved through `cat-file --batch-check` on stdin,
which never parses options, and only the full sha it answers reaches argv. A citation's
revision must also look like a sha before it reaches git at all (`resolve_sha`); the
agent's git tools also take a branch or a tag (`resolve_commit`, ADR-0018).

ref: https://git-scm.com/docs/git#Documentation/git.txt---literal-pathspecs
ref: https://git-scm.com/docs/gitcli (--end-of-options)
"""

import hashlib
import os
import re
import subprocess
from pathlib import Path

# A local repo answers these in milliseconds; a minute means something is wrong (a
# network filesystem, a lock), and the verifier should fail rather than hang.
GIT_TIMEOUT_S = 60

# A commit named by the model: hex only, so it can never be an option. (It can still
# be a ref's name; `resolve_sha` refuses a ref that shadows the prefix.)
# 7 is git's default abbreviation; 64 is a full sha256 object name.
# ref: https://git-scm.com/docs/hash-function-transition
SHA = re.compile(r"[0-9a-f]{7,64}")

# Environment variables that point git at a repository other than `repo`. Cleared, so
# running inside a git hook (which sets GIT_DIR) cannot redirect the verifier.
# ref: https://git-scm.com/docs/git#_the_git_repository
_REDIRECTING_ENV = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
)


# The subcommands docs/tech-stack.md allows on the target repo, all read-only. Any
# other is refused before it runs, so a later caller cannot slip in a write.
ALLOWED_SUBCOMMANDS = frozenset(
    {"log", "diff", "blame", "grep", "cat-file", "merge-base"}
)


class GitError(RuntimeError):
    """git answered with an error: not a repo, a bad path, a failed command."""


class GitUnavailable(RuntimeError):
    """git could not be run at all, or timed out. Not a GitError on purpose: a caller
    that turns a GitError into a verdict on its input must let this one through."""


def run_git(
    repo: Path,
    args: list[str],
    *,
    stdin: str | None = None,
    ok_returncodes: tuple[int, ...] = (0,),
) -> str:
    """Runs `git <args>` read-only in `repo` and returns stdout; raises GitError.

    `ok_returncodes` names the exit codes that are answers, not failures: `git grep`
    exits 1 when nothing matched.

    ref: https://git-scm.com/docs/git-grep
    """
    result = _run(repo, args, stdin)
    if result.returncode not in ok_returncodes:
        raise GitError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def resolve_commit(repo: Path, rev: str) -> str | None:
    """The full sha of the commit `rev` names, or None if it names no commit.

    `rev` is anything git accepts (a sha prefix, a branch, a tag); an ambiguous prefix
    names no commit. It goes in on stdin, one line, so it is never an option.
    """
    if not rev or any(c.isspace() for c in rev):
        return None
    out = run_git(
        repo,
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        stdin=f"{rev}^{{commit}}\n",
    )
    fields = out.split()
    # "<sha> commit" on success; "<rev> missing" or "<rev> ambiguous" otherwise.
    if len(fields) == 2 and fields[1] == "commit":
        return fields[0]
    return None


def resolve_sha(repo: Path, sha: str) -> str | None:
    """The full sha of the commit that `sha`, a hex prefix, names; None if none does.

    git resolves a ref before an object prefix, so a tag or branch named `abcdef1`
    would answer for the prefix `abcdef1`. Such an answer is refused: the commit found
    must start with the digits given.
    ref: https://git-scm.com/docs/gitrevisions#_specifying_revisions
    """
    if not SHA.fullmatch(sha):
        return None
    full = resolve_commit(repo, sha)
    return full if full is not None and full.startswith(sha) else None


def is_ancestor(repo: Path, commit: str, of: str) -> bool:
    """True if `commit` is `of` or an ancestor of it. Both must be full shas."""
    result = _run(repo, ["merge-base", "--is-ancestor", "--end-of-options", commit, of])
    # ref: https://git-scm.com/docs/git-merge-base#_discussion (exit 0 yes, 1 no)
    if result.returncode in (0, 1):
        return result.returncode == 0
    raise GitError(f"git merge-base failed: {result.stderr.strip()}")


def parents(repo: Path, commit: str) -> list[str]:
    """The parents of `commit` (a full sha), first parent first, from its raw object."""
    header, _ = _commit_object(repo, commit)
    return [
        line[len("parent ") :]
        for line in header.splitlines()
        if line.startswith("parent ")
    ]


def commit_message(repo: Path, commit: str) -> str:
    """The full message of `commit` (a full sha), from its raw object."""
    return _commit_object(repo, commit)[1].strip()


def _commit_object(repo: Path, commit: str) -> tuple[str, str]:
    """A commit's raw object, split into its headers and its message, which a blank
    line separates.

    ref: https://git-scm.com/book/en/v2/Git-Internals-Git-Objects#_git_commit_objects
    """
    header, _, message = run_git(repo, ["cat-file", "commit", commit]).partition("\n\n")
    return header, message


def changed_paths(repo: Path, commit: str, path: str) -> list[str]:
    """The files at or under `path` that `commit` (a full sha) changed.

    What a commit changed is its diff against its first parent. For a root commit that
    is its whole tree, diffed against the empty tree. For a merge it is what the merge
    brought into the line it was merged into (`--first-parent`'s view): a file that
    changed on the merged branch counts, which matches the merge being the commit that
    landed it. The side branch's own commits are in the range too, and can be cited.
    """
    before = diff_base(repo, commit)
    out = run_git(
        repo,
        [
            "diff",
            "--name-only",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
            "--end-of-options",
            before,
            commit,
            "--",
            path,
        ],
    )
    return out.splitlines()


def diff_base(repo: Path, commit: str) -> str:
    """What `commit` (a full sha) is diffed against to say what it changed: its first
    parent, or the empty tree for a root commit (see `changed_paths`)."""
    return next(iter(parents(repo, commit)), None) or _empty_tree(commit)


def _empty_tree(commit: str) -> str:
    """The empty tree's name in this repo's hash: sha1 or sha256, by the sha's length.
    git knows it without its being stored. ref: https://git-scm.com/docs/git-hash-object
    """
    algorithm = "sha1" if len(commit) == 40 else "sha256"
    return hashlib.new(algorithm, b"tree 0\0").hexdigest()


def _run(
    repo: Path, args: list[str], stdin: str | None = None
) -> subprocess.CompletedProcess:
    if args[0] not in ALLOWED_SUBCOMMANDS:
        raise ValueError(
            f"git {args[0]} is not a read-only subcommand this repo allows"
        )
    env = {k: v for k, v in os.environ.items() if k not in _REDIRECTING_ENV}
    try:
        return subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "--no-optional-locks",
                "--literal-pathspecs",
                *args,
            ],
            input=stdin,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise GitUnavailable(f"could not run git {args[0]}: {e}") from e
