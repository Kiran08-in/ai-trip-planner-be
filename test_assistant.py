import asyncio
from types import SimpleNamespace

from services import assistant

USER = [{"role": "user", "content": "hi"}]


def call(name, args):
    return SimpleNamespace(function=SimpleNamespace(name=name, arguments=args))


def reply(content="", calls=None):
    return SimpleNamespace(content=content, tool_calls=calls or [])


def fake_ai(monkeypatch, replies):
    seen = []

    async def fake_chat(messages, tools=None):
        seen.append(list(messages))
        return replies[len(seen) - 1]

    async def fake_run_tool(name, arguments):
        return {"ok": name}

    monkeypatch.setattr(assistant, "chat_message", fake_chat)
    monkeypatch.setattr(assistant, "run_tool", fake_run_tool)
    return seen


def test_plain_answer_uses_no_tools(monkeypatch):
    fake_ai(monkeypatch, [reply("Hello!")])
    result = asyncio.run(assistant.chat(USER))
    assert result == {"answer": "Hello!", "tools_used": []}


def test_tool_then_answer(monkeypatch):
    seen = fake_ai(monkeypatch, [
        reply(calls=[call("get_weather", {"city": "Goa", "days": 2})]),
        reply("Take an umbrella."),
    ])
    result = asyncio.run(assistant.chat(USER))
    assert result["answer"] == "Take an umbrella."
    assert result["tools_used"] == ["get_weather"]
    last_message = seen[1][-1]
    assert last_message["role"] == "tool"
    assert last_message["tool_name"] == "get_weather"


def test_endless_tool_requests_stop(monkeypatch):
    seen = fake_ai(monkeypatch, [reply(calls=[call("get_weather", {})])] * 10)
    result = asyncio.run(assistant.chat(USER))
    assert len(seen) == assistant.MAX_ROUNDS
    assert "could not finish" in result["answer"]


def test_too_many_calls_in_one_round(monkeypatch):
    calls = [call("find_places", {})] * 6
    fake_ai(monkeypatch, [reply(calls=calls), reply("done")])
    result = asyncio.run(assistant.chat(USER))
    assert len(result["tools_used"]) == assistant.MAX_CALLS_PER_ROUND