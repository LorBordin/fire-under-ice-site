"""Tests for build.py: render a small site into a temporary folder."""
import re
import shutil
from pathlib import Path

import pytest
import yaml
from PIL import Image

from build import build
from tests.test_sitelib import minimal_content

REAL_TEMPLATES = Path(__file__).parent.parent / "templates"

SECTION_IDS = ["top", "project", "years", "watch", "science", "team", "press", "partners", "contact"]


@pytest.fixture
def site(tmp_path, static_dir):
    """A project folder (content.yaml, templates/, static/) ready to build.

    `static_dir` (from conftest.py) already created tmp_path/static.
    """
    shutil.copytree(REAL_TEMPLATES, tmp_path / "templates")
    write_content(tmp_path, minimal_content())
    return tmp_path


def write_content(root: Path, content: dict) -> None:
    (root / "content.yaml").write_text(
        yaml.safe_dump(content, allow_unicode=True), encoding="utf-8"
    )


def build_html(site: Path) -> str:
    out = site / "_site"
    assert build(site, out) == 0
    return (out / "index.html").read_text(encoding="utf-8")


def test_build_writes_index(site):
    out = site / "_site"
    assert build(site, out) == 0
    assert (out / "index.html").is_file()
    assert (out / "static" / "img" / "a-800.webp").is_file()


def test_build_fails_on_invalid_content(site, capsys):
    c = minimal_content()
    c["hero"]["subtitle"] = "TODO check"
    write_content(site, c)
    out = site / "_site"
    assert build(site, out) == 1
    assert not out.exists()
    assert "hero.subtitle" in capsys.readouterr().err


def test_utf8_characters(site):
    c = minimal_content()
    c["hero"]["title"] = "Kverkfjöll Mýrdalsjökull"
    write_content(site, c)
    html = build_html(site)
    assert "Kverkfjöll Mýrdalsjökull" in html
    assert '<meta charset="utf-8">' in html


def test_no_root_absolute_urls(site):
    html = build_html(site)
    assert not re.search(r'(src|href|srcset)="/', html)


def test_nonconsented_member_absent(site, capsys):
    c = minimal_content()
    c["team"][0]["members"].append(
        {"name": "Secret Person", "role": "r", "line": "x", "photo": "img/a-800.webp", "consent": False}
    )
    write_content(site, c)
    html = build_html(site)
    assert "Secret Person" not in html
    assert "Anna Rossi" in html
    assert "Secret Person" in capsys.readouterr().out  # reported as skipped


def test_section_ids_present(site):
    html = build_html(site)
    for section_id in SECTION_IDS:
        assert f'id="{section_id}"' in html
    for target in ["project", "years", "science", "team", "contact"]:
        assert f'href="#{target}"' in html


def test_stale_files_removed(site):
    extra = site / "static" / "img" / "extra.png"
    Image.new("RGB", (10, 10)).save(extra)
    out = site / "_site"
    assert build(site, out) == 0
    assert (out / "static" / "img" / "extra.png").exists()
    extra.unlink()
    assert build(site, out) == 0
    assert not (out / "static" / "img" / "extra.png").exists()


def test_all_images_have_alt(site):
    html = build_html(site)
    tags = re.findall(r"<img\b[^>]*>", html)
    assert tags
    for tag in tags:
        assert re.search(r'alt="[^"]+"', tag), tag
        assert 'width="' in tag and 'height="' in tag, tag


def test_markup_hooks_for_js(site):
    html = build_html(site)
    assert 'class="hero-img"' in html and 'fetchpriority="high"' in html
    assert 'data-youtube="913rFrz9-xo"' in html
    assert re.search(r'<input[^>]*type="range"[^>]*\bhidden\b', html)
    assert "og:image" in html and "https://fireunderice.org/static/img/a-1400.webp" in html
    assert html.count('class="reveal"') == len(SECTION_IDS) - 1


def test_text_is_escaped_and_italic(site):
    c = minimal_content()
    c["project"]["paragraphs"] = ["R&D with *Indipendenti* <b>x</b>"]
    write_content(site, c)
    html = build_html(site)
    assert "R&amp;D with <em>Indipendenti</em> &lt;b&gt;x&lt;/b&gt;" in html


