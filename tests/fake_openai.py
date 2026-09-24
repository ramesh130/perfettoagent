"""A scripted stand-in for OpenAI's Responses API, for tests with no network.

The client is a real `openai.OpenAI` whose HTTP transport is an in-process
`MockTransport`: no socket is opened, and the SDK's own streaming parser and response
types run as they would against the API. It plays the same scripts as
`fake_model.FakeModel` (`reply`, `text`, `tool_use`), rendered as the Responses API
would answer:

- a `tool_use` block is a `function_call` item, its id the `call_id`;
- a text block is a `message` item with one `output_text` part;
- `stop_reason="refusal"` is a `message` item with a `refusal` part, whose text is
  `stop_details["explanation"]`;
- `stop_reason="max_tokens"` is a response `incomplete` at `max_output_tokens`, and
  `reply(..., incomplete="<reason>")` one incomplete for another reason;
- `reply(..., failed={"code": ..., "message": ...})` is a response that `failed`;
- a `tool_use` whose input is a string sends that string as the arguments, as is;
- usage is converted: OpenAI's `input_tokens` is the whole input, cached and
  cache-written tokens included.

Every response starts with a reasoning item, as a reasoning model's do, so a test sees
it replayed. `requests` keeps every request body.

ref: https://developers.openai.com/api/docs/guides/streaming-responses
"""

import json
from collections.abc import Callable

import httpx2
import openai
from fake_model import USAGE

# What the fake puts in each reasoning item, as the API's opaque replay blob.
ENCRYPTED = "opaque-reasoning-state"


class FakeOpenAI:
    def __init__(self, script: Callable[[dict, int], dict]):
        self.script = script
        self.requests: list[dict] = []
        self.client = openai.OpenAI(
            api_key="test-key-not-a-secret",
            max_retries=0,
            http_client=httpx2.Client(transport=httpx2.MockTransport(self._handle)),
        )

    def _handle(self, request: httpx2.Request) -> httpx2.Response:
        body = json.loads(request.content)
        self.requests.append(body)
        message = self.script(body, len(self.requests))
        return httpx2.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_events(message, body["model"], len(self.requests)).encode(),
        )

    def first_message(self) -> str:
        """The first request's user message."""
        [user] = [i for i in self.requests[0]["input"] if i.get("role") == "user"]
        return user["content"]

    def tool_results(self, turn: int) -> dict[str, dict]:
        """The tool outputs the `turn`th request (1-based) carried, by call id:
        {id: {"content": ..., "is_error": bool}}, as `FakeModel.tool_results` gives
        them. An output of the form {"error": message} is an error, its content the
        message."""
        results = {}
        for item in reversed(self.requests[turn - 1]["input"]):
            if item.get("type") != "function_call_output":
                break
            content = json.loads(item["output"])
            is_error = isinstance(content, dict) and set(content) == {"error"}
            results[item["call_id"]] = {
                "content": content["error"] if is_error else content,
                "is_error": is_error,
            }
        return results


def _events(message: dict, model: str, turn: int) -> str:
    """The server-sent events that stream `message` as a Responses API response."""
    stop = message["stop_reason"]
    output = [
        {
            "type": "reasoning",
            "id": f"rs_{turn}",
            "summary": [],
            "encrypted_content": ENCRYPTED,
        }
    ]
    for index, block in enumerate(message["content"]):
        if block["type"] == "text":
            output.append(_message(f"msg_{turn}_{index}", _output_text(block["text"])))
        else:
            output.append(
                {
                    "type": "function_call",
                    "id": f"fc_{block['id']}",
                    "call_id": block["id"],
                    "name": block["name"],
                    "arguments": (
                        block["input"]
                        if isinstance(block["input"], str)
                        else json.dumps(block["input"])
                    ),
                    "status": "completed",
                }
            )
    if stop == "refusal":
        explanation = (message.get("stop_details") or {}).get("explanation", "")
        output.append(
            _message(f"msg_{turn}_r", {"type": "refusal", "refusal": explanation})
        )
    reason = "max_output_tokens" if stop == "max_tokens" else message.get("incomplete")
    status = "incomplete" if reason else "completed"
    if message.get("failed"):
        status = "failed"
    response = {
        "id": f"resp_{turn}",
        "object": "response",
        "created_at": 0,
        "model": model,
        "status": status,
        "incomplete_details": {"reason": reason} if reason else None,
        "error": message.get("failed"),
        "output": output,
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "usage": _usage({**USAGE, **message.get("usage", {})}),
    }
    events = [
        ("response.created", {"response": {**response, "status": "in_progress"}}),
        (f"response.{status}", {"response": response}),
    ]
    return "".join(
        f"event: {name}\ndata: "
        f"{json.dumps({'type': name, 'sequence_number': n, **data})}\n\n"
        for n, (name, data) in enumerate(events)
    )


def _message(id: str, part: dict) -> dict:
    return {
        "type": "message",
        "id": id,
        "role": "assistant",
        "status": "completed",
        "content": [part],
    }


def _output_text(text: str) -> dict:
    return {"type": "output_text", "text": text, "annotations": []}


def _usage(usage: dict) -> dict:
    cached = usage["cache_read_input_tokens"]
    written = usage["cache_creation_input_tokens"]
    return {
        "input_tokens": usage["input_tokens"] + cached + written,
        "input_tokens_details": {
            "cached_tokens": cached,
            "cache_write_tokens": written,
        },
        "output_tokens": usage["output_tokens"],
        "output_tokens_details": {"reasoning_tokens": 0},
        "total_tokens": usage["input_tokens"]
        + cached
        + written
        + usage["output_tokens"],
    }
