#!/usr/bin/env python3
"""Render the curated Tourify design docs as pages on the portfolio site.

Markdown in docs/ is the source of truth; the HTML is generated, never edited.
Tourify's own repo stays private -- only this curated subset is published, and
the docs that carry launch-relevant design are deliberately not in it.

    python3 tourify/build.py        # writes tourify/*.html
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

try:
    import markdown
except ImportError:
    sys.exit("needs Python-Markdown:  pip install markdown")

HERE = pathlib.Path(__file__).parent
DOCS = HERE / "docs"

# Order is the reading order, not alphabetical: product intent, then shape, then
# the decisions that constrained both, then the supporting detail.
PAGES = [
    ("overview", "Overview", HERE / "overview.md"),
    ("vision", "Vision", DOCS / "vision.md"),
    ("prd", "Requirements", DOCS / "prd.md"),
    ("personas", "Personas", DOCS / "personas.md"),
    ("user-stories", "User stories", DOCS / "user-stories.md"),
    ("architecture", "Architecture", DOCS / "architecture.md"),
    ("database", "Data model", DOCS / "database.md"),
    ("api", "API surface", DOCS / "api.md"),
    ("backend", "Backend", DOCS / "backend.md"),
    ("frontend", "Client", DOCS / "frontend.md"),
    ("technical-decisions", "Technical decisions", DOCS / "technical-decisions.md"),
    ("testing", "Testing", DOCS / "testing.md"),
    ("glossary", "Glossary", DOCS / "glossary.md"),
]

SLUGS = {p.name: slug for slug, _, p in PAGES}

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — Tourify</title>
<meta name="description" content="{desc}">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0a0c10">
<link rel="icon" type="image/svg+xml" href="{icon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="docs.css">
</head>
<body>
<a class="skip" href="#doc">Skip to content</a>
<div class="shell">
  <nav class="side" aria-label="Documents">
    <a class="home" href="../">&#8592; john freda</a>
    <h2>Tourify</h2>
    <ul>
{nav}
    </ul>
    <h2>Elsewhere</h2>
    <ul>
      <li><a href="https://tourify-j82w.vercel.app" target="_blank" rel="noopener noreferrer">Live demo &#8599;</a></li>
    </ul>
  </nav>
  <article id="doc">
{body}
    <p class="note">Working design document from a private repository, published as part
    of a portfolio. Written during development, lightly edited for publication.</p>
  </article>
</div>
</body>
</html>
"""

ICON = ("data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
        "<rect width='32' height='32' rx='7' fill='%237ee787'/><text x='16' y='22' "
        "font-family='ui-monospace,monospace' font-size='13' font-weight='bold' "
        "fill='%230a0c10' text-anchor='middle'>T</text></svg>")


def first_paragraph(md_text: str) -> str:
    """A one-line description for <meta>, taken from the doc's own opening."""
    for block in md_text.split("\n\n"):
        block = block.strip()
        if not block or block.startswith("#") or block.startswith(">"):
            continue
        text = re.sub(r"[*`\[\]]|\(([^)]*)\)", "", block).replace("\n", " ")
        # filenames read as a leak in a description shown by search engines
        text = re.sub(r"\b([a-z][a-z0-9-]*)\.md\b", lambda m: _humanise(m.group(0)), text)
        return html.escape(" ".join(text.split())[:155])
    return "Design documentation for Tourify."


TITLES = {slug: title for slug, title, _ in PAGES}


def _humanise(name: str) -> str:
    """`database.md` -> `Data model` if published, else `database notes`."""
    stem = name[:-3] if name.endswith(".md") else name
    slug = SLUGS.get(name)
    if slug:
        return TITLES[slug]
    return stem.replace("-", " ") + " notes"


def rewrite_links(body: str) -> str:
    """Retarget inter-doc links and make their text readable.

    The docs cross-reference each other by filename, including files this site
    does not carry. Published targets become .html; everything else is
    unwrapped, so a broken link cannot reach the site whatever the source
    references. Either way the visible text becomes the page's real title
    rather than a bare filename, which reads as a leak in prose.
    """

    def fix(m: re.Match) -> str:
        href, text = m.group(1), m.group(2)
        label = _humanise(text) if text.endswith(".md") else text
        slug = SLUGS.get(href)
        return f'<a href="{slug}.html">{label}</a>' if slug else label

    return re.sub(r'<a href="([^"]*\.md)"[^>]*>(.*?)</a>', fix, body, flags=re.S)


def main() -> None:
    md = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists", "attr_list"])

    for slug, title, path in PAGES:
        if not path.exists():
            sys.exit(f"missing source: {path}")
        text = path.read_text()
        md.reset()
        body = rewrite_links(md.convert(text))
        # Tables must scroll inside their own box, never widen the page.
        body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
        body = re.sub(r"</table>", "</table></div>", body)

        nav = "\n".join(
            '      <li><a href="{s}.html"{cur}>{t}</a></li>'.format(
                s=s, t=html.escape(t), cur=' aria-current="page"' if s == slug else ""
            )
            for s, t, _ in PAGES
        )
        out = TEMPLATE.format(
            title=html.escape(title), desc=first_paragraph(text),
            icon=ICON, nav=nav, body=body,
        )
        (HERE / f"{slug}.html").write_text(out)
        print(f"  {slug}.html")

    # /tourify/ should land on the overview.
    (HERE / "index.html").write_text((HERE / "overview.html").read_text())
    print("  index.html (copy of overview)")


if __name__ == "__main__":
    main()
