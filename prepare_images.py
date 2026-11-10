"""Turn the brochure's original images into small web images.

Reads from the brochure folder (never modifies it) and writes WebP/PNG files
under static/img/. Run with:  uv run prepare_images.py

To add a photo: add one line to JOBS below, e.g.
    ("responsive", "brochure/2027/figures/photos/my-photo.jpg", "my-photo"),
then reference it in content.yaml as `img/my-photo` (no extension; the site
picks up the -800/-1400/-2000 versions automatically).

Job kinds:
  responsive  several widths, named <out>-<width>.webp
  square      400x400 centre crop, <out>.webp (team portraits)
  logo        PNG, 160 px high, transparency kept
  pdf         first page of a PDF, then responsive
  thumbnail   downloaded from YouTube, then responsive
  gallery     place photos listed in content.yaml, watermarked, widths
              400/800/1400/2000, written to static/img/places/<slug>/
"""
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from sitelib import gallery_ref, load_content

HERE = Path(__file__).parent
EXPEDITION = Path.home() / "expeditions/Iceland"
BROCHURE = EXPEDITION / "brochure/2027"
OUT_DIR = HERE / "static" / "img"

WIDTHS = (800, 1400, 2000)
GALLERY_WIDTHS = (400, 800, 1400, 2000)
# The badge and font of the watermark on gallery photos.
BADGE = BROCHURE / "logos/csi_logo_crop.png"
FONT = HERE / "fonts/Cabin-SemiBold.otf"
QUALITY = 78
# The thumbnail follows video.youtube_id in content.yaml (rerun this script after changing it).
THUMB_URL = "https://i.ytimg.com/vi/{id}/maxresdefault.jpg"

# (kind, source relative to EXPEDITION, output relative to static/img)
JOBS: list[tuple[str, str, str]] = [
    ("responsive", "brochure/2027/figures/photos/p01-cover.jpg", "p01-cover"),
    ("responsive", "photos/press/people.JPG", "press-hall"),
    ("responsive", "photos/press/presentazione_2.JPG", "press-talk"),
    ("responsive", "brochure/2027/figures/photos/p06-lake.jpg", "p06-lake"),
    ("responsive", "brochure/2027/figures/photos/p08-cauldron.jpg", "p08-cauldron"),
    ("responsive", "brochure/2027/figures/photos/p08-sala-rosa.jpg", "p08-sala-rosa"),
    ("responsive", "brochure/2027/figures/composites/f7_3d.jpg", "f7-3d"),
    ("responsive", "brochure/2027/figures/composites/f7_ortho.jpg", "f7-ortho"),
    ("responsive", "brochure/2027/figures/composites/f3_lake_overlay.jpg", "f3-lake-overlay"),
    # The 2006 vs 2025 slider images are built by make_comparison.py.
    ("pdf", "brochure/2027/figures/composites/f2_iceland_map.pdf", "map-iceland"),
    ("pdf", "brochure/2027/figures/composites/f6_targets_map.pdf", "map-targets-2027"),
    ("responsive", "brochure/2027/figures/composites/f1_schema.jpg", "f1-schema"),
    ("responsive", "brochure/2027/figures/composites/f_p05_hveradalur2025.png", "survey-hveradalur-2025"),
    # Team portraits: source file in people/ -> team/<surname>.webp
    ("square", "brochure/2027/people/benassi.png", "team/benassi.webp"),
    ("square", "brochure/2027/people/lorenzo.png", "team/bordin.webp"),
    ("square", "brochure/2027/people/jerba.png", "team/gerbaudo.webp"),
    ("square", "brochure/2027/people/lazzaro.jpeg", "team/monticone.webp"),
    ("square", "brochure/2027/people/maria.png", "team/trombini.webp"),
    ("square", "brochure/2027/people/marco.png", "team/ettrapini.webp"),
    ("square", "brochure/2027/people/urbanet.jpg", "team/urbanet.webp"),
    ("square", "brochure/2027/people/paco.png", "team/vicenzi.webp"),
    ("square", "brochure/2027/people/scialo.png", "team/scialo.webp"),
    ("square", "brochure/2027/people/turrini.png", "team/turrini.webp"),
    ("square", "brochure/2027/people/Katia.png", "team/zampatti.webp"),
    ("square", "brochure/2027/people/tommi.png", "team/biondi.webp"),
    ("square", "brochure/2027/people/testa.png", "team/testa.webp"),
    # (people/maria.jpeg is deliberately ignored)
    ("logo", "brochure/2027/logos/SSI.png", "logos/ssi.png"),
    ("logo", "brochure/2027/logos/FVG.png", "logos/fvg.png"),
    ("logo", "brochure/2027/logos/cai_logo.png", "logos/cai_logo.png"),
    ("logo", "brochure/2027/logos/soc_geo_logo_crop.png", "logos/soc_geo_logo_crop.png"),
    ("logo", "brochure/2027/logos/gaibana_logo.png", "logos/gaibana_logo.png"),
    ("logo", "brochure/2027/logos/csi_logo_crop.png", "logos/csi_logo_crop.png"),
    ("thumbnail", THUMB_URL, "video-thumb"),
    # Section photos on the home page (clean; their place galleries carry the watermark).
    ("responsive", "photos/torfa/river_crossing.JPG", "field-river"),
    ("responsive", "photos/kverkfjoll/P7161066.JPG", "field-rope"),
    ("responsive", "photos/kverkfjoll/P7181204.JPG", "field-gas"),
    ("responsive", "photos/kverkfjoll/P7161094.JPG", "field-heat"),
    ("responsive", "photos/torfa/RIMG0247.JPG", "science-pool"),
    ("responsive", "photos/torfa/thermal_camera.JPG", "science-thermal"),
    ("responsive", "photos/kverkfjoll/blue_ice.jpg", "contact-blue-ice"),
]


