"""Build the web 3D model (static/model/<name>.glb) from the ODM photogrammetry OBJ.

The ODM model is far too heavy for a web page (1.5 M triangles, 115 textures,
~400 MB). This script, run by hand once:

1. simplifies the mesh to FACES triangles, keeping the texture coordinates
   (MeshLab's texture-aware quadric edge collapse, via pymeshlab);
2. packs ODM's textures, all shrunk by the same factor, into one square
   atlas of ATLAS px, and moves the texture coordinates to match;
3. moves the model to the origin (ODM stores it in UTM 28N, offset in
   odm_georeferencing_model_geo.txt), turns it to glTF axes (+Y up, north = -Z)
   and writes a single .glb file: unlit material, JPEG texture embedded;
4. prints where the cave marker goes (centre of the 2025 survey in the
   brochure KML, converted to the model's coordinates), for content.yaml.

Run with:  uv run --group assets make_model.py
(pymeshlab and numpy are in the separate `assets` group, so the site build,
the tests and GitHub Actions never install them.)
"""
import io
import json
import re
import struct
import sys
import tempfile
from pathlib import Path

import numpy as np
import pymeshlab
from PIL import Image

from geo import utm
from make_comparison import survey_overlays

HERE = Path(__file__).parent
SRC = Path.home() / "expeditions/Iceland/2026/fotogrammetria/runs/fly_2_v2-mesh12/model_3d/odm_textured_model_geo.obj"
OUT = HERE / "static" / "model" / "hveradalur-2026.glb"
ODM_OFFSET = SRC.parent / "odm_georeferencing_model_geo.txt"   # "WGS84 UTM 28N" / "<east> <north>"
CAVE_OVERLAY = "s25"  # the 2025 survey in the brochure KML marks the cave
FACES = 300_000       # triangles kept
ATLAS = 4096          # atlas side in px (4096 is safe on every phone GPU)
PAD = 2               # px of empty space around each packed texture
JPEG_QUALITY = 85


# ------------------------------------------------------------- 1. simplify

def simplify(src: Path, faces: int, tmp: Path) -> Path:
    """Decimate `src` to `faces` triangles; return the path of the saved OBJ."""
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(str(src))
    print(f"Loaded {ms.current_mesh().face_number():,} triangles")
    ms.meshing_decimation_quadric_edge_collapse_with_texture(
        targetfacenum=faces, qualitythr=0.5, preserveboundary=True,
        boundaryweight=1.0, optimalplacement=True, preservenormal=True,
        planarquadric=True,
    )
    ms.meshing_remove_connected_component_by_face_number(mincomponentsize=50)
    print(f"Simplified to {ms.current_mesh().face_number():,} triangles")
    out = tmp / "low.obj"
    # Textures are not rewritten: we read the originals next to SRC.
    ms.save_current_mesh(str(out), save_wedge_texcoord=True, save_textures=False)
    return out


def read_obj(path: Path):
    """Return (positions Nx3, uvs Mx2, faces Fx3x2 [pos idx, uv idx], material per face, material names)."""
    v, vt, faces, mats, names = [], [], [], [], {}
    current = -1
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("v "):
                v.append(line.split()[1:4])
            elif line.startswith("vt "):
                vt.append(line.split()[1:3])
            elif line.startswith("usemtl "):
                current = names.setdefault(line.split()[1], len(names))
            elif line.startswith("f "):
                corners = [c.split("/") for c in line.split()[1:4]]
                faces.append([[int(c[0]) - 1, int(c[1]) - 1] for c in corners])
                mats.append(current)
    if min(mats, default=0) < 0:
        sys.exit("OBJ face without material: cannot texture it")
    order = sorted(names, key=names.get)
    return (np.array(v, np.float64), np.array(vt, np.float64),
            np.array(faces, np.int64), np.array(mats, np.int64), order)


