"""Tests for places (galleries) and the In the field section in sitelib.py."""
from pathlib import Path

import pytest
from PIL import Image

from sitelib import gallery_ref, slugify, validate
from tests.test_sitelib import minimal_content


# ------------------------------------------------------------ helpers
# Also used by tests/test_build.py.

def place(slug: str = "torfa", n: int = 4) -> dict:
    """A valid place: photo 0 is the cover, photos 1-3 are featured."""
    photos = []
    for i in range(n):
        p = {
            "source": f"photos/{slug}/P{i}.JPG",
            "author": "Andrea Benassi",
            "caption": f"Photo {i}, July 2026.",
            "alt": f"Cave photo {i}",
        }
        if i == 0:
            p["cover"] = True
        elif i <= 3:
            p["featured"] = True
        photos.append(p)
    return {
        "slug": slug,
        "name": slug.capitalize() + " place",
        "years": "2026–2027",
        "teaser": "One sentence.",
        "intro": ["First paragraph."],
        "photos": photos,
    }


def make_place_images(static_dir: Path, places: list[dict]) -> None:
    """Write the derived gallery images (two widths) for every photo."""
    for pl in places:
        for ph in pl["photos"]:
            ref = gallery_ref(pl["slug"], ph["source"])
            for w in (400, 800):
                path = static_dir / f"{ref}-{w}.webp"
                path.parent.mkdir(parents=True, exist_ok=True)
                Image.new("RGB", (w, w * 3 // 4)).save(path)


def with_places(static_dir: Path, *places: dict) -> dict:
    c = minimal_content()
    c["headings"]["places"] = {"kicker": "Places", "title": "Where we work"}
    c["places"] = list(places)
    make_place_images(static_dir, c["places"])
    return c


# ------------------------------------------------------------ names

def test_slugify():
    assert slugify("Copia di Vatnajökull 2026 - Paolo Testa (113)") == "copia-di-vatnajokull-2026-paolo-testa-113"
    assert slugify("P7110912") == "p7110912"
    assert slugify("20260711_143730") == "20260711-143730"
    assert slugify("Scialò") == "scialo"


def test_gallery_ref():
    assert gallery_ref("torfa", "photos/torfa/RIMG0247.JPG") == "img/places/torfa/rimg0247"


# ------------------------------------------------------------ validation

def test_places_valid(static_dir):
    assert validate(with_places(static_dir, place(), place("kverkfjoll")), static_dir) == []


def test_places_and_field_optional(static_dir):
    c = minimal_content()
    assert "places" not in c and "field" not in c
    assert validate(c, static_dir) == []


@pytest.mark.parametrize("key", ["slug", "name", "years", "teaser", "intro", "photos"])
def test_place_missing_keys(static_dir, key):
    c = with_places(static_dir, place())
    del c["places"][0][key]
    assert f"places[0].{key}: missing" in validate(c, static_dir)


@pytest.mark.parametrize("key", ["source", "author", "caption", "alt"])
def test_photo_missing_keys(static_dir, key):
    c = with_places(static_dir, place())
    del c["places"][0]["photos"][1][key]
    assert f"places[0].photos[1].{key}: missing" in validate(c, static_dir)


def test_place_empty_photos(static_dir):
    c = with_places(static_dir, place())
    c["places"][0]["photos"] = []
    assert "places[0].photos: missing" in validate(c, static_dir)


@pytest.mark.parametrize("bad", ["Torfa", "static", "tor fa", "torfa"])
def test_bad_or_duplicate_slug(static_dir, bad):
    second = place("kverkfjoll")
    c = with_places(static_dir, place(), second)
    c["places"][1]["slug"] = bad
    errors = validate(c, static_dir)
    assert any(e.startswith("places[1].slug:") for e in errors), errors


def test_duplicate_stem(static_dir):
    pl = place()
    pl["photos"][4 - 1]["source"] = "a/X 1.JPG"
    pl["photos"].append({"source": "b/x-1.jpg", "author": "A", "caption": "C", "alt": "A"})
    c = with_places(static_dir, pl)
    errors = validate(c, static_dir)
    assert any("places[0].photos[4]" in e and "same image name" in e for e in errors), errors


@pytest.mark.parametrize("change", ["no_cover", "two_covers", "two_featured", "four_featured", "both"])
def test_cover_featured_counts(static_dir, change):
    pl = place(n=5)
    ph = pl["photos"]
    if change == "no_cover":
        del ph[0]["cover"]
    elif change == "two_covers":
        ph[4]["cover"] = True
    elif change == "two_featured":
        del ph[3]["featured"]
    elif change == "four_featured":
        ph[4]["featured"] = True
    elif change == "both":
        ph[1]["cover"] = True
        del ph[0]["cover"]
    c = with_places(static_dir, pl)
    errors = validate(c, static_dir)
    assert any(e.startswith("places[0]:") for e in errors), errors


def test_gallery_image_missing(static_dir):
    c = with_places(static_dir, place())
    ref = gallery_ref("torfa", c["places"][0]["photos"][2]["source"])
    for f in (static_dir / ref).parent.glob(Path(ref).name + "-*.webp"):
        f.unlink()
    errors = validate(c, static_dir)
    assert any(
        e.startswith("places[0].photos[2]: image not found") and "uv run prepare_images.py" in e
        for e in errors
    ), errors


def test_places_need_heading(static_dir):
    c = with_places(static_dir, place())
    del c["headings"]["places"]
    assert "headings.places: missing" in validate(c, static_dir)


def test_field_valid(static_dir):
    c = minimal_content()
    c["headings"]["field"] = {"kicker": "In the field", "title": "What the ice demands"}
    c["field"] = [{"title": "Rivers", "text": "Wet.", "image": "img/a", "image_alt": "River", "credit": "Paolo Testa"}]
    assert validate(c, static_dir) == []


def test_field_item_rules(static_dir):
    c = minimal_content()
    c["headings"]["field"] = {"kicker": "In the field", "title": "What the ice demands"}
    c["field"] = [{"title": "Rivers", "text": "Wet.", "image": "img/a", "credit": "Paolo Testa"}]
    assert "field[0].image_alt: missing" in validate(c, static_dir)


def test_field_needs_heading(static_dir):
    c = minimal_content()
    c["field"] = [{"title": "Rivers", "text": "Wet.", "image": "img/a", "image_alt": "R", "credit": "P"}]
    assert "headings.field: missing" in validate(c, static_dir)


def test_todo_in_caption(static_dir):
    c = with_places(static_dir, place())
    c["places"][0]["photos"][0]["caption"] = "TODO"
    assert "places[0].photos[0].caption: contains TODO" in validate(c, static_dir)


# ------------------------------------------------------------ review fixes

def test_slugify_icelandic_letters():
    assert slugify("Þórsmörk") == "thorsmork"
    assert slugify("ðæ") == "dae"
    assert slugify("IMG 01 ß") == "img-01-ss"
    assert slugify("Øræfi") == "oraefi"


def test_empty_image_name_rejected(static_dir):
    c = with_places(static_dir, place())
    c["places"][0]["photos"][1]["source"] = "photos/torfa/---.JPG"
    errors = validate(c, static_dir)
    assert any(e.startswith("places[0].photos[1].source:") and "empty" in e for e in errors), errors


def test_unused_gallery_file_rejected(static_dir):
    c = with_places(static_dir, place())
    stray = static_dir / "img" / "places" / "torfa" / "removed-800.webp"
    Image.new("RGB", (800, 600)).save(stray)
    gone = static_dir / "img" / "places" / "oldplace" / "x-800.webp"
    gone.parent.mkdir(parents=True)
    Image.new("RGB", (800, 600)).save(gone)
    errors = validate(c, static_dir)
    assert any("img/places/torfa/removed-800.webp" in e and "prepare_images.py" in e for e in errors), errors
    assert any("img/places/oldplace/x-800.webp" in e for e in errors), errors


def test_unused_gallery_files_checked_without_places(static_dir):
    stray = static_dir / "img" / "places" / "torfa" / "a-800.webp"
    stray.parent.mkdir(parents=True)
    Image.new("RGB", (800, 600)).save(stray)
    errors = validate(minimal_content(), static_dir)
    assert any("img/places/torfa/a-800.webp" in e for e in errors), errors
