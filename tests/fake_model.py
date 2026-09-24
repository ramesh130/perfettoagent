"""A scripted stand-in for the Messages API, for tests with no network.

The client is a real `anthropic.Anthropic` whose HTTP transport is an in-process
`MockTransport`: no socket is opened, and the SDK's own Tool Runner, streaming parser
and tool dispatch run exactly as they would against the API. Each request goes to
`script(request, turn)`, which returns the assistant message to stream back as
server-sent events. `requests` keeps every request body, for tests that check what
the model was sent.

ref: https://platform.claude.com/docs/en/build-with-claude/streaming#event-types
"""

import json
from collections.abc import Callable

import anthropic
import httpx2

# Usage reported on every scripted response unless the script gives its own.
USAGE = {
    "input_tokens": 1000,
    "output_tokens": 200,
    "cache_read_input_tokens": 3000,
    "cache_creation_input_tokens": 0,
}


def text(value) -> dict:
    """A text block; a dict or list is written as JSON, as structured output is."""
    return {
        "type": "text",
        "text": value if isinstance(value, str) else json.dumps(value),
    }


def tool_use(name: str, arguments: dict, id: str | None = None) -> dict:
    return {
        "type": "tool_use",
        "id": id or f"toolu_{name}",
        "name": name,
        "input": arguments,
    }


def reply(*content: dict, stop_reason: str = "end_turn", **extra) -> dict:
    """One scripted assistant message. `extra` may set `stop_details` or `usage`."""
    return {"content": list(content), "stop_reason": stop_reason, **extra}


class FakeModel:
    def __init__(self, script: Callable[[dict, int], dict]):
        self.script = script
        self.requests: list[dict] = []
        self.client = anthropic.Anthropic(
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
            content=_events(message, body["model"]).encode(),
        )

    def tool_results(self, turn: int) -> dict[str, dict]:
        """The tool results the `turn`th request (1-based) carried, by tool_use id:
        {id: {"content": ..., "is_error": bool}}. Content is parsed as JSON where
        it is JSON."""
        last = self.requests[turn - 1]["messages"][-1]
        results = {}
        for block in last["content"]:
            if block.get("type") == "tool_result":
                content = block["content"]
                if isinstance(content, list):
                    content = "".join(c.get("text", "") for c in content)
                try:
                    content = json.loads(content)
                except (TypeError, ValueError):
                    pass
                results[block["tool_use_id"]] = {
                    "content": content,
                    "is_error": bool(block.get("is_error")),
                }
        return results


def _events(message: dict, model: str) -> str:
    """The server-sent events that stream `message`."""
    usage = {**USAGE, **message.get("usage", {})}
    events = [
        (
            "message_start",
            {
                "type": "message_start",
                "message": {
                    "id": "msg_fake",
                    "type": "message",
                    "role": "assistant",
                    "model": model,
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {**usage, "output_tokens": 1},
                },
            },
        )
    ]
    for index, block in enumerate(message["content"]):
        if block["type"] == "text":
            start = {"type": "text", "text": ""}
            delta = {"type": "text_delta", "text": block["text"]}
        else:
            start = {**block, "input": {}}
            delta = {
                "type": "input_json_delta",
                "partial_json": json.dumps(block["input"]),
            }
        events += [
            (
                "content_block_start",
                {"type": "content_block_start", "index": index, "content_block": start},
            ),
            (
                "content_block_delta",
                {"type": "content_block_delta", "index": index, "delta": delta},
            ),
            ("content_block_stop", {"type": "content_block_stop", "index": index}),
        ]
    events += [
        (
            "message_delta",
            {
                "type": "message_delta",
                "delta": {
                    "stop_reason": message["stop_reason"],
                    "stop_sequence": None,
                    "stop_details": message.get("stop_details"),
                },
                "usage": usage,
            },
        ),
        ("message_stop", {"type": "message_stop"}),
    ]
    return "".join(
        f"event: {name}\ndata: {json.dumps(data)}\n\n" for name, data in events
    )