def _open(src: Path) -> Image.Image:
    """Open an image and apply its EXIF rotation."""
    im = Image.open(src)
    im = ImageOps.exif_transpose(im)
    return im


def _save_webp(im: Image.Image, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "WEBP", quality=QUALITY, method=6)


def _responsive_image(im: Image.Image, out_stem: Path, widths_set=WIDTHS,
                      finish=lambda im: im) -> list[Path]:
    """Write one WebP per width in `widths_set` that does not upscale.

    `finish` is applied to each resized image before saving (the gallery
    uses it to add the watermark at every size).
    """
    widths = [w for w in widths_set if w <= im.width] or [im.width]
    if im.width < widths_set[0]:
        widths = [im.width]
    outs = []
    for w in widths:
        h = round(im.height * w / im.width)
        small = im.resize((w, h), Image.LANCZOS) if w != im.width else im.copy()
        out = out_stem.parent / f"{out_stem.name}-{w}.webp"
        _save_webp(finish(small), out)
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


def rasterise_pdf(src: Path, out_stem: Path) -> list[Path]:
    """Render page 1 of a PDF with ImageMagick, then make responsive sizes."""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "page.png"
        subprocess.run(
            ["magick", "-density", "200", f"{src}[0]", "-background", "#0D0D0D",
             "-alpha", "remove", str(png)],
            check=True,
        )
        return responsive(png, out_stem)


def _youtube_id() -> str:
    """The video id from content.yaml, so the thumbnail always matches the video."""
    from sitelib import load_content
    return load_content(HERE / "content.yaml")["video"]["youtube_id"]


def _download_thumbnail(out_stem: Path) -> list[Path]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_file = Path(tmp) / "thumb.jpg"
        with urllib.request.urlopen(THUMB_URL.format(id=_youtube_id()), timeout=30) as resp:
            tmp_file.write_bytes(resp.read())
        return responsive(tmp_file, out_stem)


def run_job(kind: str, source: str, output: str) -> list[Path]:
    out = OUT_DIR / output
    src = EXPEDITION / source
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


