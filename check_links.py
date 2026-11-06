"""Check that the external links in content.yaml still answer.

Run by hand, not part of the build (it needs the network):
    uv run check_links.py

Prints one line per URL, e.g. "200  https://...", or the error name
(e.g. "TimeoutError") when the request failed. Exits 1 if any link did
not return a 2xx or 3xx status.
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path

from sitelib import load_content

TIMEOUT = 15
USER_AGENT = "fire-under-ice-site link check"
CONTENT = Path(__file__).resolve().parent / "content.yaml"


def collect_urls(content: dict) -> list[str]:
    """Every http(s) string in the content, in order, without duplicates.

    The site's own address (site.url) is skipped.
    """
    skip = content.get("site", {}).get("url")
    found: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            if node.startswith(("http://", "https://")) and node != skip:
                found.append(node)

    walk(content)
    return list(dict.fromkeys(found))


def _fetch(url: str, method: str) -> int:
    """Return the HTTP status code. HTTP errors give their code; other errors raise."""
    request = urllib.request.Request(
        url, method=method, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def check(url: str, fetch=_fetch) -> tuple[str, int | str]:
    """Return (url, status) or (url, exception name).

    Tries HEAD first; some servers refuse HEAD (405 or 403), so those retry with GET.
    """
    try:
        status = fetch(url, "HEAD")
        if status in (405, 403):
            status = fetch(url, "GET")
    except Exception as exc:
        return url, type(exc).__name__
    return url, status


def main() -> None:
    urls = collect_urls(load_content(CONTENT))
    failed = False
    for url in urls:
        _, status = check(url)
        print(f"{status}  {url}")
        if not (isinstance(status, int) and 200 <= status < 400):
            failed = True
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
