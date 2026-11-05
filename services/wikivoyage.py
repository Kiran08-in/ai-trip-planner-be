import re
import httpx
from urllib.parse import quote
from services.wiki_pedia import HEADERS

VOYAGE_URL = "https://en.wikivoyage.org/w/api.php"
KEEP = {"intro", "understand", "stay safe", "respect"}


async def fetch_guide(client, title):
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "exsectionformat": "wiki",
        "redirects": 1,
        "titles": title,
        "format": "json",
    }
    response = await client.get(VOYAGE_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        if page.get("extract"):
            return {"title": page["title"], "text": page["extract"]}
    return None


def split_sections(text):
    sections = {}
    current = "intro"
    for line in text.splitlines():
        match = re.match(r"^==\s*([^=].*?)\s*==$", line)
        if match:
            current = match.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}

def chunk_text(text, max_chars=800):
    chunks = []
    current = ""
    for paragraph in text.split("\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        while len(paragraph) > max_chars:
            cut = paragraph.rfind(" ", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            if current:
                chunks.append(current)
                current = ""
            chunks.append(paragraph[:cut])
            paragraph = paragraph[cut:].strip()
        if current and len(current) + len(paragraph) + 1 > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = f"{current}\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks


def make_chunks(title, sections):
    url = "https://en.wikivoyage.org/wiki/" + quote(title.replace(" ", "_"))
    chunks = []
    for name, text in sections.items():
        if name not in KEEP:
            continue
        for part in chunk_text(text):
            if len(part) < 40:
                continue
            chunks.append({"city": title, "section": name, "text": part, "url": url})
    return chunks