def test_sponsors_heading_only_when_present(site):
    assert "Sponsors" in build_html(site)
    c = minimal_content()
    c["sponsors"] = []
    write_content(site, c)
    assert "Sponsors" not in build_html(site)


def test_team_shows_only_csi_when_nobody_consents(site):
    c = minimal_content()
    c["team"][0]["members"][0]["consent"] = False
    write_content(site, c)
    html = build_html(site)
    assert "Centro Speleologico Indipendenti" in html
    assert "team-group" not in html


def test_team_role_and_bio_rendered(site):
    html = build_html(site)
    assert '<span class="role">Expedition leader</span>' in html
    assert "PhD in caving" in html


def test_science_model_button(site):
    c = minimal_content()
    c["science"][1]["model"] = "model/x.glb"
    write_content(site, c)
    (site / "static" / "model").mkdir()
    (site / "static" / "model" / "x.glb").write_bytes(b"\0" * 2_600_000)
    html = build_html(site)
    assert 'data-model="static/model/x.glb"' in html
    assert "Explore in 3D (2.6 MB)" in html
    # The button only works with JavaScript, so it starts hidden.
    assert re.search(r"<button[^>]*class=\"model-load\"[^>]*hidden", html)


def test_no_model_no_button(site):
    assert "model-load" not in build_html(site)


def test_science_model_marker(site):
    c = minimal_content()
    c["science"][1]["model"] = "model/x.glb"
    c["science"][1]["model_marker"] = "1m 2m 3m"
    write_content(site, c)
    (site / "static" / "model").mkdir()
    (site / "static" / "model" / "x.glb").write_bytes(b"glTF")
    assert 'data-model-marker="1m 2m 3m"' in build_html(site)


def _two_backgrounds():
    c = minimal_content()
    drone = dict(c["comparison"]["backgrounds"][0], label="Drone 2026", credit="Background: drone.")
    c["comparison"]["backgrounds"].append(drone)
    return c


def test_comparison_single_background_has_no_switch(site):
    html = build_html(site)
    assert "compare-switch" not in html
    assert "Background: satellite." in html


def test_comparison_switch(site):
    write_content(site, _two_backgrounds())
    html = build_html(site)
    # Hidden without JS; the first background is shown and pressed.
    assert re.search(r'<div class="compare-switch"[^>]*hidden', html)
    assert re.search(r'<button[^>]*aria-pressed="true"[^>]*>Satellite 2024</button>', html)
    assert re.search(r'<button[^>]*aria-pressed="false"[^>]*>Drone 2026</button>', html)
    assert 'data-credit="Background: drone."' in html
    assert '<span class="compare-credit">Background: satellite.</span>' in html


# ------------------------------------------------------------ place pages

from tests.test_places import place, with_places  # noqa: E402


@pytest.fixture
def site_with_places(site):
    # The real fonts, CSS and JS, so the link check covers the <head> too.
    real_static = REAL_TEMPLATES.parent / "static"
    shutil.copytree(real_static / "fonts", site / "static" / "fonts")
    for name in ("style.css", "script.js"):
        shutil.copy(real_static / name, site / "static" / name)
    c = with_places(site / "static", place("torfa"), place("kverkfjoll", n=5))
    write_content(site, c)
    return site


def built_pages(out: Path) -> list[Path]:
    return sorted(out.rglob("*.html"))


