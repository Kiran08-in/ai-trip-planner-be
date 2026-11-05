import os

import httpx
from dotenv import load_dotenv
from ollama import AsyncClient, ResponseError

load_dotenv()

EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
embed_client = AsyncClient(
    host=os.getenv("OLLAMA_EMBED_HOST", "http://localhost:11434"),
    timeout=60,
)


class EmbeddingUnavailable(Exception):
    pass


async def embed_texts(texts):
    try:
        response = await embed_client.embed(model=EMBED_MODEL, input=texts)
    except (ResponseError, httpx.HTTPError, ConnectionError, OSError):
        raise EmbeddingUnavailable("The local embedding model is not available.")
    return response.embeddings