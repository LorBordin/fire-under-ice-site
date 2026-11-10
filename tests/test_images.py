"""Tests for prepare_images.py, using small Pillow-generated sources."""
from pathlib import Path

import pytest

from PIL import Image

from prepare_images import (
    FONT, gallery_jobs, logo, responsive, run_gallery, square, watermark,
)
from tests.test_places import place
from tests.test_topics import topic

# A generated stand-in for the brochure badge, so tests never need the brochure.
badge = Image.new("RGBA", (216, 206), (0, 0, 0, 255))
WHITE = (255, 255, 255)


def make(path: Path, size, color="gray", mode="RGB") -> Path:
    Image.new(mode, size, color).save(path)
    return path


def test_responsive_widths(tmp_path):
    src = make(tmp_path / "a.png", (2500, 1000))
    outs = responsive(src, tmp_path / "out")
    assert [p.name for p in outs] == ["out-800.webp", "out-1400.webp", "out-2000.webp"]
    for p, w in zip(outs, (800, 1400, 2000)):
        with Image.open(p) as im:
            assert im.width == w
            assert abs(im.height - w * 0.4) <= 1


def test_responsive_no_upscale(tmp_path):
    src = make(tmp_path / "a.png", (1000, 500))
    outs = responsive(src, tmp_path / "out")
    assert [p.name for p in outs] == ["out-800.webp"]


def test_responsive_small_source(tmp_path):
    src = make(tmp_path / "a.png", (500, 300))
    outs = responsive(src, tmp_path / "out")
    assert [p.name for p in outs] == ["out-500.webp"]


def test_square(tmp_path):
    src = make(tmp_path / "a.png", (600, 400))
    out = square(src, tmp_path / "s.webp")
    with Image.open(out) as im:
        assert im.size == (400, 400)


def test_logo_keeps_alpha(tmp_path):
    src = make(tmp_path / "l.png", (400, 200), (255, 0, 0, 0), "RGBA")
    out = logo(src, tmp_path / "o.png", 160)
    with Image.open(out) as im:
        assert im.size == (320, 160)
        assert im.mode == "RGBA"


# ------------------------------------------------------------ watermark

def test_watermark_keeps_size_and_marks_corner():
    im = Image.new("RGB", (2000, 1500), "white")
    out = watermark(im, "Andrea Benassi", badge, FONT)
    assert out.size == (2000, 1500) and out.mode == "RGB"
    assert out.getpixel((1940, 1440)) != WHITE   # inside the badge
    assert out.getpixel((10, 10)) == WHITE       # top-left untouched


def test_watermark_portrait():
    out = watermark(Image.new("RGB", (1500, 2000), "white"), "Maria F. Trombini", badge, FONT)
    # badge width 0.08 * min(1500, 2666) = 120 px: column 1500-37-121 is clear
    # of the badge, 1500-37-60 is inside it
    assert out.getpixel((1500 - 37 - 60, 2000 - 37 - 30)) != WHITE


def test_watermark_non_ascii_author():
    out = watermark(Image.new("RGB", (2000, 1500), "white"), "Lorenzo Scialò", badge, FONT)
    assert out.getpixel((1940, 1440)) != WHITE


# ------------------------------------------------------------ gallery

def two_places() -> dict:
    return {"places": [place("torfa", 2), place("kverkfjoll", 1)]}


def test_gallery_jobs():
    jobs = gallery_jobs(two_places())
    assert jobs == [
        ("photos/torfa/P0.JPG", "Andrea Benassi", "img/places/torfa/p0"),
        ("photos/torfa/P1.JPG", "Andrea Benassi", "img/places/torfa/p1"),
        ("photos/kverkfjoll/P0.JPG", "Andrea Benassi", "img/places/kverkfjoll/p0"),
    ]


def one_place_content(name="P1.JPG") -> dict:
    pl = place("torfa", 1)
    pl["photos"][0]["source"] = f"photos/torfa/{name}"
    return {"places": [pl]}


