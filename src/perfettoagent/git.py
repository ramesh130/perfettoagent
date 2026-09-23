"""Read-only access to the target app's repo, through `git` subprocess calls only.

CLAUDE.md and docs/tech-stack.md allow `log`, `diff`, `blame`, `grep`, `cat-file` and
`merge-base`, and nothing that writes. Every call here is one of those. Every call also
carries:

- `--no-optional-locks`, so even a read never refreshes the index as a side effect;
- `--literal-pathspecs`, so a path is a path: `:(glob)`, `:!x` and other pathspec
  magic in text the model wrote are not interpreted;
- `--end-of-options` before revisions and `--` before paths, so no text the model wrote
  can be read as an option (`--output=/tmp/x` is a path after `--`, not a flag).

Revisions the model supplies must look like a sha before they reach git at all, and
they are resolved through `cat-file --batch-check` on stdin, which never parses options.

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

# A commit named by the model: hex only, so it can never be an option or a ref name.
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


class GitError(RuntimeError):
    """git could not answer: not a repo, a bad revision, or a failed command."""


def run_git(repo: Path, args: list[str], *, stdin: str | None = None) -> str:
    """Runs `git <args>` read-only in `repo` and returns stdout; raises GitError."""
    result = _run(repo, args, stdin)
    if result.returncode != 0:
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


def is_ancestor(repo: Path, commit: str, of: str) -> bool:
    """True if `commit` is `of` or an ancestor of it. Both must be full shas."""
    result = _run(repo, ["merge-base", "--is-ancestor", "--end-of-options", commit, of])
    # ref: https://git-scm.com/docs/git-merge-base#_discussion (exit 0 yes, 1 no)
    if result.returncode in (0, 1):
        return result.returncode == 0
    raise GitError(f"git merge-base failed: {result.stderr.strip()}")


def parents(repo: Path, commit: str) -> list[str]:
    """The parents of `commit` (a full sha), first parent first, from its raw object.

    ref: https://git-scm.com/book/en/v2/Git-Internals-Git-Objects#_git_commit_objects
    """
    raw = run_git(repo, ["cat-file", "commit", commit])
    header = raw.split("\n\n", 1)[0]
    return [
        line[len("parent ") :]
        for line in header.splitlines()
        if line.startswith("parent ")
    ]


def changed_paths(repo: Path, commit: str, path: str) -> list[str]:
    """The files at or under `path` that `commit` (a full sha) changed.

    What a commit changed is its diff against its first parent. For a root commit that
    is its whole tree, diffed against the empty tree. For a merge it is what the merge
    brought into the line it was merged into (`--first-parent`'s view): a file that
    changed on the merged branch counts, which matches the merge being the commit that
    landed it. The side branch's own commits are in the range too, and can be cited.
    """
    before = next(iter(parents(repo, commit)), None) or _empty_tree(commit)
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


def _empty_tree(commit: str) -> str:
    """The empty tree's name in this repo's hash: sha1 or sha256, by the sha's length.
    git knows it without its being stored. ref: https://git-scm.com/docs/git-hash-object
    """
    algorithm = "sha1" if len(commit) == 40 else "sha256"
    return hashlib.new(algorithm, b"tree 0\0").hexdigest()


def _run(
    repo: Path, args: list[str], stdin: str | None = None
) -> subprocess.CompletedProcess:
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
        raise GitError(f"could not run git {args[0]}: {e}") from e
