"""Tests for review_copy.py (reviewer copies of science pages)."""
from review_copy import topic_markdown
from tests.test_topics import topic


def test_topic_markdown():
    t = topic()
    t["references"] = [
        {"text": "Doe 2020. A paper.", "url": "https://example.org/a"},
        {"text": "Roe 2021. Another."},
    ]
    t["reviewers"] = "Somebody"
    md = topic_markdown(t)
    assert md.startswith("# Microbiology title\n")
    assert "Reviewers: Somebody · Status: draft (not on the site)" in md
    assert "## First chapter" in md and "## Second chapter" in md
    assert "Para one.\n\nPara two." in md
    assert "[Photo: Sampling a pool. © Cristian Monticone]" in md
    assert md.rstrip().endswith("1. Doe 2020. A paper. https://example.org/a\n2. Roe 2021. Another.")
    assert "## References" in md
    t["reviewed"] = True
    assert "Status: published" in topic_markdown(t)
