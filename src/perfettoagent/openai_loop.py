"""The OpenAI loop: the Responses API, streamed, with the tool loop written by hand,
since the `openai` SDK has no tool runner (ADR-0020, ADR-0023).

Each turn is one `responses.create(stream=True)`. Every `function_call` in its output is
answered with a `function_call_output` of the same `call_id`, through `Tool.call`, and
the next request replays the whole history: `store` is false, so nothing of the run is
kept on OpenAI's servers, and each reasoning item comes back with its
`encrypted_content` so it can be replayed. The frozen system prompt is the first
`developer` item, and the tools and output format are the same bytes on every request,
so the prefix is cached (implicit caching). Tool choice is `auto`, never forced.

A turn with no function call is the answer: its `output_text` is the structured output
(`text.format`, strict). A refusal, or a response `incomplete` for any reason (the
output cap above all), ends the run with no answer; neither is retried.

ref: https://developers.openai.com/api/docs/guides/function-calling
ref: https://developers.openai.com/api/docs/guides/structured-outputs
ref: https://developers.openai.com/api/docs/guides/reasoning
ref: https://developers.openai.com/api/docs/guides/prompt-caching
"""

import json

from perfettoagent.loop import (
    MAX_TOKENS,
    MAX_TURNS,
    Cost,
    Ending,
    ModelError,
    RunFailed,
    call_tool,
    cut_off,
    for_model,
    out_of_turns,
    refused,
)

# The events that end a streamed response, each carrying the whole response.
_FINAL_EVENTS = ("response.completed", "response.incomplete", "response.failed")

# A refusal's text is the model's; kept short, it is a caveat, not a transcript.
MAX_REFUSAL_CHARS = 300


class OpenAILoop:
    """One Responses API conversation, and what it cost."""

    def __init__(self, client, model: str, effort: str, bound: list):
        self._client = client
        self._model = model
        self._effort = effort
        self._bound = {tool.name: (tool, ctx) for tool, ctx in bound}
        self._tools = [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
                "strict": True,
            }
            for tool, _ in bound
        ]
        self.cost = Cost(model)

    def run(self, system: str, user_message: str, output_schema: dict) -> Ending:
        output_format = {
            "type": "json_schema",
            "name": "diagnosis",
            "schema": output_schema,
            "strict": True,
        }
        history: list = [
            {"role": "developer", "content": system},
            {"role": "user", "content": user_message},
        ]
        for _ in range(MAX_TURNS):
            response = self._request(history, output_format)
            self._count(response)
            if response.status == "incomplete":
                reason = getattr(response.incomplete_details, "reason", None)
                return _incomplete(reason)
            if response.status != "completed":
                raise RunFailed(
                    f"the response ended {response.status}: {response.error}"
                )
            refusal = _refusal(response)
            if refusal is not None:
                return refused(refusal)
            calls = [item for item in response.output if item.type == "function_call"]
            if not calls:
                return Ending(text=response.output_text)
            history += [
                item.model_dump(mode="json", exclude_none=True)
                for item in response.output
            ]
            history += [self._answer(call) for call in calls]
        return out_of_turns()

    def _request(self, history: list, output_format: dict):
        stream = self._client.responses.create(
            model=self._model,
            input=history,
            tools=self._tools,
            tool_choice="auto",
            text={"format": output_format},
            reasoning={"effort": self._effort},
            max_output_tokens=MAX_TOKENS,
            store=False,
            include=["reasoning.encrypted_content"],
            stream=True,
        )
        final = None
        for event in stream:
            if event.type in _FINAL_EVENTS:
                final = event.response
        if final is None:
            raise RunFailed("the response stream ended without a response")
        return final

    def _count(self, response) -> None:
        calls = sum(1 for item in response.output if item.type == "function_call")
        usage = usage_of(response.usage) if response.usage is not None else {}
        self.cost.add(calls, usage)

    def _answer(self, call) -> dict:
        """The `function_call_output` for one call. A mistake the model can correct
        comes back as `{"error": ...}` for it to read; RunFailed stops the run here,
        before another request."""
        try:
            output = self._call(call)
        except ModelError as e:
            output = json.dumps({"error": str(e)})
        return {
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": output,
        }

    def _call(self, call) -> str:
        if call.name not in self._bound:
            raise ModelError(f"no tool named {call.name!r}")
        tool, context = self._bound[call.name]
        try:
            arguments = json.loads(call.arguments)
        except json.JSONDecodeError as e:
            raise ModelError(for_model(f"arguments not JSON: {e}")) from e
        if not isinstance(arguments, dict):
            raise ModelError("the arguments are not a JSON object")
        return call_tool(tool, context, arguments)


def usage_of(usage) -> dict:
    """An OpenAI Responses `usage` in `run.usage`'s shape. OpenAI's `input_tokens` is
    the whole input; its cached and cache-written parts are split out of it, so
    `input_tokens` here is the rest, as Anthropic counts it (ADR-0023)."""
    details = usage.input_tokens_details
    cached = getattr(details, "cached_tokens", 0) or 0
    written = getattr(details, "cache_write_tokens", 0) or 0
    return {
        "input_tokens": usage.input_tokens - cached - written,
        "output_tokens": usage.output_tokens,
        "cache_read_input_tokens": cached,
        "cache_creation_input_tokens": written,
    }


def _refusal(response) -> str | None:
    """The text of a refusal in the response's output, or None. OpenAI gives no
    category, so the text is the reason (ADR-0020)."""
    for item in response.output:
        if item.type != "message":
            continue
        for part in item.content:
            if part.type == "refusal":
                text = " ".join(part.refusal.split()) or "no reason given"
                return text[:MAX_REFUSAL_CHARS]
    return None


def _incomplete(reason: str | None) -> Ending:
    if reason == "max_output_tokens":
        return cut_off("max_output_tokens")
    return Ending(
        unanswered=f"the response ended incomplete ({reason or 'no reason given'})"
    )
