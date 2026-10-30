import json

from services.ai import chat_message
from services.tools import TOOLS, run_tool

MAX_ROUNDS = 5
MAX_CALLS_PER_ROUND = 3

SYSTEM_PROMPT = (
    "You are TripBanao's travel assistant for Indian cities. "
    "Use the tools to get real weather and real places. Never invent them. "
    "If a tool returns an error, tell the user simply. Keep answers short."
)


async def chat(user_messages):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + user_messages
    tools_used = []

    for _ in range(MAX_ROUNDS):
        reply = await chat_message(messages, tools=TOOLS)
        messages.append(reply)

        if not reply.tool_calls:
            return {"answer": reply.content, "tools_used": tools_used}

        for call in reply.tool_calls[:MAX_CALLS_PER_ROUND]:
            name = call.function.name
            print("tool call:", name, call.function.arguments)
            result = await run_tool(name, call.function.arguments)
            tools_used.append(name)
            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(result, default=str),
            })

    return {
        "answer": "I could not finish this in a few steps. Please ask a simpler question.",
        "tools_used": tools_used,
    }