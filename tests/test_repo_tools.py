"""The git tools (roadmap item 6, issue #24): their schemas, their caps, and that no
text the model writes can make them do anything but read.

Two repos. A staged eval case (ADR-0015) is the realistic one: a real app's history,
where every result is checked against git's own answer. A synthetic repo, written in
one `git fast-import`, is big enough to hit each cap, which a case's range is not. Each
cap is tested both ways: past it, and a control under it.
"""

import hashlib
import subprocess
from pathlib import Path

import pytest
from test_eval_cases import HINT_WORDS

from perfettoagent import git as git_module
from perfettoagent import repo_tools
from perfettoagent.evalcases import list_cases, load_inputs
from perfettoagent.git import ALLOWED_SUBCOMMANDS, GitError
from perfettoagent.repo_tools import (
    MAX_BLAME_LINES,
    MAX_COMMITS,
    MAX_DIFF_LINES,
    MAX_GREP_HITS,
    REPO_TOOLS,
    get_git_diff,
    get_git_log,
    git_blame,
    grep_repo,
)
from perfettoagent.tools import ToolInputError

# The synthetic repo: past each cap by a margin, so an off-by-one shows.
SYNTH_COMMITS = MAX_COMMITS + 5
SYNTH_DIFF_LINES = MAX_DIFF_LINES + 100
SYNTH_HITS = MAX_GREP_HITS + 50

# Text the model could write that git would read as an option, were it one: each
# writes a file or runs a command.
# ref: https://git-scm.com/docs/git-grep (-O, --open-files-in-pager)
# ref: https://git-scm.com/docs/git-diff (--output)
INJECTIONS = (
    "--output={out}",
    "-O",
    "--open-files-in-pager=touch {out}",
    "-Otouch {out}",
    "--exec=touch {out}",
)


