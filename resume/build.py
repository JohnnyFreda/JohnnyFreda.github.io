#!/usr/bin/env python3
"""Render the resume as a page on the site, from the same file that makes the PDF.

print.html is the single source: it carries the content and the print styling
that Chromium turns into the PDF. This lifts its body out and re-dresses it in
the site's own styling, so the page and the download can never drift apart.

    python3 resume/build.py     # writes resume/index.html
"""

from __future__ import annotations

import pathlib
import re

HERE = pathlib.Path(__file__).parent
PDF = "John_Freda_Resume.pdf"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Résumé — John Freda</title>
<meta name="description" content="Résumé of John Freda, full-stack developer in Tampa, FL. TypeScript, React, React Native, Python/FastAPI, PostgreSQL.">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0a0c10">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='7' fill='%237ee787'/><text x='16' y='22' font-family='ui-monospace,monospace' font-size='13' font-weight='bold' fill='%230a0c10' text-anchor='middle'>JF</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap">
<link rel="stylesheet" href="resume.css">
</head>
<body>
<a class="skip" href="#cv">Skip to content</a>
<div class="wrap">
  <div class="bar">
    <a class="home" href="../">&#8592; john freda</a>
    <a class="dl" href="{pdf}" download>Download PDF</a>
  </div>
  <main id="cv" class="cv">
{body}
  </main>
</div>
</body>
</html>
"""


def main() -> None:
    src = (HERE / "print.html").read_text()
    m = re.search(r"<body[^>]*>(.*)</body>", src, re.S)
    if not m:
        raise SystemExit("no <body> in print.html")
    body = m.group(1).strip()
    # The print sheet marks section headings with h2; the page needs one h1 for
    # the document, and the name is it.
    body = body.replace('<div class="name">John Freda</div>', '<h1 class="name">John Freda</h1>')
    (HERE / "index.html").write_text(TEMPLATE.format(pdf=PDF, body=body))
    print("  resume/index.html")


if __name__ == "__main__":
    main()
