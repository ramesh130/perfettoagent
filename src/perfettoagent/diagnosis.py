"""`diagnosis.json`, schema 1: defined once, here, as JSON Schema, and checked in code.

Two schemas, because two parties write a diagnosis (ADR-0006):

- OUTPUT_SCHEMA is what the model writes: the verdict, the metric, its confidence, the
  culprit, the claims with their citations, and caveats. It is strict in the sense the
  Anthropic API's `output_config.format` requires, so the agent (roadmap item 7) passes
  it there unchanged: every object has `additionalProperties: false` and lists every
  property as required, and an optional value is `anyOf [..., null]`.
- DIAGNOSIS_SCHEMA is the file we write: the model's output after `verify` has run,
  plus what only our code knows. Each claim gets an id; each citation gets the
  verifier's result (a trace citation's fresh `row_count`, a commit citation's full
  sha, and the `error` that failed it, if any); failed claims move to
  `dropped_claims`; and `verification` and `run` record what the verifier did and
  what the run cost.

None of the fields our code fills are in OUTPUT_SCHEMA, so a model that pre-fills
`dropped_claims`, a `row_count`, or any "verified" flag fails validation instead of
being trusted.

The validator is a small interpreter for the JSON Schema keywords the two schemas use
and nothing more. It refuses a schema with any other keyword, so a keyword added here
later cannot be silently ignored by the check. The API's structured outputs support the
same subset (no numeric or string-length constraints), so what the model can be held to
and what we check are the same thing.

ref: https://json-schema.org/understanding-json-schema/reference
ref: https://docs.claude.com/en/docs/build-with-claude/structured-outputs
"""

SCHEMA_VERSION = 1

VERDICTS = ("regression", "no_regression", "inconclusive")
SIDES = ("baseline", "current")

# The model's own confidence, in words: coarse on purpose, since nothing is ever scored
# on it (CLAUDE.md, eval integrity) and a number would suggest a precision it lacks.
CONFIDENCES = ("low", "medium", "high")

# `direct`: the culprit commit changed the code the evidence points at. `correlated`:
# it is the likeliest commit in the range, but no trace row points into its diff.
ATTRIBUTIONS = ("direct", "correlated")

# The keywords the validator understands. A schema using any other is refused.
_KEYWORDS = {
    "type",
    "enum",
    "const",
    "anyOf",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "description",
}

_STRING = {"type": "string"}
_NUMBER = {"type": "number"}
_INTEGER = {"type": "integer"}


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


def _enum(values) -> dict:
    return {"type": "string", "enum": list(values)}


