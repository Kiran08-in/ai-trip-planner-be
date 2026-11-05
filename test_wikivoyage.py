from services.wikivoyage import split_sections, chunk_text, make_chunks

TEXT = (
    "Puri is a city.\n\n"
    "== Understand ==\nHot summers.\n=== Climate ===\nMarch to June is hot.\n\n"
    "== Get in ==\nBy train."
)


def test_split_sections_keeps_subheadings_inside_parent():
    s = split_sections(TEXT)
    assert s["intro"] == "Puri is a city."
    assert "Hot summers." in s["understand"]
    assert "March to June is hot." in s["understand"]
    assert s["get in"] == "By train."


def test_text_without_headings_is_all_intro():
    assert split_sections("Just one line.") == {"intro": "Just one line."}

def test_chunk_text_merges_short_lines_and_respects_max():
    text = "\n".join(["a" * 300] * 5)
    chunks = chunk_text(text, max_chars=700)
    assert all(len(c) <= 700 for c in chunks)
    assert len(chunks) == 3


def test_chunk_text_cuts_a_very_long_line_at_a_space():
    text = "word " * 400
    chunks = chunk_text(text, max_chars=500)
    assert all(len(c) <= 500 for c in chunks)
    assert "".join(c.replace(" ", "") for c in chunks) == "word" * 400


def test_make_chunks_keeps_wanted_sections_and_adds_credit_url():
    sections = {"intro": "x" * 100, "get in": "y" * 100, "eat": "tiny"}
    chunks = make_chunks("Puri", sections)
    assert [c["section"] for c in chunks] == ["intro"]
    assert chunks[0]["url"] == "https://en.wikivoyage.org/wiki/Puri"
    assert chunks[0]["city"] == "Puri"