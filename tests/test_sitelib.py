"""Tests for sitelib.py: validation, consent filter, italics, image info."""
import copy

import pytest

from sitelib import image_info, inline_md, filter_consented, validate


def minimal_content() -> dict:
    """A valid content dict using only the images from the `static_dir` fixture.

    Other tests (e.g. tests/test_build.py) import this and tweak it.
    """
    return {
        "site": {
            "title": "Fire Under Ice",
            "url": "https://fireunderice.org",
            "description": "A glaciological expedition.",
            "contact_email": "info@fireunderice.org",
        },
        "headings": {
            "years": {"kicker": "Years", "title": "Years title"},
            "watch": {"kicker": "Watch", "title": "Watch title"},
            "science": {"kicker": "Science", "title": "Science title"},
            "team": {"kicker": "Team", "title": "Team title"},
            "press": {"kicker": "Press", "title": "Press title"},
            "partners": {"kicker": "Partners", "title": "Partners title"},
            "contact": {"kicker": "Contact", "title": "Contact title"},
        },
        "hero": {
            "title": "Fire Under Ice",
            "subtitle": "Kverkfjöll, Iceland",
            "years": "2025-2027",
            "image": "img/a",
            "image_alt": "Ice cave entrance",
        },
        "project": {
            "kicker": "The project",
            "title": "What we do",
            "paragraphs": ["First paragraph.", "Second paragraph."],
        },
        "years": [
            {
                "year": 2025,
                "label": "Recon",
                "place": "Kverkfjöll",
                "text": "We went and looked.",
                "image": "img/a",
                "image_alt": "Team on the glacier",
            }
        ],
        "comparison": {
            "caption": "Same place, nineteen years apart.",
            "backgrounds": [
                {
                    "label": "Satellite 2024",
                    "before": "img/a",
                    "before_alt": "The glacier in 2006",
                    "after": "img/a",
                    "after_alt": "The glacier in 2025",
                    "credit": "Background: satellite.",
                }
            ],
        },
        "map": {
            "image": "img/a",
            "image_alt": "Map of the survey area",
            "caption": "Survey area.",
        },
        "video": {
            "youtube_id": "913rFrz9-xo",
            "title": "Expedition film",
            "thumbnail": "img/a",
            "thumbnail_alt": "Film still",
        },
        "science": [
            {"title": "Glaciology", "text": "Measuring ice."},
            {
                "title": "Mapping",
                "text": "Surveying caves.",
                "figure": "img/a",
                "figure_alt": "Surveyor at work",
            },
        ],
        "csi": {
            "name": "Centro Speleologico Indipendenti",
            "logo": "img/logo.png",
            "blurb": ["First sentence.", "Second sentence."],
        },
        "team": [
            {
                "group": "Core team",
                "members": [
                    {
                        "name": "Anna Rossi",
                        "role": "Expedition leader",
                        "line": "PhD in caving",
                        "photo": "img/a-800.webp",
                        "consent": True,
                    }
                ],
            }
        ],
        "press": {
            "articles": [
                {"year": 2025, "title": "On the ice", "byline": "A. Author, Some Magazine"}
            ],
            "talks": [
                {"year": 2025, "venue": "Town Hall", "place": "Trieste", "title": "Fire under ice"}
            ],
            "tv": [{"title": "Report", "outlet": "RAI", "url": "https://example.org/tv"}],
        },
        "partners": [
            {"name": "Partner One", "logo": "img/logo.png", "consent": True}
        ],
        "sponsors": [
            {"name": "Sponsor One", "logo": "img/logo.png", "consent": True}
        ],
        "credits": ["Original artwork by Lee Florea"],
    }


# ---------- validate ----------

def test_valid_content_has_no_errors(static_dir):
    assert validate(minimal_content(), static_dir) == []


def test_empty_sponsors_is_valid(static_dir):
    c = minimal_content()
    c["sponsors"] = []
    assert validate(c, static_dir) == []


def test_todo_is_error(static_dir):
    c = minimal_content()
    c["hero"]["subtitle"] = "TODO check"
    errors = validate(c, static_dir)
    assert len(errors) == 1
    assert errors[0].startswith("hero.subtitle:") and "TODO" in errors[0]


def test_missing_required_field(static_dir):
    c = minimal_content()
    del c["hero"]["image_alt"]
    assert "hero.image_alt: missing" in validate(c, static_dir)


def test_missing_image_file(static_dir):
    c = minimal_content()
    c["hero"]["image"] = "img/nope"
    errors = validate(c, static_dir)
    assert len(errors) == 1
    assert errors[0].startswith("hero.image:") and "not found" in errors[0]


def test_forbidden_phrase_case_insensitive(static_dir):
    c = minimal_content()
    c["project"]["paragraphs"] = ["An Extremophile story"]
    errors = validate(c, static_dir)
    assert len(errors) == 1
    assert "extremophile" in errors[0]


