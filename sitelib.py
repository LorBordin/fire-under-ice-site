"""Pure logic for the site generator: no printing, no file output.

Everything here takes plain Python data (dicts and lists loaded from
content.yaml) and returns plain data, which makes it easy to test.
build.py is the part that wires these functions to the real files.
"""
import copy
import re
from pathlib import Path
from typing import Any, NamedTuple

import yaml
from PIL import Image
from markupsafe import Markup, escape

# Keys that must be present (and non-empty) in each kind of entry.
# A dotted name such as "press.articles" means "each item of the list
# content['press']['articles']"; a plain list section such as "years"
# is checked item by item as well.
REQUIRED: dict[str, list[str]] = {
    "site": ["title", "url", "description", "contact_email"],
    "hero": ["title", "subtitle", "years", "image", "image_alt"],
    "project": ["kicker", "title", "paragraphs"],
    # one {kicker, title, intro?} per section; the page headings live here
    "headings": ["years", "watch", "science", "team", "press", "partners", "contact"],
    "headings.years": ["kicker", "title"],
    "headings.watch": ["kicker", "title"],
    "headings.science": ["kicker", "title"],
    "headings.team": ["kicker", "title"],
    "headings.press": ["kicker", "title"],
    "headings.partners": ["kicker", "title"],
    "headings.contact": ["kicker", "title"],
    "comparison": ["before", "before_alt", "after", "after_alt", "caption"],
    "map": ["image", "image_alt", "caption"],
    "science": ["title", "text"],
    "press.tv": ["title", "outlet", "url"],
    "credits": [],
    "years": ["year", "label", "place", "text", "image", "image_alt"],
    "video": ["youtube_id", "title", "thumbnail", "thumbnail_alt"],
    "csi": ["name", "logo", "blurb"],
    "team.members": ["name", "role", "line", "photo"],
    "partners": ["name", "logo"],
    "sponsors": ["name", "logo"],
    "press.articles": ["year", "title", "byline"],
    "press.talks": ["year", "venue", "place", "title"],
}

# Sections that may be absent or empty (an empty list is how "no sponsors yet" is written).
OPTIONAL_SECTIONS = ("sponsors",)

# Phrases we never want on the site (compared in lowercase).
FORBIDDEN: tuple[str, ...] = ("heart of europe", "2000 mw", "kinetic trigger", "extremophile")

# Any dict key with one of these names holds an image path.
IMAGE_KEYS = ("image", "photo", "logo", "thumbnail", "before", "after")
# These get alt text from a sibling key "<key>_alt"; photo/logo use "name".
ALT_FROM_SIBLING = ("image", "thumbnail", "before", "after")

RESPONSIVE_WIDTHS = (800, 1400, 2000)