def test_writes_place_pages(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    assert (out / "index.html").is_file()
    assert (out / "torfa" / "index.html").is_file()
    assert (out / "kverkfjoll" / "index.html").is_file()


_URL_ATTR = re.compile(r'\b(src|href|srcset|data-srcset)="([^"]*)"')


def test_all_local_links_resolve(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    pages = [p for p in built_pages(out) if p.parent == out or p.parent.parent == out]
    assert len(pages) == 3
    checked = 0
    for page in pages:
        html = page.read_text(encoding="utf-8")
        for attr, value in _URL_ATTR.findall(html):
            urls = [part.strip().split(" ")[0] for part in value.split(",")] if "srcset" in attr else [value]
            for url in urls:
                if not url or url.startswith(("http:", "https:", "mailto:", "#")):
                    continue
                path = url.split("#")[0]
                target = (page.parent / path).resolve()
                if path == "" or path.endswith("/"):
                    target = target / "index.html"
                assert target.is_file(), f"{page.relative_to(out)}: {attr}={url}"
                checked += 1
    assert checked > 20


def test_place_page_title_and_og(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    html = (out / "torfa" / "index.html").read_text(encoding="utf-8")
    assert "<title>Torfa place · Fire Under Ice</title>" in html
    assert 'content="https://fireunderice.org/static/img/places/torfa/p0-' in html
    assert '<meta name="description" content="One sentence.">' in html


def test_place_nav_points_home(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    html = (out / "torfa" / "index.html").read_text(encoding="utf-8")
    assert 'href="../#team"' in html
    assert 'href="../#places"' in html
    assert 'href="../kverkfjoll/"' in html


def test_gallery_links_without_js(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    html = (out / "kverkfjoll" / "index.html").read_text(encoding="utf-8")
    links = re.findall(r'<a href="([^"]+)" data-index="(\d+)"[^>]*aria-label="([^"]+)"', html)
    assert [int(i) for _, i, _ in links] == list(range(5))
    for href, _, label in links:
        assert href.startswith("../static/img/places/kverkfjoll/") and href.endswith("-800.webp")
        assert "©" in label or "&copy;" in label
    assert 'id="photo-1"' in html and 'id="photo-5"' in html


def test_no_places_no_nav_link(site):
    out = site / "_site"
    assert build(site, out) == 0
    assert 'href="#places"' not in (out / "index.html").read_text(encoding="utf-8")
    assert len(built_pages(out)) == 1


def test_places_section(site_with_places):
    html = build_html(site_with_places)
    assert 'id="places"' in html
    assert html.count('class="place-card"') == 2
    assert 'href="torfa/"' in html and 'href="kverkfjoll/"' in html
    assert "See all 4 photos" in html and "See all 5 photos" in html
    for card in re.findall(r'<article class="place-card">.*?</article>', html, re.S):
        thumbs = re.search(r'<ul class="place-thumbs">(.*?)</ul>', card, re.S).group(1)
        assert thumbs.count("<img") == 3
    first = re.search(r'<article class="place-card">.*?</article>', html, re.S).group(0)
    assert re.search(r'<a class="place-card-link"[^>]*>\s*<img src="static/img/places/torfa/p0-', first)


def test_places_nav_link(site_with_places):
    assert 'href="#places"' in build_html(site_with_places)


def test_viewer_markup(site_with_places):
    out = site_with_places / "_site"
    assert build(site_with_places, out) == 0
    html = (out / "torfa" / "index.html").read_text(encoding="utf-8")
    assert html.count('<dialog class="viewer"') == 1
    for cls, label in (("viewer-prev", "Previous photo"), ("viewer-next", "Next photo"), ("viewer-close", "Close")):
        assert re.search(rf'<button[^>]*class="{cls}"[^>]*aria-label="{label}"', html)
    assert "<dialog" not in (out / "index.html").read_text(encoding="utf-8")


# ------------------------------------------------ field, science, contact, credits

def _field_item(title="Rivers", credit="Andrea Benassi"):
    return {"title": title, "text": f"{title} text.", "image": "img/a", "image_alt": f"{title} photo", "credit": credit}


def test_field_section(site):
    c = minimal_content()
    c["headings"]["field"] = {"kicker": "In the field", "title": "What it takes"}
    c["field"] = [_field_item("Rivers"), _field_item("Heat")]
    write_content(site, c)
    html = build_html(site)
    assert 'id="field"' in html
    section = re.search(r'<section id="field".*?</section>', html, re.S).group(0)
    assert section.count("<img") == 2
    assert "Rivers photo" in section and "<h3>Heat</h3>" in section


def test_science_card_images(site):
    c = minimal_content()
    c["science"][0]["image"] = "img/a"
    c["science"][0]["image_alt"] = "Hot pool"
    c["science"][1]["model"] = "model/x.glb"
    write_content(site, c)
    (site / "static" / "model").mkdir()
    (site / "static" / "model" / "x.glb").write_bytes(b"glTF")
    html = build_html(site)
    card = re.search(r'<li class="card">(?:(?!</li>).)*Glaciology.*?</li>', html, re.S).group(0)
    assert 'alt="Hot pool"' in card
    # The wide figure of the entry with a model still renders, outside the cards.
    assert re.search(r'<figure class="science-figure" data-model="static/model/x.glb"[^>]*>\s*<img[^>]*alt="Surveyor at work"', html)
    assert html.count('class="science-figure"') == 1


def test_contact_background(site):
    c = minimal_content()
    c["contact_image"] = {"image": "img/a", "image_alt": "Blue ice", "credit": "Maria F. Trombini"}
    write_content(site, c)
    html = build_html(site)
    assert '<img src="static/img/a-800.webp"' in html
    assert re.search(r'<img [^>]*class="contact-bg"', html)


def test_photo_credits_footer(site):
    c = minimal_content()
    c["headings"]["field"] = {"kicker": "In the field", "title": "What it takes"}
    c["field"] = [_field_item("Rivers", "Maria F. Trombini"), _field_item("Heat", "Andrea Benassi")]
    c["contact_image"] = {"image": "img/a", "image_alt": "Blue ice", "credit": "Ivan Vicenzi"}
    write_content(site, c)
    html = build_html(site)
    assert "<li>Photos: Andrea Benassi, Maria F. Trombini, Ivan Vicenzi.</li>" in html
    assert 'Photos © their authors. For use, write to <a href="mailto:info@fireunderice.org">' in html


def test_no_photo_credit_without_photos(site):
    assert "Photos:" not in build_html(site)


def test_viewer_touch_rules():
    """Pinch-zoom stays possible; swipes work anywhere in the viewer; second fingers ignored."""
    real = REAL_TEMPLATES.parent / "static"
    css = (real / "style.css").read_text(encoding="utf-8")
    js = (real / "script.js").read_text(encoding="utf-8")
    assert re.search(r"\.viewer\{[^}]*touch-action:pan-y pinch-zoom", css)
    assert not re.search(r"\.viewer-figure img\{[^}]*touch-action:pan-y\b(?! pinch)", css)
    assert "pointercancel" in js and "isPrimary" in js


def test_stat_note(site):
    c = minimal_content()
    c["project"]["stats"] = [
        {"value": "1984–2026", "label": "survey record", "note": "Surveys up to 2008 by others."}
    ]
    write_content(site, c)
    html = build_html(site)
    assert "1984–2026*" in re.sub(r"<[^>]+>", "", html)
    assert '<p class="note stats-note">* Surveys up to 2008 by others.</p>' in html


def test_article_status(site):
    c = minimal_content()
    c["press"]["articles"][0]["status"] = "in press"
    write_content(site, c)
    assert '<span class="status">in press</span>' in build_html(site)


def test_press_photos(site):
    c = minimal_content()
    c["press"]["photos"] = [
        {"image": "img/a", "image_alt": "Hall", "caption": "Costacciaro.", "credit": "Paolo Testa"}
    ]
    write_content(site, c)
    html = build_html(site)
    section = html[html.index('id="press"'):html.index('id="partners"')]
    assert 'alt="Hall"' in section
    assert "Costacciaro." in section and "Paolo Testa" in section
    footer = html[html.index('class="site-footer"'):]
    assert "Paolo Testa" in footer


def _patron_content(flag):
    c = minimal_content()
    c["partners"] = [
        {"name": "Partner One", "logo": "img/logo.png", "consent": True, "patron_2027": flag},
        {"name": "Partner Two", "logo": "img/logo.png", "consent": True},
    ]
    c["headings"]["partners"]["patron_note"] = "Patronage being sought for 2027"
    return c


def test_patron_star(site):
    write_content(site, _patron_content(True))
    html = build_html(site)
    assert html.count('class="patron-star"') == 1
    assert "Patronage being sought for 2027" in html


def test_patron_star_exactly_true(site):
    write_content(site, _patron_content("true"))
    html = build_html(site)
    assert 'class="patron-star"' not in html
    assert "Patronage being sought" not in html
