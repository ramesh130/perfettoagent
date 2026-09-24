import json

import pytest
from fake_model import FakeModel, reply, text
from test_diagnose import answer, build_repo

from perfettoagent import agent
from perfettoagent.cli import main
from perfettoagent.diagnosis import check_diagnosis


def test_main_without_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage: perfettoagent" in capsys.readouterr().out


def tp(trace, sql, *extra):
    return main(["tp", "--trace", str(trace), "--sql", sql, *extra])


def test_tp_prints_rows_and_the_row_count(
    trace_processor, tiny_trace, monkeypatch, capsys
):
    monkeypatch.setenv("TRACE_PROCESSOR", str(trace_processor))
    sql = "select id, dur from slice order by dur desc, id limit 2"
    assert tp(tiny_trace, sql) == 0
    assert capsys.readouterr().out.splitlines() == [
        "id   dur",
        "---  ---------",
        "142  601074250",
        "116  568439417",
        "(2 rows)",
    ]


def test_tp_says_when_rows_were_cut(trace_processor, tiny_trace, monkeypatch, capsys):
    monkeypatch.setenv("TRACE_PROCESSOR", str(trace_processor))
    assert tp(tiny_trace, "select id from slice") == 0
    out = capsys.readouterr().out.splitlines()
    assert len(out) == 2 + 200 + 1
    assert out[-1] == "(840 rows; showing the first 200)"


def test_tp_json_is_the_query_trace_result(
    trace_processor, tiny_trace, monkeypatch, capsys
):
    monkeypatch.setenv("TRACE_PROCESSOR", str(trace_processor))
    assert tp(tiny_trace, "select count(*) as n from slice", "--json") == 0
    assert json.loads(capsys.readouterr().out) == {
        "columns": ["n"],
        "rows": [[840]],
        "row_count": 1,
        "truncated": False,
    }


def test_tp_rejects_a_non_select(tiny_trace, tmp_path, monkeypatch, capsys):
    # No trace processor is needed, or reached: the gate runs first.
    monkeypatch.setenv("TRACE_PROCESSOR", str(tmp_path / "absent"))
    assert tp(tiny_trace, "SELECT 1; DELETE FROM slice") == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "rejected: only one statement" in captured.err


def test_tp_reports_a_sql_error(trace_processor, tiny_trace, monkeypatch, capsys):
    monkeypatch.setenv("TRACE_PROCESSOR", str(trace_processor))
    assert tp(tiny_trace, "select * from nope") == 1
    assert "no such table: nope" in capsys.readouterr().err


def test_tp_fails_clearly_without_a_usable_trace_processor(
    tiny_trace, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("TRACE_PROCESSOR", str(tmp_path / "absent"))
    assert tp(tiny_trace, "select 1") == 1
    assert "is not executable" in capsys.readouterr().err


# --- diagnose: the model is faked, the client injected where the CLI builds one -------


@pytest.fixture(scope="module")
def repo(tmp_path_factory) -> dict:
    return build_repo(tmp_path_factory.mktemp("cli") / "checkout-q9")


@pytest.fixture
def cli_model(monkeypatch, trace_processor):
    """Makes the CLI's `anthropic.Anthropic()` return a fake model's client, and
    points it at the real trace processor. Returns a setter for the script."""
    monkeypatch.setenv("TRACE_PROCESSOR", str(trace_processor))

    def use(script) -> FakeModel:
        fake = FakeModel(script)
        monkeypatch.setattr(agent.anthropic, "Anthropic", lambda: fake.client)
        return fake

    return use


def diagnose_cli(repo, trace, out, *extra):
    return main(
        [
            "diagnose",
            "--baseline", str(trace),
            "--current", str(trace),
            "--repo", str(repo["path"]),
            "--range", repo["range"],
            "--out", str(out),
            *extra,
        ]
    )  # fmt: skip


def test_diagnose_writes_a_verified_diagnosis(
    cli_model, repo, tiny_trace, tmp_path, capsys
):
    cli_model(lambda request, turn: reply(text(answer(repo))))
    out = tmp_path / "diagnosis.json"
    assert diagnose_cli(repo, tiny_trace, out) == 0
    diagnosis = json.loads(out.read_text())
    check_diagnosis(diagnosis)
    assert diagnosis["verdict"] == "regression"
    printed = capsys.readouterr().out
    assert printed.startswith(f"regression, commit {repo['sha']['change'][:12]}: ")
    assert "1 claims kept, 0 dropped; 0 tool calls" in printed


def test_diagnose_writes_a_refusal_as_inconclusive(
    cli_model, repo, tiny_trace, tmp_path
):
    cli_model(lambda request, turn: reply(stop_reason="refusal"))
    out = tmp_path / "diagnosis.json"
    assert diagnose_cli(repo, tiny_trace, out) == 0
    assert json.loads(out.read_text())["verdict"] == "inconclusive"


def test_diagnose_writes_nothing_for_an_invalid_answer(
    cli_model, repo, tiny_trace, tmp_path, capsys
):
    cli_model(lambda request, turn: reply(text({"verdict": "regression"})))
    out = tmp_path / "diagnosis.json"
    assert diagnose_cli(repo, tiny_trace, out) == 1
    assert not out.exists()
    assert "does not match its schema" in capsys.readouterr().err


def test_diagnose_rejects_a_bad_range_before_any_request(
    cli_model, repo, tiny_trace, tmp_path, capsys
):
    fake = cli_model(lambda request, turn: reply(text(answer(repo))))
    out = tmp_path / "diagnosis.json"
    bad = {**repo, "range": "nothing..here"}
    assert diagnose_cli(bad, tiny_trace, out) == 2
    assert fake.requests == []
    assert not out.exists()
    assert "rejected: the range's base" in capsys.readouterr().err