def load_content(path: Path) -> dict:
    """Read the YAML content file (UTF-8) into nested dicts and lists."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------- images

class ImageInfo(NamedTuple):
    src: str      # URL of the largest file, relative: "static/img/..."
    srcset: str   # "static/img/x-800.webp 800w, ..." or "" for a single file
    width: int    # pixel size of the largest file
    height: int


def image_info(static_dir: Path, ref: str) -> ImageInfo:
    """Look up an image reference from content.yaml.

    "img/team/x.webp" (has an extension) is one file.
    "img/p01-cover" (no extension) is a set x-800.webp, x-1400.webp, ...
    Raises FileNotFoundError if nothing matches.
    """
    if Path(ref).suffix:
        files = [(None, static_dir / ref)]
        if not files[0][1].is_file():
            files = []
    else:
        files = [
            (w, static_dir / f"{ref}-{w}.webp")
            for w in RESPONSIVE_WIDTHS
            if (static_dir / f"{ref}-{w}.webp").is_file()
        ]
    if not files:
        raise FileNotFoundError(f"image not found: {ref}")

    largest = files[-1][1]
    with Image.open(largest) as im:
        width, height = im.size

    def url(p: Path) -> str:
        return "static/" + p.relative_to(static_dir).as_posix()

    srcset = ""
    if files[0][0] is not None:
        srcset = ", ".join(f"{url(p)} {w}w" for w, p in files)
    return ImageInfo(url(largest), srcset, width, height)


# ------------------------------------------------------------ validation

def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == []


def _lookup(content: dict, dotted: str) -> list[tuple[str, dict]]:
    """Find the dicts that REQUIRED[dotted] applies to, with their YAML paths.

    Returns [(path, dict), ...]. Missing sections give an empty list here;
    a missing *top-level* section is reported separately by validate().
    """
    parts = dotted.split(".")
    # Each "node" is (path-so-far, value); expand one path part at a time.
    nodes: list[tuple[str, Any]] = [("", content)]
    for part in parts:
        nxt = []
        for path, node in nodes:
            # Lists on the way (e.g. team -> groups) are walked item by item.
            items = (
                [(f"{path}[{i}]", n) for i, n in enumerate(node)]
                if isinstance(node, list) else [(path, node)]
            )
            for p, n in items:
                if isinstance(n, dict) and part in n:
                    nxt.append((f"{p}.{part}" if p else part, n[part]))
        nodes = nxt
    result = []
    for path, node in nodes:
        if isinstance(node, list):
            result += [(f"{path}[{i}]", n) for i, n in enumerate(node) if isinstance(n, dict)]
        elif isinstance(node, dict):
            result.append((path, node))
    return result


def validate(content: dict, static_dir: Path) -> list[str]:
    """Return every problem found, as "<yaml.path>: <message>". [] means valid."""
    errors: list[str] = []

    # 1. Required fields.
    for dotted, keys in REQUIRED.items():
        top = dotted.split(".")[0]
        if top in OPTIONAL_SECTIONS and _is_blank(content.get(top)):
            continue
        if top not in content or _is_blank(content[top]):
            errors.append(f"{top}: missing")
            continue
        for path, entry in _lookup(content, dotted):
            for key in keys:
                if _is_blank(entry.get(key)):
                    errors.append(f"{path}.{key}: missing")

    # 2. Walk the whole tree for TODO, forbidden phrases, images and alts.
    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                child = f"{path}.{key}" if path else str(key)
                if key in IMAGE_KEYS and isinstance(value, str):
                    check_image(node, key, value, child, path)
                walk(value, child)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                walk(value, f"{path}[{i}]")
        elif isinstance(node, str):
            if "TODO" in node:
                errors.append(f"{path}: contains TODO")
            lowered = node.lower()
            for phrase in FORBIDDEN:
                if phrase in lowered:
                    errors.append(f"{path}: forbidden phrase: {phrase}")

    def check_image(entry: dict, key: str, ref: str, path: str, parent: str) -> None:
        try:
            image_info(static_dir, ref)
        except FileNotFoundError:
            errors.append(f"{path}: file not found: {ref}")
        # Alt text: from "<key>_alt", or from the entry's name for photo/logo.
        if key in ALT_FROM_SIBLING:
            alt_key = f"{key}_alt"
        else:
            alt_key = "name"
        if _is_blank(entry.get(alt_key)):
            errors.append(f"{parent + '.' if parent else ''}{alt_key}: missing")

    walk(content, "")

    # The same problem can be found twice (e.g. a missing alt is both
    # "required" and "alt text"); keep the first of each, in order.
    return list(dict.fromkeys(errors))


# --------------------------------------------------------------- consent

def filter_consented(content: dict) -> tuple[dict, list[str]]:
    """Return (copy of content without non-consented people/partners, skipped names).

    Only a YAML true value counts (`consent: true`; note YAML also reads an
    unquoted `yes`/`on` as true). A missing key, `false`, 1, a quoted "yes" or a
    typo such as `concent` all mean "hidden", so a mistake never publishes someone.
    """
    out = copy.deepcopy(content)
    skipped: list[str] = []

    def keep(entries: list) -> list:
        kept = []
        for e in entries:
            if e.get("consent") is True:
                kept.append(e)
            else:
                skipped.append(str(e.get("name", "?")))
        return kept

    groups = out.get("team") or []
    for group in groups:
        group["members"] = keep(group.get("members") or [])
    out["team"] = [g for g in groups if g["members"]]  # drop empty groups
    out["partners"] = keep(out.get("partners") or [])
    out["sponsors"] = keep(out.get("sponsors") or [])
    return out, skipped


# ---------------------------------------------------------------- italics

_ITALIC = re.compile(r"\*([^*]+)\*")


def inline_md(text: str) -> Markup:
    """Escape all HTML, then turn *x* into <em>x</em>.

    Escaping comes first, so the only markup in the result is our own <em>.
    """
    escaped = str(escape(text))
    return Markup(_ITALIC.sub(r"<em>\1</em>", escaped))
