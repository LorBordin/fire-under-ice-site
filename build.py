"""Build the site: content.yaml + templates/ + static/  ->  _site/

The flow, step by step (see build() below):
  1. load content.yaml                      (sitelib.load_content)
  2. validate it; on any error print them all and stop   (sitelib.validate)
  3. drop people/partners without `consent: true`       (sitelib.filter_consented)
  4. render templates/index.html (home page) and templates/place.html (once
     per place) with Jinja2; both extend templates/layout.html
  5. delete the old _site/, write index.html and <slug>/index.html, copy static/

Run it with:  uv run build.py
Preview with: uv run python -m http.server -d _site 8000
"""
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from sitelib import file_size, filter_consented, gallery_ref, image_info, inline_md, load_content, validate


def make_environment(root: Path) -> Environment:
    """Jinja2 setup: autoescape on, unknown variables are errors, helpers added."""
    env = Environment(
        loader=FileSystemLoader(root / "templates"),
        autoescape=True,              # every {{ value }} is HTML-escaped
        undefined=StrictUndefined,    # a typo in a template fails loudly
    )
    env.filters["md"] = inline_md     # {{ text | md }}  ->  escaped, *x* = italic
    static_dir = root / "static"
    env.globals["img"] = lambda ref: image_info(static_dir, ref)
    env.globals["filesize"] = lambda ref: file_size(static_dir, ref)
    env.globals["gallery_ref"] = gallery_ref
    env.globals["prefixed_srcset"] = prefixed_srcset
    env.globals["photo_authors"] = photo_authors
    return env


def photo_authors(c: dict) -> list[str]:
    """Unique photo authors (places, field, science, contact image), sorted by surname."""
    names: list[str] = []
    for pl in c.get("places") or []:
        names += [ph["author"] for ph in pl["photos"]]
    names += [p["credit"] for p in (c.get("press") or {}).get("photos") or []]
    names += [f["credit"] for f in c.get("field") or []]
    names += [s["credit"] for s in c.get("science") or [] if s.get("credit")]
    names += [p["credit"] for p in (c.get("science_why") or {}).get("photos") or []]
    if c.get("contact_image"):
        names.append(c["contact_image"].get("credit"))
    unique = {n.strip() for n in names if n and n.strip()}
    return sorted(unique, key=lambda n: (n.split()[-1].casefold(), n.casefold()))


def prefixed_srcset(srcset: str, root: str) -> str:
    """Put `root` ("" or "../") in front of every URL of a srcset."""
    if not root or not srcset:
        return srcset
    return ", ".join(root + part.strip() for part in srcset.split(","))


def build(root: Path, out: Path) -> int:
    """Build the site in `out` from the project at `root`. Returns an exit code."""
    content = load_content(root / "content.yaml")

    errors = validate(content, root / "static")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    content, skipped = filter_consented(content)
    if skipped:
        print("Skipped (no consent): " + ", ".join(skipped))

    env = make_environment(root)
    # {output path: html}. Place pages live one folder down, hence root="../".
    pages = {"index.html": env.get_template("index.html").render(c=content, root="")}
    for place in content.get("places") or []:
        pages[f"{place['slug']}/index.html"] = env.get_template("place.html").render(
            c=content, root="../", place=place
        )

    if out.exists():
        shutil.rmtree(out)            # so files removed from static/ do not linger
    out.mkdir(parents=True)
    for name, html in pages.items():
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_text(html, encoding="utf-8")
    shutil.copytree(root / "static", out / "static")

    print(f"Built {out / 'index.html'}")
    return 0


def main() -> None:
    root = Path(__file__).parent
    sys.exit(build(root, root / "_site"))


if __name__ == "__main__":
    main()
