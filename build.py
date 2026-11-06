"""Build the site: content.yaml + templates/ + static/  ->  _site/

The flow, step by step (see build() below):
  1. load content.yaml                      (sitelib.load_content)
  2. validate it; on any error print them all and stop   (sitelib.validate)
  3. drop people/partners without `consent: true`       (sitelib.filter_consented)
  4. render templates/base.html with Jinja2 into one HTML string
  5. delete the old _site/, write index.html, copy static/ next to it

Run it with:  uv run build.py
Preview with: uv run python -m http.server -d _site 8000
"""
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from sitelib import filter_consented, image_info, inline_md, load_content, validate


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
    return env


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

    html = make_environment(root).get_template("base.html").render(c=content)

    if out.exists():
        shutil.rmtree(out)            # so files removed from static/ do not linger
    out.mkdir(parents=True)
    (out / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(root / "static", out / "static")

    print(f"Built {out / 'index.html'}")
    return 0


def main() -> None:
    root = Path(__file__).parent
    sys.exit(build(root, root / "_site"))


if __name__ == "__main__":
    main()
