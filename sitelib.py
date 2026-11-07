"""Pure logic for the site generator: no printing, no file output.

Everything here takes plain Python data (dicts and lists loaded from
content.yaml) and returns plain data, which makes it easy to test.
build.py is the part that wires these functions to the real files.
"""
import copy
import re
import unicodedata
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
    "comparison": ["caption", "backgrounds"],
    # the first background is the default (and the only one without JavaScript)
    "comparison.backgrounds": ["label", "before", "before_alt", "after", "after_alt", "credit"],
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
    # Place galleries (one page each) and the In the field section.
    "places": ["slug", "name", "years", "teaser", "intro", "photos"],
    "places.photos": ["source", "author", "caption", "alt"],
    "field": ["title", "text", "image", "image_alt", "credit"],
}

# Sections that may be absent or empty (an empty list is how "no sponsors yet" is written).
OPTIONAL_SECTIONS = ("sponsors", "places", "field")

# Phrases we never want on the site (compared in lowercase).
FORBIDDEN: tuple[str, ...] = ("heart of europe", "2000 mw", "kinetic trigger", "extremophile")

# Any dict key with one of these names holds an image path.
IMAGE_KEYS = ("image", "photo", "logo", "thumbnail", "before", "after", "figure")
# These get alt text from a sibling key "<key>_alt"; photo/logo use "name".
ALT_FROM_SIBLING = ("image", "thumbnail", "before", "after", "figure")

# Any dict key with one of these names holds a plain file path under static/ (no alt text).
FILE_KEYS = ("model",)

RESPONSIVE_WIDTHS = (400, 800, 1400, 2000)


# Place slugs become folder names: /torfa/ -> _site/torfa/index.html.
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
RESERVED_SLUGS = ("static",)
MAX_FEATURED = 3


# Letters that have no accent-free form in Unicode: spelled out first.
_SPELL_OUT = str.maketrans({"ð": "d", "þ": "th", "æ": "ae", "ø": "o", "ß": "ss", "œ": "oe", "ł": "l", "đ": "d"})


def slugify(text: str) -> str:
    """"Copia di Vatnajökull (113)" -> "copia-di-vatnajokull-113", "Þórsmörk" -> "thorsmork"."""
    decomposed = unicodedata.normalize("NFKD", text.lower().translate(_SPELL_OUT))
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")


def gallery_ref(slug: str, source: str) -> str:
    """The web image of a gallery photo, e.g. "img/places/torfa/rimg0247".

    Used by prepare_images.py (to write it) and by the templates (to show it),
    so the two always agree.
    """
    return f"img/places/{slug}/{slugify(Path(source).stem)}"


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


def file_size(static_dir: Path, ref: str) -> str:
    """Size of a file under static/, for people: "11.5 MB"."""
    return f"{(static_dir / ref).stat().st_size / 1e6:.1f} MB"


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
                if key in FILE_KEYS and isinstance(value, str) and not (static_dir / value).is_file():
                    errors.append(f"{child}: file not found: {value}")
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
    errors += _validate_places(content, static_dir)

    # The same problem can be found twice (e.g. a missing alt is both
    # "required" and "alt text"); keep the first of each, in order.
    return list(dict.fromkeys(errors))


def _validate_places(content: dict, static_dir: Path) -> list[str]:
    """Rules for places and field that the generic checks above cannot express."""
    errors: list[str] = []
    headings = content.get("headings") or {}
    for section in ("places", "field"):
        if not _is_blank(content.get(section)) and _is_blank(headings.get(section)):
            errors.append(f"headings.{section}: missing")

    places = content.get("places") or []
    seen_slugs: set[str] = set()
    used_refs: set[str] = set()
    for i, pl in enumerate(places):
        if not isinstance(pl, dict):
            continue
        slug = pl.get("slug")
        if isinstance(slug, str) and slug:
            if not SLUG_RE.match(slug):
                errors.append(f"places[{i}].slug: use lowercase letters, digits and hyphens only: {slug}")
            elif slug in RESERVED_SLUGS:
                errors.append(f"places[{i}].slug: reserved name: {slug}")
            elif slug in seen_slugs:
                errors.append(f"places[{i}].slug: used twice: {slug}")
            seen_slugs.add(slug)
        photos = [p for p in (pl.get("photos") or []) if isinstance(p, dict)]
        if not photos:
            continue

        covers = sum(1 for p in photos if p.get("cover") is True)
        featured = sum(1 for p in photos if p.get("featured") is True)
        if covers != 1:
            errors.append(f"places[{i}]: needs exactly one photo with cover: true (found {covers})")
        if featured != MAX_FEATURED:
            errors.append(f"places[{i}]: needs exactly {MAX_FEATURED} photos with featured: true (found {featured})")
        if any(p.get("cover") is True and p.get("featured") is True for p in photos):
            errors.append(f"places[{i}]: a photo cannot be both cover and featured")

        if not (isinstance(slug, str) and SLUG_RE.match(slug)):
            continue
        stems: dict[str, int] = {}
        for j, ph in enumerate(photos):
            source = ph.get("source")
            if not isinstance(source, str) or not source:
                continue
            ref = gallery_ref(slug, source)
            if not slugify(Path(source).stem):
                errors.append(
                    f"places[{i}].photos[{j}].source: the file name gives an empty image name; "
                    "rename the original with some letters or digits"
                )
                continue
            if ref in stems:
                errors.append(
                    f"places[{i}].photos[{j}]: same image name as photos[{stems[ref]}] "
                    f"({Path(ref).name}); rename one source file"
                )
                continue
            stems[ref] = j
            try:
                image_info(static_dir, ref)
            except FileNotFoundError:
                errors.append(
                    f"places[{i}].photos[{j}]: image not found: {ref} (run uv run prepare_images.py)"
                )
            used_refs.add(ref)
    errors += _unused_gallery_files(static_dir, used_refs)
    return errors


def _unused_gallery_files(static_dir: Path, used_refs: set[str]) -> list[str]:
    """Gallery images no photo uses any more, e.g. after deleting an entry.

    They would still be published at a guessable address, so the build refuses
    until prepare_images.py has removed them (important if consent is withdrawn).
    """
    places_dir = static_dir / "img" / "places"
    if not places_dir.is_dir():
        return []
    errors = []
    for f in sorted(p for p in places_dir.rglob("*") if p.is_file()):
        rel = f.relative_to(static_dir).as_posix()
        ref = re.sub(r"-\d+\.webp$", "", rel)
        if ref not in used_refs:
            errors.append(f"{rel}: not used by any photo in places (run uv run prepare_images.py to remove it)")
    return errors


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