def git(repo: Path, *args: str, stdin: str | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        input=stdin,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


@pytest.fixture(scope="module")
def case_repo(tmp_path_factory) -> tuple[Path, str, str]:
    """The first case's repo, staged as the model gets it, and its range."""
    cases = list_cases()
    if not cases:
        pytest.skip("no eval cases in this checkout")
    inputs = load_inputs(cases[0])
    repo = inputs.checkout(tmp_path_factory.mktemp("case") / "repo")
    return repo, inputs.range_base, inputs.range_head


def _blob(text: str) -> str:
    """A fast-import `data` command: its length in bytes, then the bytes.
    ref: https://git-scm.com/docs/git-fast-import#_data"""
    return f"data {len(text.encode())}\n{text}"


@pytest.fixture(scope="module")
def synth(tmp_path_factory) -> tuple[Path, list[str]]:
    """A repo of SYNTH_COMMITS commits, oldest first. The first adds `big.txt`
    (SYNTH_DIFF_LINES lines) and `many.kt` (SYNTH_HITS lines naming `needle`); each
    later one rewrites `counter.txt`."""
    repo = tmp_path_factory.mktemp("synth") / "repo"
    subprocess.run(["git", "init", "--quiet", str(repo)], check=True)
    stream = []
    for i in range(SYNTH_COMMITS):
        files = [("counter.txt", f"{i}\n")]
        if i == 0:
            files += [
                ("big.txt", "".join(f"line {n}\n" for n in range(SYNTH_DIFF_LINES))),
                (
                    "many.kt",
                    "".join(f"val needle{n} = {n}\n" for n in range(SYNTH_HITS)),
                ),
            ]
        stream.append(
            f"commit refs/heads/main\n"
            f"committer T <t@example.com> {1_700_000_000 + i} +0000\n"
            + _blob(f"Commit {i}\n")
            + "\n"
            + "".join(f"M 100644 inline {p}\n" + _blob(c) + "\n" for p, c in files)
        )
    git(repo, "fast-import", "--quiet", stdin="".join(stream))
    shas = git(repo, "log", "--reverse", "--format=%H", "main").split()
    return repo, shas


def tree_state(repo: Path) -> dict[str, str]:
    """Every file under `repo`, `.git` included, by content hash."""
    return {
        str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(repo.rglob("*"))
        if p.is_file()
    }


# --- Schemas -----------------------------------------------------------------------


def test_the_four_git_tools_are_declared():
    assert [t.name for t in REPO_TOOLS] == [
        "get_git_log",
        "get_git_diff",
        "git_blame",
        "grep_repo",
    ]


@pytest.mark.parametrize("tool", REPO_TOOLS, ids=lambda t: t.name)
def test_each_schema_is_strict(tool):
    definition = tool.definition()
    assert definition["strict"] is True
    assert set(definition) == {"name", "description", "input_schema", "strict"}
    schema = definition["input_schema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["required"] == list(schema["properties"])


@pytest.mark.parametrize("tool", REPO_TOOLS, ids=lambda t: t.name)
def test_each_schema_matches_its_function(tool):
    """The model's arguments are the function's parameters after `repo`, no more."""
    params = list(
        tool.function.__code__.co_varnames[1 : tool.function.__code__.co_argcount]
    )
    assert list(tool.input_schema["properties"]) == params


@pytest.mark.parametrize("tool", REPO_TOOLS, ids=lambda t: t.name)
def test_each_description_says_what_it_cannot_tell(tool):
    assert "cannot" in tool.description
    for word in HINT_WORDS:
        assert word not in tool.description.lower()


def test_call_refuses_an_extra_or_missing_property(case_repo):
    repo, base, head = case_repo
    log = REPO_TOOLS[0]
    with pytest.raises(ToolInputError, match="unexpected 'limit'"):
        log.call(repo, {"range": f"{base}..{head}", "paths": None, "limit": 5})
    with pytest.raises(ToolInputError, match="missing 'paths'"):
        log.call(repo, {"range": f"{base}..{head}"})
    with pytest.raises(ToolInputError, match="expected integer"):
        REPO_TOOLS[1].call(repo, {"sha": head, "path": None, "max_lines": "10"})
    # Control: the same call, well formed, runs.
    assert log.call(repo, {"range": f"{base}..{head}", "paths": None})["commits"]


# --- get_git_log -------------------------------------------------------------------


def test_log_lists_the_range_newest_first(case_repo):
    repo, base, head = case_repo
    result = get_git_log(repo, f"{base}..{head}", None)
    expected = git(repo, "log", "--format=%H", f"{base}..{head}").split()
    assert [c["sha"] for c in result["commits"]] == expected
    assert result["commit_count"] == len(expected) < MAX_COMMITS
    assert result["truncated"] is False
    assert result["range"]["head"].startswith(head)
    newest = result["commits"][0]
    assert newest["subject"] == git(repo, "log", "-1", "--format=%s", head).strip()
    assert (
        newest["files"]
        == git(repo, "diff", "--name-only", "--no-renames", f"{head}~1", head).split(
            "\n"
        )[:-1]
    )


def test_log_filters_by_path(case_repo):
    repo, base, head = case_repo
    everything = get_git_log(repo, f"{base}..{head}", None)["commits"]
    path = everything[0]["files"][0]
    result = get_git_log(repo, f"{base}..{head}", [path])
    assert 0 < len(result["commits"]) <= len(everything)
    assert all(path in c["files"] for c in result["commits"])


def test_log_stops_at_the_cap_and_says_so(synth):
    repo, shas = synth
    result = get_git_log(repo, f"{shas[0]}..{shas[-1]}", None)
    assert len(result["commits"]) == MAX_COMMITS
    assert result["commit_count"] == SYNTH_COMMITS - 1
    assert result["truncated"] is True
    assert result["commits"][0]["sha"] == shas[-1]


def test_log_at_exactly_the_cap_is_not_truncated(synth):
    repo, shas = synth
    base = shas[-1 - MAX_COMMITS]
    result = get_git_log(repo, f"{base}..{shas[-1]}", None)
    assert len(result["commits"]) == result["commit_count"] == MAX_COMMITS
    assert result["truncated"] is False


@pytest.mark.parametrize(
    "spec",
    ["", "HEAD", "..HEAD", "HEAD..", "HEAD...HEAD~1", "deadbeef..HEAD", "a b..HEAD"],
)
def test_log_refuses_a_range_it_cannot_resolve(case_repo, spec):
    repo, _, _ = case_repo
    with pytest.raises(ToolInputError):
        get_git_log(repo, spec, None)


# --- get_git_diff ------------------------------------------------------------------


def test_diff_shows_a_commit_whole_under_the_cap(case_repo):
    repo, _, head = case_repo
    result = get_git_diff(repo, head, None, None)
    expected = git(repo, "diff", "--no-renames", f"{head}~1", head)
    assert result["diff"] == expected.removesuffix("\n")
    assert result["line_count"] == len(expected.splitlines()) <= MAX_DIFF_LINES
    assert result["truncated"] is False
    assert result["message"] == git(repo, "log", "-1", "--format=%B", head).strip()
    assert result["diffed_against"] == git(repo, "rev-parse", f"{head}~1").strip()


def test_diff_is_cut_at_the_cap_and_says_so(synth):
    repo, shas = synth
    result = get_git_diff(repo, shas[0], "big.txt", None)
    assert len(result["diff"].split("\n")) == MAX_DIFF_LINES
    assert result["line_count"] > MAX_DIFF_LINES
    assert result["truncated"] is True
    # Asking for more than the cap still gets the cap.
    assert get_git_diff(repo, shas[0], "big.txt", 10_000)["diff"] == result["diff"]


def test_diff_honours_a_smaller_max_lines_and_a_path(synth):
    repo, shas = synth
    result = get_git_diff(repo, shas[0], "counter.txt", 3)
    assert len(result["diff"].split("\n")) == 3
    assert "big.txt" not in result["diff"]
    whole = get_git_diff(repo, shas[0], "counter.txt", None)
    assert whole["truncated"] is False
    assert "+0" in whole["diff"]
    assert whole["diffed_against"] == git_module._empty_tree(shas[0])


def test_diff_refuses_an_unknown_commit_or_a_bad_limit(case_repo):
    repo, _, head = case_repo
    with pytest.raises(ToolInputError):
        get_git_diff(repo, "0000000", None, None)
    with pytest.raises(ToolInputError):
        get_git_diff(repo, head, None, 0)


# --- git_blame ---------------------------------------------------------------------


def _a_changed_file(repo: Path, head: str) -> tuple[str, int]:
    """A file the head commit changed, and its line count."""
    path = git(repo, "diff", "--name-only", f"{head}~1", head).split("\n")[0]
    return path, len(git(repo, "show", f"{head}:{path}").split("\n")) - 1


def test_blame_names_the_commit_for_each_line(case_repo):
    repo, _, head = case_repo
    path, _ = _a_changed_file(repo, head)
    result = git_blame(repo, path, 1, 3, head)
    source = git(repo, "show", f"{head}:{path}").split("\n")
    assert [line["line"] for line in result["lines"]] == [1, 2, 3]
    assert [line["text"] for line in result["lines"]] == source[:3]
    expected = git(repo, "blame", "--porcelain", "-L1,3", head, "--", path)
    for line in result["lines"]:
        assert line["sha"] in expected
        assert line["date"].endswith("+00:00")
    assert result["truncated"] is False


def test_blame_is_at_the_given_commit_not_the_head(synth):
    repo, shas = synth
    assert git_blame(repo, "counter.txt", 1, 1, shas[3])["lines"][0]["text"] == "3"
    assert git_blame(repo, "counter.txt", 1, 1, shas[3])["lines"][0]["sha"] == shas[3]


def test_blame_is_cut_at_the_cap_and_says_so(synth):
    repo, shas = synth
    result = git_blame(repo, "big.txt", 1, SYNTH_DIFF_LINES, shas[-1])
    assert len(result["lines"]) == MAX_BLAME_LINES
    assert result["lines"][-1]["text"] == f"line {MAX_BLAME_LINES - 1}"
    assert result["truncated"] is True
    control = git_blame(repo, "big.txt", 1, MAX_BLAME_LINES, shas[-1])
    assert control["truncated"] is False
    assert control["lines"] == result["lines"]


@pytest.mark.parametrize("start,end", [(0, 3), (5, 4), (-1, 2)])
def test_blame_refuses_a_bad_span(synth, start, end):
    repo, shas = synth
    with pytest.raises(ToolInputError):
        git_blame(repo, "big.txt", start, end, shas[-1])


def test_blame_past_the_end_of_the_file_is_gits_error(synth):
    repo, shas = synth
    with pytest.raises(GitError, match="has only 1 line"):
        git_blame(repo, "counter.txt", 5, 6, shas[-1])


# --- grep_repo ---------------------------------------------------------------------


def test_grep_finds_what_git_grep_finds(case_repo):
    repo, _, head = case_repo
    everywhere = grep_repo(repo, r"^import ", None, None, head)
    expected = git(repo, "grep", "-c", "-E", r"^import ", head).split()
    assert everywhere["hit_count"] == sum(int(r.rsplit(":", 1)[1]) for r in expected)
    # One file's imports: under the cap, so every hit comes back.
    path, count = expected[0].removeprefix(f"{head}:").rsplit(":", 1)
    result = grep_repo(repo, r"^import ", [path], None, head)
    assert len(result["hits"]) == result["hit_count"] == int(count) <= MAX_GREP_HITS
    assert result["truncated"] is False
    for hit in everywhere["hits"] + result["hits"]:
        source = git(repo, "show", f"{head}:{hit['path']}").split("\n")
        assert source[hit["line"] - 1] == hit["text"]


def test_grep_is_cut_at_the_cap_and_says_so(synth):
    repo, shas = synth
    result = grep_repo(repo, "needle", None, None, shas[-1])
    assert len(result["hits"]) == MAX_GREP_HITS
    assert result["hit_count"] == SYNTH_HITS
    assert result["truncated"] is True
    assert grep_repo(repo, "needle", None, 10_000, shas[-1])["hits"] == result["hits"]
    control = grep_repo(repo, "needle", None, 7, shas[-1])
    assert len(control["hits"]) == 7


def test_grep_with_no_match_is_an_empty_answer(synth):
    repo, shas = synth
    result = grep_repo(repo, "no such text anywhere", None, None, shas[-1])
    assert result["hits"] == [] and result["hit_count"] == 0


def test_grep_reads_the_commit_not_the_working_tree(synth):
    repo, shas = synth
    assert grep_repo(repo, "^0$", ["counter.txt"], None, shas[0])["hit_count"] == 1
    assert grep_repo(repo, "^0$", ["counter.txt"], None, shas[-1])["hit_count"] == 0
    # fast-import writes no working tree; one written by hand is not searched.
    (repo / "loose.kt").write_text("needle in the working tree\n")
    assert grep_repo(repo, "working tree", None, None, shas[-1])["hit_count"] == 0


def test_grep_paths_limit_the_search(synth):
    repo, shas = synth
    assert grep_repo(repo, "line", ["many.kt"], None, shas[-1])["hit_count"] == 0
    assert grep_repo(repo, "line", ["big.txt"], None, shas[-1])["truncated"] is True


# --- Read-only, whatever the model writes ------------------------------------------


@pytest.mark.parametrize("injection", INJECTIONS)
def test_no_argument_is_read_as_an_option(synth, tmp_path, injection):
    repo, shas = synth
    out = tmp_path / "written"
    text = injection.format(out=out)
    head = shas[-1]
    # As a pattern: searched for, literally, and not found.
    assert grep_repo(repo, text, None, None, head)["hit_count"] == 0
    # As a path: no such file.
    assert grep_repo(repo, "needle", [text], None, head)["hit_count"] == 0
    assert get_git_log(repo, f"{shas[0]}..{head}", [text])["commits"] == []
    assert get_git_diff(repo, head, text, None)["diff"] == ""
    with pytest.raises(GitError):
        git_blame(repo, text, 1, 1, head)
    # As a revision: names no commit.
    with pytest.raises(ToolInputError):
        get_git_diff(repo, text, None, None)
    with pytest.raises(ToolInputError):
        get_git_log(repo, f"{text}..{head}", None)
    with pytest.raises(ToolInputError):
        grep_repo(repo, "needle", None, None, text)
    assert not out.exists()


def test_no_tool_writes_to_the_repo(case_repo, monkeypatch):
    """Every tool, called on the case repo, leaves every file in it (`.git` included)
    as it was, and runs only allow-listed subcommands."""
    repo, base, head = case_repo
    before = tree_state(repo)
    calls: list[list[str]] = []
    real_run = subprocess.run

    def recording_run(argv, *args, **kwargs):
        calls.append(argv)
        return real_run(argv, *args, **kwargs)

    monkeypatch.setattr(git_module.subprocess, "run", recording_run)
    log = get_git_log(repo, f"{base}..{head}", None)
    path = log["commits"][0]["files"][0]
    get_git_diff(repo, head, None, None)
    git_blame(repo, path, 1, 2, head)
    grep_repo(repo, "import", None, None, head)

    assert tree_state(repo) == before
    subcommands = {argv[argv.index("--literal-pathspecs") + 1] for argv in calls}
    assert subcommands <= ALLOWED_SUBCOMMANDS
    assert subcommands == {"log", "diff", "blame", "grep", "cat-file"}


def test_the_allow_list_is_unchanged_and_read_only():
    assert ALLOWED_SUBCOMMANDS == {
        "log",
        "diff",
        "blame",
        "grep",
        "cat-file",
        "merge-base",
    }


def test_the_module_calls_git_only_through_run_git():
    source = Path(repo_tools.__file__).read_text()
    assert "subprocess" not in source
    assert "_run(" not in source