def test_all_errors_reported_together(static_dir):
    c = minimal_content()
    c["hero"]["subtitle"] = "TODO"
    del c["hero"]["image_alt"]
    c["project"]["paragraphs"] = ["The heart of Europe"]
    assert len(validate(c, static_dir)) == 3


def test_nested_path_in_error(static_dir):
    c = minimal_content()
    c["team"][0]["members"][0]["photo"] = "img/x.webp"
    errors = validate(c, static_dir)
    assert errors == ["team[0].members[0].photo: file not found: img/x.webp"]


# ---------- filter_consented ----------

def _team(*members):
    c = minimal_content()
    c["team"] = [{"group": "G", "members": list(members)}]
    return c


def test_consent_true_kept_false_and_missing_dropped():
    base = {"line": "x", "photo": "img/a-800.webp"}
    c = _team(
        {"name": "A", "consent": True, **base},
        {"name": "B", "consent": False, **base},
        {"name": "C", **base},
        {"name": "D", "consent": "yes", **base},
    )
    out, skipped = filter_consented(c)
    assert [m["name"] for m in out["team"][0]["members"]] == ["A"]
    assert skipped == ["B", "C", "D"]


def test_empty_group_removed():
    c = _team({"name": "B", "consent": False})
    out, skipped = filter_consented(c)
    assert out["team"] == []
    assert skipped == ["B"]


def test_partners_and_sponsors_filtered():
    c = minimal_content()
    c["partners"].append({"name": "Hidden", "logo": "img/logo.png"})
    c["sponsors"][0]["consent"] = False
    out, skipped = filter_consented(c)
    assert [p["name"] for p in out["partners"]] == ["Partner One"]
    assert out["sponsors"] == []
    assert skipped == ["Hidden", "Sponsor One"]


def test_filter_does_not_mutate_input():
    c = _team({"name": "B", "consent": False})
    before = copy.deepcopy(c)
    filter_consented(c)
    assert c == before


# ---------- inline_md ----------

def test_inline_md_escapes_html():
    assert inline_md("R&D <b>x</b>") == "R&amp;D &lt;b&gt;x&lt;/b&gt;"


def test_inline_md_italic():
    assert inline_md("*Indipendenti* in spirit") == "<em>Indipendenti</em> in spirit"


# ---------- image_info ----------

def test_image_info_responsive(static_dir):
    info = image_info(static_dir, "img/a")
    assert info.src == "static/img/a-1400.webp"
    assert info.srcset == "static/img/a-800.webp 800w, static/img/a-1400.webp 1400w"
    assert (info.width, info.height) == (1400, 1050)


def test_image_info_single(static_dir):
    info = image_info(static_dir, "img/logo.png")
    assert info.src == "static/img/logo.png"
    assert info.srcset == ""
    assert (info.width, info.height) == (100, 50)


def test_image_info_missing_raises(static_dir):
    with pytest.raises(FileNotFoundError):
        image_info(static_dir, "img/nope")
    with pytest.raises(FileNotFoundError):
        image_info(static_dir, "img/nope.webp")


def test_missing_caption_in_map_is_reported(static_dir):
    c = minimal_content()
    del c["map"]["caption"]
    assert "map.caption: missing" in validate(c, static_dir)


def test_missing_heading_title_is_reported(static_dir):
    c = minimal_content()
    del c["headings"]["press"]["title"]
    assert "headings.press.title: missing" in validate(c, static_dir)


def test_team_member_role_required(static_dir):
    c = minimal_content()
    del c["team"][0]["members"][0]["role"]
    assert validate(c, static_dir) == ["team[0].members[0].role: missing"]


def test_science_model_file_must_exist(static_dir):
    c = minimal_content()
    c["science"][1]["model"] = "model/x.glb"
    assert validate(c, static_dir) == ["science[1].model: file not found: model/x.glb"]
    (static_dir / "model").mkdir()
    (static_dir / "model" / "x.glb").write_bytes(b"glTF")
    assert validate(c, static_dir) == []


def test_comparison_background_needs_credit(static_dir):
    c = minimal_content()
    del c["comparison"]["backgrounds"][0]["credit"]
    assert validate(c, static_dir) == ["comparison.backgrounds[0].credit: missing"]


def test_press_photo_needs_credit(static_dir):
    c = minimal_content()
    c["press"]["photos"] = [{"image": "img/a", "image_alt": "Hall", "caption": "Costacciaro."}]
    assert "press.photos[0].credit: missing" in validate(c, static_dir)


def test_science_why_item_needs_text(static_dir):
    c = minimal_content()
    c["science_why"] = {"kicker": "Why", "title": "T", "items": [{"title": "A"}]}
    assert "science_why.items[0].text: missing" in validate(c, static_dir)
