import json

from perfettoagent.cli import main


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
