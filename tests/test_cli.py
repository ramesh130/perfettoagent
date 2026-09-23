from perfettoagent.cli import main


def test_main_without_command_prints_help(capsys):
    assert main([]) == 0
    assert "usage: perfettoagent" in capsys.readouterr().out
