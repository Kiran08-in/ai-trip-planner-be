import os

import httpx
from dotenv import load_dotenv
from ollama import AsyncClient, ResponseError

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
client = AsyncClient(host=os.getenv("OLLAMA_HOST"), timeout=60)


class AIUnavailable(Exception):
    pass


async def ask_ai(messages):
    try:
        response = await client.chat(model=MODEL, messages=messages)
    except ResponseError as e:
        if e.status_code == 429:
            raise AIUnavailable("The AI is busy or the free limit is reached. Try again later.")
        if e.status_code in (401, 403):
            raise AIUnavailable("The AI key is not accepted.")
        raise AIUnavailable("The AI gave an error. Try again later.")
    except (httpx.HTTPError, ConnectionError, OSError):
        raise AIUnavailable("Cannot reach the AI. Check the network and try again.")
    return response.message.content