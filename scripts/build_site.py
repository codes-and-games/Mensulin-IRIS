"""Static documentation site for GitHub Pages: converts docs/**/*.md and README.md to HTML under site/. No data, no run folders.
    python -m pip install markdown && python scripts/build_site.py"""
from pathlib import Path
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "site"

def read_markdown(src: Path) -> str:
    """Read UTF-8 Markdown, with a warned fallback for legacy Windows-1252 files."""
    raw = src.read_bytes()
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        try:
            decoded = raw.decode("cp1252")
        except UnicodeDecodeError:
            raise RuntimeError(f"{src.relative_to(ROOT)} is neither valid UTF-8 nor Windows-1252") from exc
        print(f"WARNING: {src.relative_to(ROOT)} decoded as Windows-1252; invalid UTF-8 at byte {exc.start}")
        return decoded

PAGE = "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'><title>{t}</title><style>body{{font:16px/1.55 system-ui;max-width:60rem;margin:2rem auto;padding:0 1rem}}table{{border-collapse:collapse;font-size:.9rem}}td,th{{border:1px solid #bbb;padding:.3rem .5rem;vertical-align:top}}code,pre{{background:#f4f4f4}}pre{{padding:.6rem;overflow:auto}}</style><p><a href='{root}index.html'>IRIS</a></p>{b}"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    pages = [(ROOT / "README.md", "index.html")] + [(p, str(p.relative_to(ROOT / "docs").with_suffix(".html"))) for p in sorted((ROOT / "docs").rglob("*.md"))]
    index = ["<h1>IRIS documentation</h1><ul>"]
    for src, rel in pages:
        dst = OUT / rel; dst.parent.mkdir(parents=True, exist_ok=True)
        html = markdown.markdown(read_markdown(src), extensions=["tables", "fenced_code"])
        html = re.sub(r'href="([^"#:]+)\.md(#[^"]*)?"', r'href="\1.html\2"', html)
        root = "../" * rel.count("/")
        dst.write_text(PAGE.format(t=src.stem, root=root, b=html), encoding="utf-8")
        if rel != "index.html":
            index.append(f"<li><a href='{rel}'>{rel[:-5]}</a></li>")
    (OUT / "index.html").write_text(PAGE.format(t="IRIS", root="", b=markdown.markdown(read_markdown(ROOT / "README.md"), extensions=["tables", "fenced_code"]) + "".join(index) + "</ul>"), encoding="utf-8")
    print("built", len(pages), "pages ->", OUT)


if __name__ == "__main__":
    main()