def _object(description: str, **properties) -> dict:
    """A strict object: no other properties, and every property required."""
    return {
        "type": "object",
        "description": description,
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _array(items: dict) -> dict:
    return {"type": "array", "items": items}


_TRACE_CITATION_FIELDS = {
    "kind": {"type": "string", "const": "trace"},
    "trace": {
        **_enum(SIDES),
        "description": "Which trace the SQL is re-run on.",
    },
    "sql": {
        "type": "string",
        "description": (
            "One SELECT or WITH query, optionally preceded by INCLUDE PERFETTO MODULE "
            "lines, e.g. a metric's sql_used verbatim. It must return at least one row."
        ),
    },
}
_COMMIT_CITATION_FIELDS = {
    "kind": {"type": "string", "const": "commit"},
    "sha": {
        "type": "string",
        "description": "A commit inside the range, as 7 to 64 hex digits.",
    },
    "path": {
        **_nullable(_STRING),
        "description": "A file or directory the commit changes, or null.",
    },
}

_METRIC = _nullable(
    _object(
        "The regressed (or checked) metric, as compute_metric returned it.",
        name=_STRING,
        unit=_STRING,
        baseline=_nullable(_NUMBER),
        current=_nullable(_NUMBER),
        delta=_nullable(_NUMBER),
        sql_used=_STRING,
    )
)
_CULPRIT = _nullable(
    _object(
        "The commit the regression is attributed to, or null for none.",
        commit=_STRING,
        files=_array(_STRING),
        attribution=_enum(ATTRIBUTIONS),
    )
)
_CAVEATS = _array(_STRING)

OUTPUT_SCHEMA = _object(
    "A cited diagnosis of one trace pair and one git range.",
    verdict=_enum(VERDICTS),
    metric=_METRIC,
    confidence=_enum(CONFIDENCES),
    culprit=_CULPRIT,
    claims=_array(
        _object(
            "One statement of fact and the citations that back it.",
            text=_STRING,
            citations=_array(
                {
                    "anyOf": [
                        _object("A trace row.", **_TRACE_CITATION_FIELDS),
                        _object("A commit.", **_COMMIT_CITATION_FIELDS),
                    ]
                }
            ),
        )
    ),
    caveats=_CAVEATS,
)

# A citation after verification: `error` is null exactly when it passed.
_VERIFIED_CITATION = {
    "anyOf": [
        _object(
            "A trace citation, re-run.",
            **_TRACE_CITATION_FIELDS,
            row_count=_nullable(_INTEGER),
            error=_nullable(_STRING),
        ),
        _object(
            "A commit citation, checked against the range.",
            **_COMMIT_CITATION_FIELDS,
            commit=_nullable(_STRING),
            error=_nullable(_STRING),
        ),
    ]
}
_VERIFIED_CLAIM = {
    "id": _STRING,
    "text": _STRING,
    "citations": _array(_VERIFIED_CITATION),
}

DIAGNOSIS_SCHEMA = _object(
    "diagnosis.json: the model's output after the verifier, and the run's cost.",
    schema_version={"type": "integer", "const": SCHEMA_VERSION},
    verdict=_enum(VERDICTS),
    metric=_METRIC,
    # null when the verifier changed the verdict or dropped the culprit: the model's
    # confidence was in a diagnosis that no longer stands.
    confidence=_nullable(_enum(CONFIDENCES)),
    culprit=_CULPRIT,
    claims=_array(
        _object("A claim every citation of which passed.", **_VERIFIED_CLAIM)
    ),
    caveats=_CAVEATS,
    dropped_claims=_array(
        _object(
            "A claim the verifier removed, and why.",
            **_VERIFIED_CLAIM,
            reason=_STRING,
        )
    ),
    verification=_object(
        "What the verifier did.",
        verdict_before=_enum(VERDICTS),
        explanation=_nullable(_STRING),
        culprit_dropped=_nullable(_STRING),
        metric_dropped=_nullable(_STRING),
        citations_checked=_INTEGER,
        citations_passed=_INTEGER,
        wall_time_s=_NUMBER,
    ),
    # null when the verifier ran outside an agent run (a test, a re-verification).
    run=_nullable(
        _object(
            "The agent run that produced the output.",
            tool_calls=_INTEGER,
            usage=_object(
                "Tokens, summed over the run's requests.",
                input_tokens=_INTEGER,
                output_tokens=_INTEGER,
                cache_read_input_tokens=_INTEGER,
                cache_creation_input_tokens=_INTEGER,
            ),
            usd=_NUMBER,
            wall_time_s=_NUMBER,
        )
    ),
)


class DiagnosisInvalid(ValueError):
    """A diagnosis does not match its schema. `errors` lists each mismatch by path."""

    def __init__(self, what: str, errors: list[str]):
        self.errors = errors
        super().__init__(f"{what} does not match its schema: " + "; ".join(errors))


def check_output(output) -> None:
    """Raises DiagnosisInvalid unless `output` matches OUTPUT_SCHEMA: the local check
    of the model's structured output (docs/tech-stack.md)."""
    errors = validate(output, OUTPUT_SCHEMA)
    if errors:
        raise DiagnosisInvalid("the model's output", errors)


def check_diagnosis(diagnosis) -> None:
    """Raises DiagnosisInvalid unless `diagnosis` matches DIAGNOSIS_SCHEMA."""
    errors = validate(diagnosis, DIAGNOSIS_SCHEMA)
    if errors:
        raise DiagnosisInvalid("diagnosis.json", errors)


def validate(value, schema: dict, path: str = "$") -> list[str]:
    """Every way `value` fails `schema`, as `path: problem` strings; [] if none."""
    unknown = schema.keys() - _KEYWORDS
    if unknown:
        raise ValueError(f"unsupported schema keyword(s) at {path}: {sorted(unknown)}")

    if "anyOf" in schema:
        branches = [(s, validate(value, s, path)) for s in schema["anyOf"]]
        if all(errors for _, errors in branches):
            # Report the branch the value was meant for: its type first, then its
            # `const` tags (a citation's `kind`), then the fewest errors.
            return min(branches, key=lambda b: _fit(value, *b))[1]
        return []

    if "type" in schema and not _is_type(value, schema["type"]):
        return [f"{path}: expected {schema['type']}, got {_type_name(value)}"]
    if "const" in schema and value != schema["const"]:
        return [f"{path}: expected {schema['const']!r}, got {value!r}"]
    if "enum" in schema and value not in schema["enum"]:
        return [f"{path}: expected one of {schema['enum']}, got {value!r}"]

    errors: list[str] = []
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", ()):
            if name not in value:
                errors.append(f"{path}: missing {name!r}")
        if schema.get("additionalProperties") is False:
            for name in value.keys() - properties.keys():
                errors.append(f"{path}: unexpected {name!r}")
        for name, subschema in properties.items():
            if name in value:
                errors += validate(value[name], subschema, f"{path}.{name}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += validate(item, schema["items"], f"{path}[{i}]")
    return errors


def _fit(value, schema: dict, errors: list[str]) -> tuple:
    """How badly `value` misses one anyOf branch; lower is closer."""
    wrong_type = "type" in schema and not _is_type(value, schema["type"])
    wrong_tag = isinstance(value, dict) and any(
        name in value and value[name] != sub["const"]
        for name, sub in schema.get("properties", {}).items()
        if "const" in sub
    )
    return (wrong_type, wrong_tag, len(errors))


def _is_type(value, name: str) -> bool:
    # bool is an int in Python, but not a number in JSON.
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    return isinstance(value, _PYTHON_TYPES[name])


_PYTHON_TYPES = {
    "string": str,
    "boolean": bool,
    "null": type(None),
    "object": dict,
    "array": list,
}


def _type_name(value) -> str:
    return type(value).__name__
