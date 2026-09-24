"""API keys from the environment or `.env` (ADR-0020 "Credentials"). The keys here
are made up; no test reads the repo's own `.env`."""

import pytest

from perfettoagent.credentials import api_key, redact


def dotenv(tmp_path, text: str):
    path = tmp_path / ".env"
    path.write_text(text)
    return path


def test_the_environment_wins_over_dotenv(tmp_path):
    path = dotenv(tmp_path, "OPENAI_API_KEY=from-file\n")
    environ = {"OPENAI_API_KEY": "from-env"}
    assert api_key("OPENAI_API_KEY", environ=environ, dotenv=path) == "from-env"


def test_dotenv_is_read_when_the_environment_lacks_the_key(tmp_path):
    path = dotenv(
        tmp_path,
        "# a comment\n"
        "\n"
        "export OPENAI_API_KEY='quoted value'\n"
        'ANTHROPIC_API_KEY = "other"\n',
    )
    assert api_key("OPENAI_API_KEY", environ={}, dotenv=path) == "quoted value"
    assert api_key("ANTHROPIC_API_KEY", environ={}, dotenv=path) == "other"


def test_an_empty_environment_value_falls_through_to_dotenv(tmp_path):
    path = dotenv(tmp_path, "OPENAI_API_KEY=from-file\n")
    assert api_key("OPENAI_API_KEY", environ={"OPENAI_API_KEY": ""}, dotenv=path) == (
        "from-file"
    )


def test_no_key_anywhere_is_none(tmp_path):
    assert api_key("OPENAI_API_KEY", environ={}, dotenv=tmp_path / "absent") is None
    path = dotenv(tmp_path, "OPENAI_API_KEY=\nnot a line\n")
    assert api_key("OPENAI_API_KEY", environ={}, dotenv=path) is None


def test_only_the_two_key_names_are_read(tmp_path):
    """Other names in `.env` are neither returned nor asked for."""
    path = dotenv(tmp_path, "SOMETHING_ELSE=x\n")
    with pytest.raises(ValueError, match="not a key"):
        api_key("SOMETHING_ELSE", environ={}, dotenv=path)


def test_redact_removes_the_keys_and_anything_shaped_like_one(tmp_path):
    path = dotenv(tmp_path, "ANTHROPIC_API_KEY=plainsecretvalue\n")
    message = (
        "Incorrect API key provided: sk-proj-****abcd. "
        "Also sk-ant-api03-xyz and plainsecretvalue."
    )
    redacted = redact(message, environ={}, dotenv=path)
    assert "sk-" not in redacted
    assert "abcd" not in redacted
    assert "plainsecretvalue" not in redacted
    assert redacted.startswith("Incorrect API key provided: [redacted]")
