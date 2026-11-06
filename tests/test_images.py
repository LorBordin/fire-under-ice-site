"""Tests for prepare_images.py, using small Pillow-generated sources."""
from pathlib import Path

from PIL import Image

from prepare_images import logo, responsive, split_halves, square


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


def test_split_halves(tmp_path):
    img = Image.new("RGB", (2000, 500), "blue")
    img.paste(Image.new("RGB", (1000, 500), "red"), (0, 0))
    src = tmp_path / "s.png"
    img.save(src)
    split_halves(src, tmp_path / "left", tmp_path / "right")
    with Image.open(tmp_path / "left-800.webp") as im:
        r, g, b = im.convert("RGB").getpixel((10, 10))
        assert r > 200 and b < 60
    with Image.open(tmp_path / "right-800.webp") as im:
        r, g, b = im.convert("RGB").getpixel((10, 10))
        assert b > 200 and r < 60
