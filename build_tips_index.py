import asyncio

import httpx
from sqlalchemy import delete

from database import SessionLocal
from models import TipChunk
from services.embeddings import embed_texts
from services.wikivoyage import fetch_guide, split_sections, make_chunks

CITIES = ["Puri", "Bhubaneswar", "Konark", "Goa", "Jaipur", "Varanasi"]


async def main():
    async with httpx.AsyncClient(timeout=15) as client:
        for city in CITIES:
            guide = await fetch_guide(client, city)
            if guide is None:
                print(city, "-> no guide found")
                continue
            chunks = make_chunks(guide["title"], split_sections(guide["text"]))
            if not chunks:
                print(guide["title"], "-> no chunks")
                continue
            vectors = []
            for i in range(0, len(chunks), 32):
                vectors += await embed_texts([c["text"] for c in chunks[i:i + 32]])
            with SessionLocal() as db:
                db.execute(delete(TipChunk).where(TipChunk.city == guide["title"]))
                for chunk, vector in zip(chunks, vectors):
                    db.add(TipChunk(**chunk, embedding=vector))
                db.commit()
            print(guide["title"], "->", len(chunks), "chunks saved")
            await asyncio.sleep(1)


asyncio.run(main())