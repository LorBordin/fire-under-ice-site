"""Fit a Google Earth screenshot to the slider frame.

Google Earth Pro cannot export a georeferenced image, so make_comparison.py
writes a KML of the slider frame (a magenta outline with a cross at each
corner) and Lorenzo saves the same view twice, with and without it. The
pixels that differ are the outline. Its four edges are not straight:
Google Earth draws in perspective over terrain, so relief bends them (and
the imagery) by a few metres. We therefore trace each edge as a curve and
map the inside with a Coons patch, which blends the four curves, instead of
a single four-corner (projective) fit.

Needs numpy (the `assets` dependency group).
"""
from typing import NamedTuple

import numpy as np
from PIL import Image

Curve = tuple[np.ndarray, np.ndarray]   # (t, s): s as a function of t, t increasing


class Curves(NamedTuple):
    top: Curve      # y(x)
    bottom: Curve   # y(x)
    left: Curve     # x(y)
    right: Curve    # x(y)


def outline_mask(with_frame: Image.Image, without_frame: Image.Image) -> np.ndarray:
    """True where the magenta outline was drawn: the two exports differ, and the pixel is magenta."""
    a = np.asarray(with_frame.convert("RGB"), np.int16)
    b = np.asarray(without_frame.convert("RGB"), np.int16)
    if a.shape != b.shape:
        raise ValueError(f"the two exports differ in size: {a.shape} vs {b.shape}")
    differs = np.abs(a - b).sum(axis=2) > 120
    magenta = (a[..., 0] > 150) & (a[..., 2] > 150) & (a[..., 1] < 120)
    mask = differs & magenta
    if mask.sum() < 1000:
        raise ValueError("no frame found: are the two exports of the same view, one with the KML on?")
    return mask


def _edge(mask: np.ndarray, axis: int, first_half: bool) -> Curve:
    """Trace one edge. axis=0: a near-horizontal edge, sampled per column (y of x).

    In each column (row for axis=1) of the chosen half, a near-horizontal line
    leaves a short run of pixels; a near-vertical line or a cross arm leaves a
    long one. Keep the short runs only, then drop points far from their neighbours.
    """
    m = mask if axis == 0 else mask.T
    half = m.shape[0] // 2
    part = m[:half] if first_half else m[half:]
    offset = 0 if first_half else half
    counts = part.sum(axis=0)
    hit = counts > 0
    if not hit.any():
        raise ValueError("an edge of the frame is missing from the export")
    thickness = np.median(counts[hit])
    keep = hit & (counts <= 3 * thickness)
    cols = np.nonzero(keep)[0]
    rows = np.arange(part.shape[0])[:, None]
    centre = (rows * part[:, cols]).sum(axis=0) / counts[cols] + offset
    # Outliers: more than 3 thicknesses away from the running median of 31 neighbours.
    pad = np.pad(centre, 15, mode="edge")
    med = np.array([np.median(pad[i:i + 31]) for i in range(len(centre))])
    good = np.abs(centre - med) <= 3 * max(thickness, 1)
    return cols[good].astype(float), centre[good]


def frame_curves(mask: np.ndarray) -> Curves:
    return Curves(
        top=_edge(mask, 0, True), bottom=_edge(mask, 0, False),
        left=_edge(mask, 1, True), right=_edge(mask, 1, False),
    )


def _at(curve: Curve, t: np.ndarray | float) -> np.ndarray:
    return np.interp(t, *curve)


def _meet(horizontal: Curve, vertical: Curve) -> tuple[float, float]:
    """Where a y(x) curve crosses an x(y) curve (they are near perpendicular)."""
    y = float(np.median(horizontal[1]))
    for _ in range(50):
        x = float(_at(vertical, y))
        y = float(_at(horizontal, x))
    return x, y


def frame_corners(c: Curves) -> list[tuple[float, float]]:
    """(x, y) of the NW, NE, SE, SW corners in the export."""
    return [_meet(c.top, c.left), _meet(c.top, c.right),
            _meet(c.bottom, c.right), _meet(c.bottom, c.left)]


def _coons(c: Curves, corners, u: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Source (x, y) for frame coordinates u (west->east) and v (north->south), both 0..1."""
    nw, ne, se, sw = (np.array(p) for p in corners)
    tx = nw[0] + (ne[0] - nw[0]) * u; ty = _at(c.top, tx)
    bx = sw[0] + (se[0] - sw[0]) * u; by = _at(c.bottom, bx)
    ly = nw[1] + (sw[1] - nw[1]) * v; lx = _at(c.left, ly)
    ry = ne[1] + (se[1] - ne[1]) * v; rx = _at(c.right, ry)
    corner = lambda k: ((1 - u) * (1 - v) * nw[k] + u * (1 - v) * ne[k]
                        + (1 - u) * v * sw[k] + u * v * se[k])
    x = (1 - v) * tx + v * bx + (1 - u) * lx + u * rx - corner(0)
    y = (1 - v) * ty + v * by + (1 - u) * ly + u * ry - corner(1)
    return x, y


def unwarp(src: Image.Image, c: Curves, size: tuple[int, int], cells: int = 48) -> Image.Image:
    """The inside of the frame, resampled to a size[0] x size[1] north-up image."""
    corners = frame_corners(c)
    w, h = size[0] * 2, size[1] * 2            # work at 2x, then shrink: less aliasing
    us, vs = np.linspace(0, 1, cells + 1), np.linspace(0, 1, cells + 1)
    gu, gv = np.meshgrid(us, vs)
    gx, gy = _coons(c, corners, gu, gv)
    mesh = []
    for j in range(cells):
        for i in range(cells):
            box = (round(us[i] * w), round(vs[j] * h), round(us[i + 1] * w), round(vs[j + 1] * h))
            quad = (gx[j, i], gy[j, i], gx[j + 1, i], gy[j + 1, i],          # NW, SW
                    gx[j + 1, i + 1], gy[j + 1, i + 1], gx[j, i + 1], gy[j, i + 1])  # SE, NE
            mesh.append((box, tuple(float(q) for q in quad)))
    big = src.convert("RGB").transform((w, h), Image.Transform.MESH, mesh, Image.Resampling.BICUBIC)
    return big.resize(size, Image.Resampling.LANCZOS)
