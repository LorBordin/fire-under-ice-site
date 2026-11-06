"""Build the 2006 vs 2025 comparison images for the slider.

Both images share the same frame and the same orthophoto background, so the
page can slide one over the other. Inputs (read only, outside this repo):

- the brochure's KML tour, which georeferences each survey drawing
  (a GroundOverlay with a north/south/east/west box in degrees);
- the transparent survey PNGs in the brochure's files/ folder;
- the July 2026 drone orthophoto, a tiled KMZ "superoverlay": a zip of
  PNG tiles at several zoom levels, each tile with its own box in degrees.

Run with:  uv run make_comparison.py
Writes static/img/cmp-2006-<w>.webp and cmp-2025-<w>.webp.

The area is ~350 m across, so treating degrees as a flat grid (with the
east-west scale shrunk by cos(latitude)) is accurate to well under a pixel.
"""
import math
import re
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from prepare_images import BROCHURE, OUT_DIR, _responsive_image

TOUR = BROCHURE / "kverkfjoll_tour.kml"
ORTHO = Path.home() / "expeditions/Iceland/2026/maps/orthophoto_RGB_07_26.kmz"
ORTHO_LEVEL = 4          # tile pyramid level: ~2600 px across the frame
WIDTH = 2000             # output width in px
MARGIN = 0.06            # extra space around the two surveys, as a fraction
SURVEYS = {"cmp-2006": "s06", "cmp-2025": "s25"}   # output stem -> KML overlay id
# Site colours, as in the brochure legend: 2006 IceBlue, 2025 MagmaRed (rgb, opacity).
TINTS = {"cmp-2006": ((0x00, 0xC2, 0xFF), 1.0), "cmp-2025": ((0xFF, 0x45, 0x00), 0.8)}

Box = tuple[float, float, float, float]   # north, south, east, west


def _box(xml: str) -> Box:
    get = lambda k: float(re.search(rf"<{k}>([-\d.]+)</{k}>", xml).group(1))
    return get("north"), get("south"), get("east"), get("west")


def survey_overlays() -> dict[str, tuple[Path, Box]]:
    """KML overlay id -> (survey PNG, box), read from the brochure tour."""
    kml = TOUR.read_text(encoding="utf-8")
    out = {}
    for oid, body in re.findall(r'<GroundOverlay id="([^"]+)">(.*?)</GroundOverlay>', kml, re.S):
        href = re.search(r"<href>([^<]+)</href>", body).group(1)
        out[oid] = (BROCHURE / href, _box(body))
    return out


def frame(boxes: list[Box]) -> Box:
    """Smallest box holding all `boxes`, plus MARGIN on each side."""
    n = max(b[0] for b in boxes); s = min(b[1] for b in boxes)
    e = max(b[2] for b in boxes); w = min(b[3] for b in boxes)
    dy, dx = (n - s) * MARGIN, (e - w) * MARGIN
    return n + dy, s - dy, e + dx, w - dx


class Canvas:
    """Maps degrees to pixels for one frame."""

    def __init__(self, box: Box, width: int):
        self.n, self.s, self.e, self.w = box
        lat = math.radians((self.n + self.s) / 2)
        metres_x = (self.e - self.w) * 111_320 * math.cos(lat)
        metres_y = (self.n - self.s) * 111_320
        self.width = width
        self.height = round(width * metres_y / metres_x)
        self.metres_per_px = metres_x / width

    def rect(self, box: Box) -> tuple[int, int, int, int]:
        n, s, e, w = box
        x0 = (w - self.w) / (self.e - self.w) * self.width
        x1 = (e - self.w) / (self.e - self.w) * self.width
        y0 = (self.n - n) / (self.n - self.s) * self.height
        y1 = (self.n - s) / (self.n - self.s) * self.height
        return round(x0), round(y0), round(x1), round(y1)

    def paste(self, base: Image.Image, im: Image.Image, box: Box) -> None:
        x0, y0, x1, y1 = self.rect(box)
        if x1 <= 0 or y1 <= 0 or x0 >= self.width or y0 >= self.height:
            return
        im = im.convert("RGBA").resize((max(1, x1 - x0), max(1, y1 - y0)), Image.LANCZOS)
        base.alpha_composite(im, (x0, y0)) if x0 >= 0 and y0 >= 0 else base.paste(im, (x0, y0), im)


def orthophoto(canvas: Canvas) -> Image.Image:
    """Stitch the orthophoto tiles of ORTHO_LEVEL that touch the frame."""
    base = Image.new("RGBA", (canvas.width, canvas.height), (13, 13, 13, 255))
    with zipfile.ZipFile(ORTHO) as z:
        for name in z.namelist():
            if not (name.startswith(f"{ORTHO_LEVEL}/") and name.endswith(".kml")):
                continue
            box = _box(z.read(name).decode())
            with z.open(name[:-4] + ".png") as f:
                canvas.paste(base, Image.open(f), box)
    # Grey it down so the survey colours carry the picture, as in the brochure.
    rgb = ImageEnhance.Color(base.convert("RGB")).enhance(0.35)
    rgb = ImageEnhance.Brightness(rgb).enhance(0.8)
    return rgb.convert("RGBA")


def tint(im: Image.Image, rgb: tuple[int, int, int], opacity: float) -> Image.Image:
    """Paint every visible pixel of `im` in one colour, keeping its transparency."""
    alpha = im.convert("RGBA").getchannel("A").point(lambda a: round(a * opacity))
    out = Image.new("RGBA", im.size, rgb + (0,))
    out.putalpha(alpha)
    return out


def scale_bar(im: Image.Image, canvas: Canvas, metres: int = 50) -> None:
    """Draw a white `metres` scale bar and a north arrow in the corners."""
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default(size=round(canvas.width / 55))
    px = metres / canvas.metres_per_px
    x, y, t = canvas.width * 0.04, canvas.height * 0.95, max(3, canvas.width // 400)
    d.rectangle([x, y - t, x + px, y], fill="white")
    d.text((x, y - 3 * t), f"{metres} m", fill="white", font=font, anchor="ls")
    ax, ay, h = canvas.width * 0.95, canvas.height * 0.05, canvas.width / 40
    d.polygon([(ax, ay), (ax - h / 3, ay + h), (ax + h / 3, ay + h)], fill="white")
    d.text((ax, ay + h * 1.15), "N", fill="white", font=font, anchor="mt")


def main() -> None:
    overlays = survey_overlays()
    used = [overlays[oid] for oid in SURVEYS.values()]
    canvas = Canvas(frame([box for _, box in used]), WIDTH)
    print(f"Frame {canvas.width}x{canvas.height} px, {canvas.metres_per_px:.2f} m/px")
    base = orthophoto(canvas)
    for stem, oid in SURVEYS.items():
        png, box = overlays[oid]
        im = base.copy()
        canvas.paste(im, tint(Image.open(png), *TINTS[stem]), box)
        scale_bar(im, canvas)
        for p in _responsive_image(im.convert("RGB"), OUT_DIR / stem):
            print(f"  {p.relative_to(OUT_DIR.parent.parent)}  {p.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
