"""Tests for topics (science pages) in sitelib.py."""
from pathlib import Path

import pytest
from PIL import Image

from sitelib import filter_consented, gallery_ref, validate
from tests.test_places import place, with_places
from tests.test_sitelib import minimal_content


# ------------------------------------------------------------ helpers
# Also used by tests/test_build.py and tests/test_images.py.

def topic(slug: str = "microbiology", reviewed: bool = False, photo: bool = True) -> dict:
    """A valid topic with two chapters; the first has a photo if `photo`."""
    chapters = [
        {"heading": "First chapter", "paragraphs": ["Para one.", "Para two."]},
        {"heading": "Second chapter", "paragraphs": ["Para three."]},
    ]
    if photo:
        chapters[0]["photo"] = {
            "source": f"photos/science/{slug}_sample.JPG",
            "author": "Cristian Monticone",
            "caption": "Sampling a pool.",
            "alt": "Sampling a pool",
        }
    return {
        "slug": slug,
        "kicker": "Research",
        "title": f"{slug.capitalize()} title",
        "teaser": "One sentence.",
        "intro": ["Intro paragraph."],
        "chapters": chapters,
        "references": [{"text": "Doe 2020. A paper."}],
        "reviewers": "Somebody",
        "reviewed": reviewed,
    }


def make_topic_images(static_dir: Path, topics: list[dict]) -> None:
    """Write the derived gallery images (two widths) for every chapter photo."""
    for t in topics:
        for ch in t["chapters"]:
            ph = ch.get("photo")
            if not ph:
                continue
            ref = gallery_ref(t["slug"], ph["source"])
            for w in (400, 800):
                path = static_dir / f"{ref}-{w}.webp"
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (w, w * 3 // 4)).save(path)


def with_topics(static_dir: Path, *topics: dict) -> dict:
    c = minimal_content()
    c["topics"] = list(topics)
    make_topic_images(static_dir, c["topics"])
    return c


# ------------------------------------------------------------ validation

def test_topics_valid(static_dir):
    c = with_topics(static_dir, topic("microbiology", True), topic("analogues", False))
    assert validate(c, static_dir) == []


def test_todo_allowed_in_unreviewed_topic(static_dir):
    t = topic(reviewed=False)
    t["intro"] = ["TODO ask Paolo"]
    assert validate(with_topics(static_dir, t), static_dir) == []


def test_todo_blocks_reviewed_topic(static_dir):
    t = topic(reviewed=True)
    t["intro"] = ["TODO ask Paolo"]
    errors = validate(with_topics(static_dir, t), static_dir)
    assert any("topics[0].intro[0]: contains TODO" in e for e in errors)


def test_forbidden_phrase_checked_in_drafts(static_dir):
    t = topic(reviewed=False)
    t["intro"] = ["Life as extremophile."]
    errors = validate(with_topics(static_dir, t), static_dir)
    assert any("forbidden phrase" in e for e in errors)


def test_topic_slug_clashes_with_place(static_dir):
    c = with_places(static_dir, place("torfa"))
    c["topics"] = [topic("torfa")]
    make_topic_images(static_dir, c["topics"])
    errors = validate(c, static_dir)
    assert any("topics[0].slug: same as a place: torfa" in e for e in errors)


def test_topic_slug_rules(static_dir):
    errors = validate(with_topics(static_dir, topic("Micro Bio", photo=False)), static_dir)
    assert any("lowercase letters" in e for e in errors)
    errors = validate(with_topics(static_dir, topic("static", photo=False)), static_dir)
    assert any("reserved name" in e for e in errors)
    errors = validate(with_topics(static_dir, topic("a", photo=False), topic("a", photo=False)), static_dir)
    assert any("used twice" in e for e in errors)


def test_topic_photo_needs_author(static_dir):
    t = topic()
    del t["chapters"][0]["photo"]["author"]
    errors = validate(with_topics(static_dir, t), static_dir)
    assert "topics[0].chapters[0].photo.author: missing" in errors


def test_topic_photo_image_missing(static_dir):
    t = topic()
    c = with_topics(static_dir, t)
    for f in (static_dir / "img/places/microbiology").glob("*"):
        f.unlink()
    errors = validate(c, static_dir)
    assert any("topics[0].chapters[0].photo: image not found" in e for e in errors)


def test_unreviewed_topic_images_not_unused(static_dir):
    c = with_topics(static_dir, topic(reviewed=False))
    assert not any("not used by any photo" in e for e in validate(c, static_dir))


# ------------------------------------------------------------ consent filter

@pytest.mark.parametrize("flag", [False, "true", 1, None])
def test_filter_drops_unreviewed_topics(flag):
    t = topic()
    if flag is None:
        del t["reviewed"]
    else:
        t["reviewed"] = flag
    c = minimal_content()
    c["topics"] = [t]
    out, skipped = filter_consented(c)
    assert out["topics"] == []
    assert "topic:microbiology" in skipped


def test_filter_keeps_reviewed_topic():
    c = minimal_content()
    c["topics"] = [topic(reviewed=True)]
    out, skipped = filter_consented(c)
    assert [t["slug"] for t in out["topics"]] == ["microbiology"]
    assert "topic:microbiology" not in skipped


def test_filter_strips_links_to_hidden_topics():
    c = minimal_content()
    c["topics"] = [topic("microbiology", True), topic("analogues", False)]
    c["science_why"] = {"kicker": "k", "title": "t", "items": [
        {"title": "A", "text": "a", "topic": "analogues"},
        {"title": "B", "text": "b", "topic": "typo"},
        {"title": "C", "text": "c", "topic": "microbiology"},
    ]}
    out, _ = filter_consented(c)
    items = out["science_why"]["items"]
    assert "topic" not in items[0] and "topic" not in items[1]
    assert items[2]["topic"] == "microbiology"
