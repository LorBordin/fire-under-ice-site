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
