"""What an agent tool is here: a plain function, and beside it a hand-written strict
input schema and a description that says what the tool cannot tell the model
(ADR-0018, docs/tech-stack.md "Agent tool surface and limits").

A `Tool` is the one declaration the rest of the code reads. `definition()` is the tool
as the Messages API takes it, `strict: true` included; the agent loop (roadmap item 7)
hands the same schema to the SDK's `beta_tool(..., input_schema=..., strict=True)`,
which sends a hand-written schema unchanged. `call()` checks the model's arguments
against that schema before the function runs, because the SDK checks a hand-written
schema only as far as the function's type hints go.

Schemas use the subset `diagnosis.validate` interprets, which is also the subset strict
tool use supports: no `minimum`, `maximum` or string lengths. A tool's limits are
therefore enforced in its function, and said in its description. Like the diagnosis
output schema, every property is required and an optional one is `anyOf [..., null]`:
the model always says what it wants, and null means "the default".

ref: https://docs.claude.com/en/docs/agents-and-tools/tool-use/implement-tool-use
ref: https://docs.claude.com/en/docs/build-with-claude/structured-outputs
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from perfettoagent.diagnosis import validate

STRING = {"type": "string"}
INTEGER = {"type": "integer"}


class ToolInputError(ValueError):
    """The model's arguments are not something the tool can answer: they fail the
    schema, or name a commit, range or line that does not exist. The message is for
    the model to read, and says what to change."""


def nullable(schema: dict) -> dict:
    """`schema`, or null for the tool's default."""
    return {"anyOf": [schema, {"type": "null"}]}


def array(items: dict) -> dict:
    return {"type": "array", "items": items}


def described(schema: dict, description: str) -> dict:
    return {**schema, "description": description}


def strict_input(**properties: dict) -> dict:
    """A tool's input: an object with these properties, every one required, no other."""
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


@dataclass(frozen=True)
class Tool:
    """One agent tool: what the model is shown, and the function that answers it.

    `function(context, **arguments)` returns a JSON-serialisable dict. `context` is what
    the run binds and the model never names: the target repo's path, for the git tools.
    """

    name: str
    description: str
    input_schema: dict
    function: Callable[..., dict]

    def definition(self) -> dict:
        """The tool as the Messages API's `tools` list takes it."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "strict": True,
        }

    def call(self, context: Any, arguments: dict) -> dict:
        """Runs the tool on the model's `arguments`, after checking them against the
        schema; raises ToolInputError if they fail it."""
        errors = validate(arguments, self.input_schema, "input")
        if errors:
            raise ToolInputError(f"{self.name}: " + "; ".join(errors))
        return self.function(context, **arguments)
