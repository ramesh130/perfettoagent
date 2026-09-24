"""The Anthropic loop: the SDK's beta Tool Runner, streamed (docs/tech-stack.md "Model
and SDK", ADR-0022).

Each tool is a `perfettoagent.tools.Tool` handed to `beta_tool` with its hand-written
strict schema unchanged, and every call goes through `Tool.call` (ADR-0018). The frozen
system prompt carries a `cache_control` breakpoint.

ref: https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
ref: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
ref: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
"""

from anthropic import beta_tool
from anthropic.lib.tools import ToolError

from perfettoagent import models
from perfettoagent.loop import (
    MAX_TOKENS,
    MAX_TURNS,
    Cost,
    Ending,
    ModelError,
    RunFailed,
    call_tool,
    cut_off,
    out_of_turns,
    refused,
)
from perfettoagent.tools import Tool


class AnthropicLoop:
    """One Tool Runner conversation, and what it cost."""

    def __init__(self, client, model: str, effort: str, bound: list):
        self._client = client
        self._model = model
        self._effort = effort
        self._fatal: list[RunFailed] = []
        self._tools = [self._runnable(tool, ctx) for tool, ctx in bound]
        self.cost = Cost(model)

    def run(self, system: str, user_message: str, output_schema: dict) -> Ending:
        runner = self._client.beta.messages.tool_runner(
            model=self._model,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self._effort,
                "format": {"type": "json_schema", "schema": output_schema},
            },
            system=[
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ],
            tools=self._tools,
            messages=[{"role": "user", "content": user_message}],
            max_iterations=MAX_TURNS,
            stream=True,
        )
        message = None
        for stream in runner:
            message = stream.get_final_message()
            self._count(message)
            if message.stop_reason == "tool_use":
                # Run this turn's tools now, not when the runner next asks: a failure
                # of the run must stop it here, before another request. The runner
                # reuses this response rather than calling the tools again.
                runner.generate_tool_call_response()
                if self._fatal:
                    raise self._fatal[0]
        return _ending(message)

    def _count(self, message) -> None:
        usage = {f: getattr(message.usage, f, None) or 0 for f in models.USAGE_FIELDS}
        calls = sum(1 for b in message.content if b.type == "tool_use")
        self.cost.add(calls, usage)

    def _runnable(self, tool: Tool, context):
        """`tool` as the Tool Runner takes it: its hand-written schema and description
        unchanged, strict, and answered through `Tool.call`."""

        def call(**arguments) -> str:
            try:
                return call_tool(tool, context, arguments)
            except ModelError as e:
                raise ToolError(str(e)) from e
            except RunFailed as e:
                # The runner would show any exception to the model as an error result;
                # the run stops before the next request instead.
                self._fatal.append(e)
                raise ToolError("internal error; the run is stopping") from e

        return beta_tool(
            call,
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            strict=True,
        )


def _ending(message) -> Ending:
    """`stop_reason` is read first: a refusal or a cut-off answer has no content to
    trust."""
    reason = message.stop_reason
    if reason == "refusal":
        details = getattr(message, "stop_details", None)
        return refused(getattr(details, "category", None) or "unspecified")
    if reason == "max_tokens":
        return cut_off("max_tokens")
    # The runner returns on a tool_use turn only when max_iterations is reached; any
    # other tool_use turn it answers and continues.
    if reason == "tool_use":
        return out_of_turns()
    if reason not in ("end_turn", "stop_sequence"):
        return Ending(
            unanswered=f"the run ended without an answer (stop_reason: {reason})"
        )
    return Ending(text="".join(b.text for b in message.content if b.type == "text"))