def make_source(root: Path, size, name="P1.JPG", exif=False) -> None:
    src = root / "photos/torfa" / name
    src.parent.mkdir(parents=True, exist_ok=True)
    kwargs = {}
    if exif:
        e = Image.Exif()
        e[0x010F] = "Cam"
        kwargs["exif"] = e
    Image.new("RGB", size, "gray").save(src, **kwargs)


def test_run_gallery_writes_widths_without_exif(tmp_path):
    root, out = tmp_path / "root", tmp_path / "out"
    make_source(root, (2500, 1875), exif=True)
    with Image.open(root / "photos/torfa/P1.JPG") as src:
        assert src.getexif()          # the source really has EXIF
    paths = run_gallery(one_place_content(), root, out, badge, FONT)
    names = sorted(p.name for p in paths)
    assert names == ["p1-1400.webp", "p1-2000.webp", "p1-400.webp", "p1-800.webp"]
    for p in paths:
        with Image.open(p) as im:
            assert im.width == int(p.stem.split("-")[1])
            assert not im.getexif()


def test_run_gallery_no_upscale(tmp_path):
    root, out = tmp_path / "root", tmp_path / "out"
    make_source(root, (900, 600))
    paths = run_gallery(one_place_content(), root, out, badge, FONT)
    assert sorted(p.name for p in paths) == ["p1-400.webp", "p1-800.webp"]


def test_run_gallery_tiny_source(tmp_path):
    root, out = tmp_path / "root", tmp_path / "out"
    make_source(root, (300, 200))
    paths = run_gallery(one_place_content(), root, out, badge, FONT)
    assert [p.name for p in paths] == ["p1-300.webp"]


def test_gallery_removes_stale(tmp_path):
    root, out = tmp_path / "root", tmp_path / "out"
    make_source(root, (900, 600))
    (out / "places/torfa").mkdir(parents=True)
    (out / "places/gone").mkdir(parents=True)
    (out / "places/torfa/old-800.webp").write_bytes(b"x")
    (out / "places/gone/x-800.webp").write_bytes(b"x")
    run_gallery(one_place_content(), root, out, badge, FONT)
    assert not (out / "places/torfa/old-800.webp").exists()
    assert not (out / "places/gone").exists()
    assert (out / "places/torfa/p1-800.webp").exists()


def test_watermark_rejects_letters_missing_from_font():
    badge = Image.new("RGBA", (216, 206), (0, 0, 0, 255))
    im = Image.new("RGB", (800, 600), "white")
    with pytest.raises(ValueError, match="Ł"):
        watermark(im, "Łukasz Čech", badge, FONT)


def test_guide_jobs_examples_use_expedition_root():
    import re
    guide = (Path(__file__).parent.parent / "GUIDE.md").read_text(encoding="utf-8")
    sources = re.findall(r'\("(?:responsive|square|logo|pdf)", "([^"]+)"', guide)
    assert sources, "GUIDE.md should show a JOBS example"
    for s in sources:
        assert s.startswith(("brochure/", "photos/")), s


def topic_content() -> dict:
    return {"places": [place("torfa", 1)], "topics": [topic("microbiology", photo=True)]}


def test_gallery_jobs_include_topics():
    jobs = gallery_jobs(topic_content())
    assert ("photos/science/microbiology_sample.JPG", "Cristian Monticone",
            "img/places/microbiology/microbiology-sample") in jobs


def test_run_gallery_keeps_topic_folder_and_removes_deleted_topic(tmp_path):
    root, out = tmp_path / "root", tmp_path / "out"
    make_source(root, (900, 600))
    src = root / "photos/science/microbiology_sample.JPG"
    src.parent.mkdir(parents=True)
    Image.new("RGB", (900, 600), "gray").save(src)
    content = topic_content()
    content["places"][0]["photos"][0]["source"] = "photos/torfa/P1.JPG"
    run_gallery(content, root, out, badge, FONT)
    assert (out / "places/microbiology/microbiology-sample-800.webp").exists()
    assert (out / "places/torfa/p1-800.webp").exists()
    del content["topics"]
    run_gallery(content, root, out, badge, FONT)
    assert not (out / "places/microbiology").exists()
    assert (out / "places/torfa/p1-800.webp").exists()
