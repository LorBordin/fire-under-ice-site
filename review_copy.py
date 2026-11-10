"""Write a plain-text reviewer copy of every science page.

Run `uv run review_copy.py`. It writes docs/review/<slug>.md for each topic in
content.yaml, published or not. Send that file to the reviewers named in the
topic's `reviewers:` line.
"""
from pathlib import Path

from sitelib import load_content


def topic_markdown(topic: dict) -> str:
    """The text of one topic as Markdown: title, status, chapters, references."""
    status = "published" if topic.get("reviewed") is True else "draft (not on the site)"
    out = [f"# {topic['title']}", "",
           f"Reviewers: {topic.get('reviewers', '')} · Status: {status}", ""]
    for p in topic.get("intro", []):
        out += [p, ""]
    for ch in topic.get("chapters", []):
        out += [f"## {ch['heading']}", ""]
        for p in ch.get("paragraphs", []):
            out += [p, ""]
        ph = ch.get("photo")
        if ph:
            out += [f"[Photo: {ph['caption']} © {ph['author']}]", ""]
    refs = topic.get("references", [])
    if refs:
        out += ["## References", ""]
        for i, r in enumerate(refs, 1):
            out.append(f"{i}. {r['text']}" + (f" {r['url']}" if r.get("url") else ""))
    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    root = Path(__file__).parent
    topics = load_content(root / "content.yaml").get("topics") or []
    if not topics:
        print("No topics in content.yaml: nothing to write.")
        return
    outdir = root / "docs" / "review"
    outdir.mkdir(parents=True, exist_ok=True)
    for t in topics:
        path = outdir / f"{t['slug']}.md"
        path.write_text(topic_markdown(t), encoding="utf-8")
        print(f"Wrote {path.relative_to(root)}")


if __name__ == "__main__":
    main()
