"""diagnosis.json schema 1: strict enough for output_config.format; its validator."""

import json

import pytest

from perfettoagent.diagnosis import (
    DIAGNOSIS_SCHEMA,
    OUTPUT_SCHEMA,
    DiagnosisInvalid,
    check_output,
    validate,
)


def _objects(schema: dict, path="$"):
    """Every object schema inside `schema`, with its path."""
    if schema.get("type") == "object":
        yield path, schema
        for name, sub in schema["properties"].items():
            yield from _objects(sub, f"{path}.{name}")
    if "items" in schema:
        yield from _objects(schema["items"], f"{path}[]")
    for i, sub in enumerate(schema.get("anyOf", ())):
        yield from _objects(sub, f"{path}|{i}")


@pytest.mark.parametrize("schema", [OUTPUT_SCHEMA, DIAGNOSIS_SCHEMA])
def test_every_object_is_strict(schema):
    # What the API's structured outputs require of every object in the schema.
    objects = list(_objects(schema))
    assert objects
    for path, obj in objects:
        assert obj["additionalProperties"] is False, path
        assert sorted(obj["required"]) == sorted(obj["properties"]), path
    json.dumps(schema)


def test_the_model_schema_has_none_of_the_fields_our_code_fills():
    text = json.dumps(OUTPUT_SCHEMA)
    for field in (
        "dropped_claims",
        "row_count",
        "schema_version",
        "verification",
        "run",
    ):
        assert f'"{field}"' not in text


def _good() -> dict:
    return {
        "verdict": "regression",
        "metric": None,
        "confidence": "medium",
        "culprit": {"commit": "abcdef1", "files": [], "attribution": "correlated"},
        "claims": [
            {
                "text": "t",
                "citations": [
                    {"kind": "trace", "trace": "current", "sql": "SELECT 1"},
                    {"kind": "commit", "sha": "abcdef1", "path": None},
                ],
            }
        ],
        "caveats": [],
    }


def test_a_good_output_validates():
    check_output(_good())


@pytest.mark.parametrize(
    ("tamper", "error"),
    [
        (lambda o: o.update(confidence=0.9), "$.confidence: expected string"),
        (lambda o: o.update(verdict="bad"), "$.verdict: expected one of"),
        (lambda o: o.pop("caveats"), "$: missing 'caveats'"),
        (lambda o: o.update(verified=True), "$: unexpected 'verified'"),
        (
            lambda o: o["claims"][0]["citations"][0].update(trace="both"),
            "$.claims[0].citations[0].trace: expected one of",
        ),
        (
            lambda o: o["claims"][0]["citations"][1].update(path=3),
            "$.claims[0].citations[1].path: expected string",
        ),
        (
            lambda o: o.update(metric={"name": "m"}),
            "$.metric: missing 'unit'",
        ),
    ],
)
def test_a_bad_output_is_refused_with_the_path_of_the_problem(tamper, error):
    out = _good()
    tamper(out)
    with pytest.raises(DiagnosisInvalid) as e:
        check_output(out)
    assert any(err.startswith(error) for err in e.value.errors), e.value.errors


def test_a_bool_is_not_a_number():
    assert validate(True, {"type": "integer"})
    assert validate(1.5, {"type": "integer"})
    assert validate(1, {"type": "number"}) == []


def test_an_unknown_schema_keyword_is_refused_not_ignored():
    with pytest.raises(ValueError, match="minimum"):
        validate(1, {"type": "integer", "minimum": 2})