def watermark(im: Image.Image, author: str, badge: Image.Image, font_path: Path) -> Image.Image:
    """Return a copy of `im` with the badge and "(c) author" at bottom right.

    All sizes scale with `base`, the shorter side of a 4:3 frame, so the mark
    looks equally big on landscape and portrait photos.
    """
    im = im.convert("RGB")
    W, H = im.size
    base = min(W, H * 4 / 3)
    margin = round(base * 0.025)

    # Badge: resized, 80 % opaque.
    bw = round(base * 0.08)
    badge = badge.convert("RGBA")
    badge = badge.resize((bw, round(badge.height * bw / badge.width)), Image.LANCZOS)
    badge.putalpha(badge.getchannel("A").point(lambda v: int(v * 0.8)))
    bx, by = W - margin - bw, H - margin - badge.height

    # Text: right edge a small gap left of the badge, centred on its height.
    font = ImageFont.truetype(str(font_path), round(base * 0.02))
    text = f"\u00a9 {author}"
    _check_glyphs(font, text)
    left, top, right, bottom = font.getbbox(text)
    tx = bx - round(base * 0.012) - (right - left)
    ty = by + (badge.height - (bottom - top)) // 2 - top

    # Draw on transparent layers: a blurred black shadow, white text, badge.
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).text((tx, ty), text, font=font, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(base * 0.003))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    layer = Image.alpha_composite(layer, shadow)
    ImageDraw.Draw(layer).text((tx, ty), text, font=font, fill=(255, 255, 255, 220))
    layer.alpha_composite(badge, (bx, by))
    return Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")


def _check_glyphs(font: ImageFont.FreeTypeFont, text: str) -> None:
    """Stop if the font cannot draw a letter (it would print an empty box).

    A missing letter is drawn with the font's "not defined" glyph, so it looks
    exactly like a code point no font has.
    """
    def shape(ch: str) -> bytes:
        return bytes(font.getmask(ch))
    notdef = shape("\U0010fffd")
    missing = sorted({ch for ch in text if not ch.isspace() and shape(ch) == notdef})
    if missing:
        raise ValueError(
            f"the watermark font has no letter for {' '.join(missing)} in {text!r}; "
            "write the name without it or add a font that has it"
        )


def gallery_jobs(content: dict) -> list[tuple[str, str, str]]:
    """(source, author, web image ref) for every place photo, in content order."""
    return [
        (ph["source"], ph["author"], gallery_ref(pl["slug"], ph["source"]))
        for pl in content.get("places", [])
        for ph in pl["photos"]
    ]


def run_gallery(content: dict, root: Path, out_dir: Path,
                badge: Image.Image, font_path: Path) -> list[Path]:
    """Write the watermarked sets for all place photos; delete leftovers.

    Sources are read from `root`, outputs go under `out_dir` (static/img).
    Files in places/<slug>/ that no photo produces, and folders of places no
    longer in content.yaml, are removed so they are not committed or served.
    """
    written: list[Path] = []
    keep_old: list[Path] = []
    for source, author, ref in gallery_jobs(content):
        out_stem = out_dir / ref.removeprefix("img/")
        try:
            with _open(root / source) as im:
                written += _responsive_image(
                    im.convert("RGB"), out_stem, GALLERY_WIDTHS,
                    finish=lambda small, a=author: watermark(small, a, badge, font_path),
                )
        except Exception as exc:  # one bad photo must not stop the rest
            print(f"WARNING: gallery {source} failed: {exc}", file=sys.stderr)
            # keep its previous files rather than deleting them as stale
            keep_old += out_stem.parent.glob(f"{out_stem.name}-*.webp")
    keep = set(written) | set(keep_old)
    places_dir = out_dir / "places"
    slugs = {pl["slug"] for pl in content.get("places", [])}
    if places_dir.is_dir():
        for folder in places_dir.iterdir():
            if not folder.is_dir():
                continue
            for f in folder.iterdir():
                if f.is_file() and (folder.name not in slugs or f not in keep):
                    f.unlink()
            if folder.name not in slugs and not any(folder.iterdir()):
                folder.rmdir()
    return written


def _report(paths: list[Path]) -> int:
    """Print each written file with its size; return the total in bytes."""
    total = 0
    for p in paths:
        size = p.stat().st_size
        total += size
        print(f"{p.relative_to(HERE)}  {size / 1024:.0f} KB")
    return total


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
    try:
        outs = run_gallery(load_content(HERE / "content.yaml"), EXPEDITION,
                           OUT_DIR, Image.open(BADGE), FONT)
        total += _report(outs)
    except Exception as exc:
        print(f"WARNING: gallery failed: {exc}", file=sys.stderr)
    print(f"Total: {total / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()
