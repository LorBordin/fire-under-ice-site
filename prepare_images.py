"""Turn the brochure's original images into small web images.

Reads from the brochure folder (never modifies it) and writes WebP/PNG files
under static/img/. Run with:  uv run prepare_images.py

To add a photo: add one line to JOBS below, e.g.
    ("responsive", "figures/photos/my-photo.jpg", "my-photo"),
then reference it in content.yaml as `img/my-photo` (no extension; the site
picks up the -800/-1400/-2000 versions automatically).

Job kinds:
  responsive  several widths, named <out>-<width>.webp
  square      400x400 centre crop, <out>.webp (team portraits)
  logo        PNG, 160 px high, transparency kept
  pdf         first page of a PDF, then responsive
  split       left/right halves of one image (needs two output names)
  thumbnail   downloaded from YouTube, then responsive
"""
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

HERE = Path(__file__).parent
BROCHURE = Path.home() / "expeditions/Iceland/brochure/2027"
OUT_DIR = HERE / "static" / "img"

WIDTHS = (800, 1400, 2000)
QUALITY = 78
THUMB_URL = "https://i.ytimg.com/vi/913rFrz9-xo/maxresdefault.jpg"

# (kind, source relative to BROCHURE, output relative to static/img)
JOBS: list[tuple[str, str, str]] = [
    ("responsive", "figures/photos/p01-cover.jpg", "p01-cover"),
    ("responsive", "figures/photos/p06-lake.jpg", "p06-lake"),
    ("responsive", "figures/photos/p08-cauldron.jpg", "p08-cauldron"),
    ("responsive", "figures/photos/p08-sala-rosa.jpg", "p08-sala-rosa"),
    ("responsive", "figures/composites/f7_3d.jpg", "f7-3d"),
    ("responsive", "figures/composites/f7_ortho.jpg", "f7-ortho"),
    ("responsive", "figures/composites/f3_lake_overlay.jpg", "f3-lake-overlay"),
    # f4_2006_vs_2025.jpg is ONE overlay map (2006 in blue on the 2025 survey in
    # orange), not two side-by-side halves, so it is not split. Use "responsive":
    ("responsive", "figures/composites/f4_2006_vs_2025.jpg", "f4-2006-vs-2025"),
    ("pdf", "figures/composites/f2_iceland_map.pdf", "map-iceland"),
    # Team portraits: source file in people/ -> team/<surname>.webp
    ("square", "people/benassi.png", "team/benassi.webp"),
    ("square", "people/lorenzo.png", "team/bordin.webp"),
    ("square", "people/jerba.png", "team/gerbaudo.webp"),
    ("square", "people/lazzaro.jpeg", "team/monticone.webp"),
    ("square", "people/maria.png", "team/trombini.webp"),
    ("square", "people/marco.png", "team/ettrapini.webp"),
    ("square", "people/urbanet.jpg", "team/urbanet.webp"),
    ("square", "people/paco.png", "team/vicenzi.webp"),
    ("square", "people/scialo.png", "team/scialo.webp"),
    ("square", "people/turrini.png", "team/turrini.webp"),
    ("square", "people/Katia.png", "team/zampatti.webp"),
    ("square", "people/tommi.png", "team/biondi.webp"),
    ("square", "people/testa.png", "team/testa.webp"),
    # (people/maria.jpeg is deliberately ignored)
    ("logo", "logos/SSI.png", "logos/ssi.png"),
    ("logo", "logos/FVG.png", "logos/fvg.png"),
    ("logo", "logos/cai_logo.png", "logos/cai_logo.png"),
    ("logo", "logos/soc_geo_logo_crop.png", "logos/soc_geo_logo_crop.png"),
    ("logo", "logos/gaibana_logo.png", "logos/gaibana_logo.png"),
    ("logo", "logos/csi_logo_crop.png", "logos/csi_logo_crop.png"),
    ("thumbnail", THUMB_URL, "video-thumb"),
]


def _open(src: Path) -> Image.Image:
    """Open an image and apply its EXIF rotation."""
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)
    return im


def _save_webp(im: Image.Image, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "WEBP", quality=QUALITY, method=6)


def _responsive_image(im: Image.Image, out_stem: Path) -> list[Path]:
    widths = [w for w in WIDTHS if w <= im.width] or [im.width]
    if im.width < WIDTHS[0]:
        widths = [im.width]
    outs = []
    for w in widths:
        h = round(im.height * w / im.width)
        small = im.resize((w, h), Image.LANCZOS) if w != im.width else im.copy()
        out = out_stem.parent / f"{out_stem.name}-{w}.webp"
        _save_webp(small, out)
        outs.append(out)
    return outs


def responsive(src: Path, out_stem: Path) -> list[Path]:
    """Write <out_stem>-<w>.webp for each width that does not upscale."""
    with _open(src) as im:
        return _responsive_image(im, out_stem)


def square(src: Path, out: Path, size: int = 400) -> Path:
    """Centre-crop to a square, resize, save as WebP."""
    with _open(src) as im:
        im = ImageOps.fit(im, (size, size), Image.LANCZOS, centering=(0.5, 0.5))
        _save_webp(im, out)
    return out


def logo(src: Path, out: Path, height: int) -> Path:
    """Resize to `height` px (never upscale), keep transparency, save PNG."""
    with _open(src) as im:
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA")
        if im.height > height:
            im = im.resize((round(im.width * height / im.height), height), Image.LANCZOS)
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out, "PNG", optimize=True)
    return out


def split_halves(src: Path, left_stem: Path, right_stem: Path) -> None:
    """Crop the left and right halves of an image, each through responsive()."""
    with _open(src) as im:
        mid = im.width // 2
        _responsive_image(im.crop((0, 0, mid, im.height)), left_stem)
        _responsive_image(im.crop((mid, 0, im.width, im.height)), right_stem)


def rasterise_pdf(src: Path, out_stem: Path) -> list[Path]:
    """Render page 1 of a PDF with ImageMagick, then make responsive sizes."""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "page.png"
        subprocess.run(
            ["magick", "-density", "200", f"{src}[0]", "-background", "white",
             "-alpha", "remove", str(png)],
            check=True,
        )
        return responsive(png, out_stem)


def _download_thumbnail(out_stem: Path) -> list[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp) / "thumb.jpg"
        with urllib.request.urlopen(THUMB_URL, timeout=30) as resp:
            tmp_file.write_bytes(resp.read())
        return responsive(tmp_file, out_stem)


def run_job(kind: str, source: str, output: str) -> list[Path]:
    out = OUT_DIR / output
    src = BROCHURE / source
    if kind == "responsive":
        return responsive(src, out)
    if kind == "square":
        return [square(src, out)]
    if kind == "logo":
        return [logo(src, out, 160)]
    if kind == "pdf":
        return rasterise_pdf(src, out)
    if kind == "thumbnail":
        return _download_thumbnail(out)
    raise ValueError(f"unknown job kind: {kind}")


def main() -> None:
    total = 0
    for kind, source, output in JOBS:
        try:
            outs = run_job(kind, source, output)
        except Exception as exc:  # keep going: one bad job must not stop the rest
            print(f"WARNING: {kind} {source} failed: {exc}", file=sys.stderr)
            continue
        for p in outs:
            size = p.stat().st_size
            total += size
            print(f"{p.relative_to(HERE)}  {size / 1024:.0f} KB")
    print(f"Total: {total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
