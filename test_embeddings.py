import asyncio

import pytest

from services import embeddings


def test_embed_texts_returns_vectors(monkeypatch):
    class Fake:
        embeddings = [[0.1, 0.2], [0.3, 0.4]]

    async def fake_embed(model, input):
        return Fake()

    monkeypatch.setattr(embeddings.embed_client, "embed", fake_embed)
    assert asyncio.run(embeddings.embed_texts(["a", "b"])) == [[0.1, 0.2], [0.3, 0.4]]


def test_embed_texts_unavailable_is_our_error(monkeypatch):
    async def boom(model, input):
        raise ConnectionError("down")

    monkeypatch.setattr(embeddings.embed_client, "embed", boom)
    with pytest.raises(embeddings.EmbeddingUnavailable):
        asyncio.run(embeddings.embed_texts(["a"]))