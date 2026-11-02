import json
from pathlib import Path

import httpx
import pytest

from reviewer.cost import estimate_cost
from reviewer.llm import LLMError, OpenAICompatibleProvider, Usage, make_provider
from reviewer.schema import Review

FIXTURE = json.loads((Path(__file__).parent / "fixtures/llm/chat_ok.json").read_text())
VALID = FIXTURE["choices"][0]["message"]["content"]


def reply(content: str, prompt=10, completion=5) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": content}}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion},
    }


class Server:
    """Scripted fake API: each item is a dict (200 JSON) or an httpx.Response."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(
            {
                "url": str(request.url),
                "auth": request.headers.get("authorization"),
                "body": json.loads(request.content),
            }
        )
        item = self.responses.pop(0)
        return item if isinstance(item, httpx.Response) else httpx.Response(200, json=item)


def make(server: Server, **kw) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="https://api.example.com/v1/",
        api_key="k",
        model="test-model",
        client=httpx.Client(transport=httpx.MockTransport(server)),
        sleep=kw.pop("sleep", lambda s: None),
        **kw,
    )


def test_valid_response_returns_schema_instance():  # AC1
    server = Server(FIXTURE)
    review = make(server).complete_json("sys", "user", Review)
    assert isinstance(review, Review) and review.findings[0].title == "Off by one"
    req = server.requests[0]
    assert req["url"] == "https://api.example.com/v1/chat/completions"
    assert req["auth"] == "Bearer k"
    assert req["body"]["model"] == "test-model"
    assert req["body"]["response_format"]["type"] == "json_schema"
    assert "findings" in req["body"]["messages"][0]["content"]  # schema in system prompt


def test_invalid_json_retries_once_with_error_then_succeeds():  # AC2
    server = Server(reply("not json"), reply(VALID))
    review = make(server).complete_json("sys", "user", Review)
    assert review.summary == "one issue"
    retry_messages = server.requests[1]["body"]["messages"]
    assert retry_messages[-2] == {"role": "assistant", "content": "not json"}
    assert "validation" in retry_messages[-1]["content"].lower()


def test_second_invalid_response_raises_llm_error():  # AC2
    server = Server(reply("nope"), reply('{"findings": []}'))
    with pytest.raises(LLMError):
        make(server).complete_json("sys", "user", Review)
    assert len(server.requests) == 2


def test_fenced_json_is_accepted():  # AC2
    server = Server(reply(f"```json\n{VALID}\n```"))
    assert make(server).complete_json("s", "u", Review).summary == "one issue"


def test_429_waits_retry_after_and_retries_once():  # AC3
    waits: list[float] = []
    server = Server(httpx.Response(429, headers={"retry-after": "7"}), FIXTURE)
    make(server, sleep=waits.append).complete_json("s", "u", Review)
    assert waits == [7.0]


def test_429_twice_raises_and_wait_is_capped():  # AC3
    waits: list[float] = []
    server = Server(
        httpx.Response(429, headers={"retry-after": "999"}), httpx.Response(429, text="slow down")
    )
    with pytest.raises(LLMError):
        make(server, sleep=waits.append).complete_json("s", "u", Review)
    assert waits == [60.0]


def test_other_http_errors_and_network_errors_raise():  # AC3
    with pytest.raises(LLMError):
        make(Server(httpx.Response(500, text="boom"))).complete_json("s", "u", Review)

    def broken(request):
        raise httpx.ConnectError("down")

    provider = OpenAICompatibleProvider(
        "https://x/v1", "k", "m", client=httpx.Client(transport=httpx.MockTransport(broken))
    )
    with pytest.raises(LLMError):
        provider.complete_json("s", "u", Review)


def test_400_falls_back_to_json_object_and_sticks():  # AC4
    server = Server(httpx.Response(400, text="json_schema unsupported"), FIXTURE, FIXTURE)
    provider = make(server)
    provider.complete_json("s", "u", Review)
    provider.complete_json("s", "u", Review)
    formats = [r["body"]["response_format"]["type"] for r in server.requests]
    assert formats == ["json_schema", "json_object", "json_object"]


def test_usage_is_summed_across_calls_and_retries():  # AC5
    provider = make(Server(reply("bad", 10, 1), reply(VALID, 20, 2)))
    provider.complete_json("s", "u", Review)
    assert provider.usage == Usage(prompt_tokens=30, completion_tokens=3, calls=2)


def test_min_interval_spaces_consecutive_calls():  # AC5
    waits: list[float] = []
    now = [100.0]
    provider = make(
        Server(FIXTURE, FIXTURE), min_interval=2.0, sleep=waits.append, clock=lambda: now[0]
    )
    provider.complete_json("s", "u", Review)
    now[0] = 100.5
    provider.complete_json("s", "u", Review)
    assert waits == [pytest.approx(1.5)]


def test_factory_presets_and_errors():  # AC6
    gemini = make_provider("gemini", "m", "key")
    assert gemini.base_url == "https://generativelanguage.googleapis.com/v1beta/openai"
    assert make_provider("groq", "m", "key").base_url == "https://api.groq.com/openai/v1"
    custom = make_provider("openai-compatible", "m", "key", base_url="https://h/v1")
    assert custom.base_url == "https://h/v1"
    for bad in (("nope", "m", "key"), ("gemini", "m", ""), ("openai-compatible", "m", "key")):
        with pytest.raises(ValueError):
            make_provider(*bad)


def test_estimate_cost():  # AC7
    usage = Usage(prompt_tokens=1_000_000, completion_tokens=500_000, calls=1)
    prices = {"m": {"input": 2.0, "output": 4.0}}
    assert estimate_cost("m", usage, prices) == pytest.approx(4.0)
    assert estimate_cost("other", usage, prices) is None


def test_request_seconds_counts_only_http_time_not_throttle_waits():  # AC8
    ticks = iter(range(0, 1000))  # every clock() read advances by 1 s
    waits: list[float] = []
    provider = make(
        Server(FIXTURE, FIXTURE), min_interval=100.0, sleep=waits.append, clock=lambda: next(ticks)
    )
    provider.complete_json("s", "u", Review)
    provider.complete_json("s", "u", Review)
    assert waits  # the second call was throttled...
    assert provider.request_seconds == pytest.approx(2.0)  # ...but only 1 s per HTTP call counts
