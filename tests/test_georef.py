"""Tests for georef.py: finding the KML frame in a Google Earth export and unwarping it."""
import pytest

np = pytest.importorskip("numpy")   # only in the `assets` group, not in CI
from PIL import Image, ImageDraw

from georef import frame_corners, frame_curves, unwarp

# A bent four-sided frame, like Google Earth draws it over terrain.
NW, NE, SE, SW = (100, 80), (900, 60), (880, 620), (120, 640)


def _bend(p, q, n=40, amp=6):
    """Points from p to q with a sideways bump in the middle."""
    out = []
    for i in range(n + 1):
        t = i / n
        x, y = p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t
        dx, dy = q[1] - p[1], -(q[0] - p[0])
        k = amp * np.sin(np.pi * t) / np.hypot(dx, dy)
        out.append((x + dx * k, y + dy * k))
    return out


def _mask():
    im = Image.new("L", (1000, 700))
    d = ImageDraw.Draw(im)
    for p, q in [(NW, NE), (NE, SE), (SE, SW), (SW, NW)]:
        d.line(_bend(p, q), fill=255, width=4)
    # Crosses: arms continue past each corner along both edges.
    for (x, y) in [NW, NE, SE, SW]:
        d.line([(x - 40, y), (x + 40, y)], fill=255, width=4)
        d.line([(x, y - 40), (x, y + 40)], fill=255, width=4)
    return np.asarray(im) > 0


def test_corners_found_within_two_pixels():
    found = frame_corners(frame_curves(_mask()))
    for got, want in zip(found, [NW, NE, SE, SW]):
        assert np.hypot(got[0] - want[0], got[1] - want[1]) < 2


def test_unwarp_maps_the_frame_onto_the_output():
    # A source image whose colour encodes position: red = x/4, green = y/4.
    xs, ys = np.meshgrid(np.arange(1000), np.arange(700))
    src = Image.fromarray(np.dstack([xs // 4, ys // 4, xs * 0]).astype(np.uint8))
    out = np.asarray(unwarp(src, frame_curves(_mask()), (400, 300)), np.int16)
    # The output's top-left pixel comes from near NW, bottom-right from near SE.
    assert abs(out[0, 0, 0] - NW[0] // 4) <= 2 and abs(out[0, 0, 1] - NW[1] // 4) <= 2
    assert abs(out[-1, -1, 0] - SE[0] // 4) <= 2 and abs(out[-1, -1, 1] - SE[1] // 4) <= 2
