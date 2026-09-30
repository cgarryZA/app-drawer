#!/usr/bin/env python3
"""Regenerate docs/index.html from this repository's releases.

One release tag per app (see README). Each release contributes one card with a
download button pointing at its .apk asset. A release with no .apk asset is
skipped rather than rendered as a dead button - a card that cannot be
downloaded from is worse than no card.

Input is the GitHub releases API via `gh api`, so this needs no token beyond
the one the workflow already has. Pure stdlib otherwise.
"""

from __future__ import annotations

import html
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

REPO = "cgarryZA/app-drawer"
OUT = pathlib.Path(__file__).resolve().parent.parent / "docs" / "index.html"


def releases() -> list[dict]:
    raw = subprocess.run(
        ["gh", "api", f"repos/{REPO}/releases", "--paginate"],
        capture_output=True, text=True, check=True).stdout
    return json.loads(raw)


def human_size(n: int) -> str:
    mb = n / (1024 * 1024)
    return f"{mb:.1f} MB" if mb >= 1 else f"{n / 1024:.0f} KB"


def cards(rels: list[dict]) -> list[dict]:
    out = []
    for r in rels:
        if r.get("draft"):
            continue
        apk = next((a for a in r.get("assets", [])
                    if a["name"].lower().endswith(".apk")), None)
        if not apk:
            continue  # nothing to download: no card
        published = r.get("published_at") or r.get("created_at") or ""
        try:
            when = datetime.fromisoformat(
                published.replace("Z", "+00:00")).strftime("%d %b %Y")
        except ValueError:
            when = ""
        out.append({
            "name": r.get("name") or r["tag_name"],
            "tag": r["tag_name"],
            "url": apk["browser_download_url"],
            "size": human_size(apk["size"]),
            "when": when,
            "notes": (r.get("body") or "").strip(),
        })
    out.sort(key=lambda c: c["name"].lower())
    return out


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>App drawer - Christian Garry</title>
<meta name="description" content="Android apps by Christian Garry. Direct APK downloads.">
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem 1.25rem 4rem;
    font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #12131a; color: #e8e9ef;
  }}
  main {{ max-width: 34rem; margin: 0 auto; }}
  h1 {{ font-size: 1.5rem; margin: 0 0 .35rem; letter-spacing: -.01em; }}
  .sub {{ color: #9a9dad; margin: 0 0 2rem; font-size: .95rem; }}
  .app {{
    background: #1b1d27; border: 1px solid #272a37; border-radius: 14px;
    padding: 1.1rem 1.2rem; margin-bottom: 1rem;
  }}
  .app h2 {{ font-size: 1.1rem; margin: 0 0 .2rem; }}
  .meta {{ color: #8b8fa3; font-size: .82rem; margin: 0 0 .9rem; }}
  .notes {{ color: #b9bccb; font-size: .9rem; margin: 0 0 .9rem; white-space: pre-wrap; }}
  a.dl {{
    display: block; text-align: center; text-decoration: none;
    background: #3d6ae4; color: #fff; font-weight: 600;
    padding: .7rem 1rem; border-radius: 10px;
  }}
  a.dl:hover {{ background: #3159c9; }}
  details {{ margin-top: 2.5rem; color: #9a9dad; font-size: .88rem; }}
  details summary {{ cursor: pointer; color: #b9bccb; }}
  details ol {{ padding-left: 1.2rem; }}
  footer {{ margin-top: 2.5rem; color: #6f7386; font-size: .78rem; }}
  .empty {{ color: #9a9dad; }}
</style>
</head>
<body>
<main>
  <h1>App drawer</h1>
  <p class="sub">Android apps I build. Not on Google Play - download and install directly.</p>

  {body}

  <details>
    <summary>Installing an APK on Android</summary>
    <ol>
      <li>Tap a download button above and let the file download.</li>
      <li>Open it. Android will ask permission to install from your browser -
          allow it, then tap the file again.</li>
      <li>Play Protect may say the app is unrecognised. Choose "Install anyway".</li>
    </ol>
    <p>Installing over an older version keeps your data.</p>
  </details>

  <footer>Generated from the repository's releases on {stamp}.
    <a href="https://github.com/{repo}" style="color:#6f7386">Source</a>.</footer>
</main>
</body>
</html>
"""

CARD = """  <div class="app">
    <h2>{name}</h2>
    <p class="meta">{size}{dot}{when}</p>
    {notes}<a class="dl" href="{url}">Download for Android</a>
  </div>
"""


def render(cs: list[dict]) -> str:
    if not cs:
        body = '<p class="empty">No apps published yet.</p>'
    else:
        body = "".join(
            CARD.format(
                name=html.escape(c["name"]),
                size=html.escape(c["size"]),
                dot=" &middot; " if c["when"] else "",
                when=html.escape(c["when"]),
                notes=(f'<p class="notes">{html.escape(c["notes"])}</p>\n    '
                       if c["notes"] else ""),
                url=html.escape(c["url"], quote=True),
            )
            for c in cs)
    return PAGE.format(
        body=body.strip(),
        stamp=datetime.now(timezone.utc).strftime("%d %b %Y"),
        repo=REPO,
    )


def main() -> int:
    cs = cards(releases())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(cs), encoding="utf-8")
    print(f"wrote {OUT} with {len(cs)} app(s): {', '.join(c['tag'] for c in cs) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