def texture_files(mtl: Path, folder: Path) -> dict[str, Path]:
    """Material name -> texture image in `folder`, from a .mtl file.

    MeshLab renames materials (material_0, ...) when it saves, so we read
    the .mtl it wrote next to the simplified OBJ.
    """
    out, name = {}, None
    for line in mtl.read_text(encoding="utf-8").splitlines():
        if line.startswith("newmtl "):
            name = line.split()[1]
        elif line.startswith("map_Kd ") and name:
            out[name] = folder / Path(line.split(maxsplit=1)[1].strip()).name
    return out


# ---------------------------------------------------------------- 2. pack

def shelf_pack(sizes: list[int], side: int, pad: int) -> list[tuple[int, int]] | None:
    """Place squares (largest first) in rows of a side x side square; None if they don't fit."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i])
    pos: list[tuple[int, int] | None] = [None] * len(sizes)
    x = y = row_h = 0
    for i in order:
        s = sizes[i] + 2 * pad
        if x + s > side:                    # next row
            x, y, row_h = 0, y + row_h, 0
        if y + s > side or s > side:
            return None
        pos[i] = (x + pad, y + pad)
        x += s
        row_h = max(row_h, s)
    return pos  # type: ignore[return-value]


def pack(images: list[Path], side: int, pad: int):
    """Largest common scale at which every texture fits; returns (scale, sizes, positions)."""
    full = [Image.open(p).size[0] for p in images]   # ODM textures are square
    lo, hi = 0.0, 1.0
    best = None
    for _ in range(30):                     # bisection on the scale
        mid = (lo + hi) / 2
        sizes = [max(8, round(s * mid)) for s in full]
        pos = shelf_pack(sizes, side, pad)
        if pos:
            lo, best = mid, (mid, sizes, pos)
        else:
            hi = mid
    if not best:
        sys.exit("textures do not fit in the atlas at any scale")
    return best


def build_atlas(images: list[Path], sizes, pos, side: int) -> Image.Image:
    atlas = Image.new("RGB", (side, side), (40, 40, 40))
    for p, s, (x, y) in zip(images, sizes, pos):
        with Image.open(p) as im:
            atlas.paste(im.convert("RGB").resize((s, s), Image.LANCZOS), (x, y))
    return atlas


# ------------------------------------------------------------- 3. write glb

def model_centre(p: np.ndarray) -> np.ndarray:
    """The point that becomes the glTF origin: middle of the box, at its lowest height."""
    centre = (p.min(0) + p.max(0)) / 2
    centre[2] = p[:, 2].min()                # ground at y=0
    return centre


def to_gltf_axes(p: np.ndarray, centre: np.ndarray) -> np.ndarray:
    """OBJ (east, north, up) -> glTF (x=east, y=up, z=south), moved so `centre` is the origin."""
    q = p - centre
    return np.stack([q[:, 0], q[:, 2], -q[:, 1]], axis=1).astype(np.float32)


def cave_marker(v: np.ndarray, centre: np.ndarray) -> np.ndarray:
    """glTF position of the cave: centre of the 2025 survey (brochure KML), on the model surface."""
    north, south, east, west = survey_overlays()[CAVE_OVERLAY][1]
    zone_line, offset_line = ODM_OFFSET.read_text().split("\n")[:2]
    zone = int(re.search(r"UTM (\d+)N", zone_line).group(1))
    off_e, off_n = (float(x) for x in offset_line.split())
    e, n = utm((north + south) / 2, (east + west) / 2, zone)
    x, y = e - off_e, n - off_n
    near = np.hypot(v[:, 0] - x, v[:, 1] - y) < 5      # vertices within 5 m
    if not near.any():
        sys.exit(f"the cave ({x:.0f}, {y:.0f}) is outside the model")
    z = v[near, 2].max()                                 # the surface, not the lake bed
    return to_gltf_axes(np.array([[x, y, z]]), centre)[0]


def write_glb(path: Path, pos: np.ndarray, uv: np.ndarray, idx: np.ndarray, jpeg: bytes) -> None:
    def align(b: bytes, fill: bytes = b"\0") -> bytes:
        return b + fill * (-len(b) % 4)

    chunks = [pos.tobytes(), uv.astype(np.float32).tobytes(), idx.astype(np.uint32).tobytes(), jpeg]
    views, blob = [], b""
    for c in chunks:
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(c)})
        blob += align(c)
    views[0]["target"] = views[1]["target"] = 34962   # ARRAY_BUFFER
    views[2]["target"] = 34963                          # ELEMENT_ARRAY_BUFFER
    gltf = {
        "asset": {"version": "2.0", "generator": "make_model.py (Fire Under Ice)"},
        "extensionsUsed": ["KHR_materials_unlit"],
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Efri Hveradalur 2026"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "TEXCOORD_0": 1}, "indices": 2, "material": 0}]}],
        "materials": [{
            "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0, "roughnessFactor": 1},
            "extensions": {"KHR_materials_unlit": {}}, "doubleSided": True,
        }],
        "textures": [{"source": 0, "sampler": 0}],
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071}],
        "images": [{"bufferView": 3, "mimeType": "image/jpeg"}],
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": len(pos), "type": "VEC3",
             "min": pos.min(0).tolist(), "max": pos.max(0).tolist()},
            {"bufferView": 1, "componentType": 5126, "count": len(uv), "type": "VEC2"},
            {"bufferView": 2, "componentType": 5125, "count": idx.size, "type": "SCALAR"},
        ],
        "bufferViews": views,
        "buffers": [{"byteLength": len(blob)}],
    }
    js = align(json.dumps(gltf, separators=(",", ":")).encode(), b" ")
    total = 12 + 8 + len(js) + 8 + len(blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + blob)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        low = simplify(SRC, FACES, Path(tmp))
        v, vt, faces, mats, names = read_obj(low)
        tex = texture_files(low.with_suffix(".obj.mtl") if low.with_suffix(".obj.mtl").exists()
                            else low.with_suffix(".mtl"), SRC.parent)

    images = [tex[n] for n in names]
    scale, sizes, pos = pack(images, ATLAS, PAD)
    print(f"Packing {len(images)} textures at {scale:.3f}x into {ATLAS}x{ATLAS}")
    atlas = build_atlas(images, sizes, pos, ATLAS)

    # Each triangle corner -> (position index, atlas uv). OBJ v is bottom-up, glTF v top-down.
    corner_pos = faces[:, :, 0].reshape(-1)
    corner_uv = vt[faces[:, :, 1].reshape(-1)]
    mat = np.repeat(mats, 3)
    off = np.array(pos, np.float64)[mat]
    size = np.array(sizes, np.float64)[mat]
    u = (off[:, 0] + np.clip(corner_uv[:, 0], 0, 1) * size) / ATLAS
    w = (off[:, 1] + (1 - np.clip(corner_uv[:, 1], 0, 1)) * size) / ATLAS

    # Merge corners that share both position and uv into one glTF vertex.
    key = np.stack([corner_pos.astype(np.float64), u, w], axis=1)
    uniq, inverse = np.unique(key, axis=0, return_inverse=True)
    centre = model_centre(v)
    positions = to_gltf_axes(v, centre)[uniq[:, 0].astype(np.int64)]
    uvs = uniq[:, 1:3]
    print(f"{len(positions):,} vertices, {len(faces):,} triangles")

    buf = io.BytesIO()
    atlas.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=False)
    write_glb(OUT, positions, uvs, inverse.reshape(-1), buf.getvalue())
    print(f"Wrote {OUT.relative_to(HERE)}  {OUT.stat().st_size / 1e6:.1f} MB "
          f"(texture {len(buf.getvalue()) / 1e6:.1f} MB)")
    cave = cave_marker(v, centre)
    print("Cave marker, for content.yaml:")
    print(f'    model_marker: "{cave[0]:.1f}m {cave[1]:.1f}m {cave[2]:.1f}m"')


if __name__ == "__main__":
    main()
