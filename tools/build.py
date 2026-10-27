#!/usr/bin/env python3
"""Builds the Right Now feed site (now.filmsuperintelligence.org) from items/*.json.

Outputs (committed to the repo, served as-is by GitHub Pages):
  now.json      every item, newest first (the homepage stream reads this)
  index.html    the full archive and source list (Google reads this)
  i/<id>.html   one page per item (what Share links point to)
  feed.xml      RSS
  items.csv     spreadsheet of every item and its source
  sitemap.xml, robots.txt

Run:  python3 tools/build.py        (no dependencies beyond Python 3.9+)
"""
import csv
import datetime as dt
import html
import io
import json
import pathlib
import re
import sys
from email.utils import format_datetime
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://now.filmsuperintelligence.org"
HOME = "https://filmsuperintelligence.org"
REQUIRED = ["id", "date", "who", "role", "kind", "text", "context", "outlet", "url"]
e = lambda s: html.escape(str(s), quote=True)


def load():
    items, errors = [], []
    for f in sorted((ROOT / "items").glob("*.json")):
        try:
            it = json.loads(f.read_text(encoding="utf-8"))
        except Exception as ex:  # noqa: BLE001
            errors.append(f"{f.name}: not valid JSON ({ex})")
            continue
        missing = [k for k in REQUIRED if not str(it.get(k, "")).strip()]
        if missing:
            errors.append(f"{f.name}: missing {', '.join(missing)}")
        if it.get("id") != f.stem:
            errors.append(f"{f.name}: id must equal the file name ({f.stem})")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(it.get("date", ""))):
            errors.append(f"{f.name}: date must be YYYY-MM-DD")
        if it.get("kind") not in ("quote", "headline"):
            errors.append(f"{f.name}: kind must be quote or headline")
        if not str(it.get("url", "")).startswith("https://"):
            errors.append(f"{f.name}: url must start with https://")
        if len(str(it.get("text", "")).split()) > 40:
            errors.append(f"{f.name}: text is over 40 words; shorten it")
        items.append(it)
    if errors:
        sys.exit("Fix these before publishing:\n  " + "\n  ".join(errors))
    items.sort(key=lambda it: (it["date"], it["id"]), reverse=True)
    return items


def d_long(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def month_name(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.year}"


def said(it):
    t = it["text"]
    return t if it["kind"] == "headline" else f"“{t}”"


STYLE = """
@font-face{font-family:"Instrument Serif";font-style:normal;font-weight:400;font-display:swap;src:url(/assets/fonts/instrument-serif-latin-400-normal.woff2) format("woff2")}
@font-face{font-family:"Instrument Serif";font-style:italic;font-weight:400;font-display:swap;src:url(/assets/fonts/instrument-serif-latin-400-italic.woff2) format("woff2")}
@font-face{font-family:"Bricolage Grotesque";font-style:normal;font-weight:200 800;font-display:swap;src:url(/assets/fonts/bricolage-grotesque-latin-opsz-normal.woff2) format("woff2-variations")}
@font-face{font-family:"JetBrains Mono";font-style:normal;font-weight:500;font-display:swap;src:url(/assets/fonts/jetbrains-mono-latin-500-normal.woff2) format("woff2")}
:root{--bg:#0a0a0a;--card:#121212;--lime:#c8ed4f;--gold:#e9c44a;--white:#fff;--line:rgba(255,255,255,.16);color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--white);font:17px/1.5 "Bricolage Grotesque",system-ui,sans-serif;padding:0 20px 80px}
a{color:var(--lime)}
.wrap{max-width:860px;margin:0 auto}
header{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 0;border-bottom:1px solid var(--line)}
.wm{font-family:"Instrument Serif",Georgia,serif;font-size:24px;color:var(--white);text-decoration:none}
.wm span{color:var(--lime)}
.enter{background:var(--gold);color:#0a0a0a;text-decoration:none;font-weight:600;padding:10px 18px;border-radius:999px;font-size:15px}
h1{font-family:"Instrument Serif",Georgia,serif;font-weight:400;color:var(--lime);font-size:clamp(44px,8vw,84px);line-height:.95;margin:40px 0 12px}
.lead{max-width:60ch;margin:0 0 10px}
.tools{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin:16px 0 8px}
h2{font-family:"Instrument Serif",Georgia,serif;font-weight:400;color:var(--gold);font-size:32px;margin:44px 0 12px}
article{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:0 0 12px}
.date{font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.07em;text-transform:uppercase;color:var(--gold);margin:0 0 6px}
.who{font-weight:700;margin:0}
.role{margin:0 0 10px}
.said{font-family:"Instrument Serif",Georgia,serif;font-size:27px;line-height:1.15;margin:0 0 10px}
.said.h{font-style:italic}
.ctx{margin:0 0 10px}
.src{font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:.05em;text-transform:uppercase;margin:0}
.src a{text-decoration:none}
footer{margin-top:48px;border-top:1px solid var(--line);padding-top:18px;font-size:14px}
"""


def head(title, desc, url, extra=""):
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{e(title)}</title><meta name="description" content="{e(desc)}">'
            f'<link rel="canonical" href="{e(url)}">'
            f'<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}">'
            f'<meta property="og:url" content="{e(url)}"><meta property="og:type" content="article">'
            f'<meta name="theme-color" content="#0a0a0a">'
            f'<link rel="alternate" type="application/rss+xml" title="Right Now" href="{BASE}/feed.xml">'
            f'{extra}<style>{STYLE}</style></head><body><div class="wrap">'
            f'<header><a class="wm" href="{HOME}">Film <span>Superintelligence</span></a>'
            f'<a class="enter" href="https://filmfreeway.com/aiinternationalfilmfestival">Submit your film</a></header>')


FOOT = ('<footer>Right Now is part of <a href="' + HOME + '">Film Superintelligence</a>, a global film challenge. '
        'Every quote links to its original source. AI International Film Festivals is operated by The AI Project, '
        'a California nonprofit public benefit corporation.</footer></div></body></html>')


def article(it, link=True):
    host = urlparse(it["url"]).hostname.replace("www.", "")
    note = f' · {e(it["sourceNote"])}' if it.get("sourceNote") else ""
    perma = f' · <a href="/i/{e(it["id"])}.html">Link</a>' if link else ""
    cls = "said h" if it["kind"] == "headline" else "said"
    return (f'<article id="{e(it["id"])}"><p class="date">{d_long(it["date"])}</p>'
            f'<p class="who">{e(it["who"])}</p><p class="role">{e(it["role"])}</p>'
            f'<p class="{cls}">{e(said(it))}</p><p class="ctx">{e(it["context"])}</p>'
            f'<p class="src"><a href="{e(it["url"])}" rel="noopener">{e(it["outlet"])} ({e(host)})</a>{note}{perma}</p></article>')


def main():
    items = load()
    today = dt.date.today().isoformat()

    (ROOT / "now.json").write_text(json.dumps({"updated": today, "count": len(items), "items": items},
                                              ensure_ascii=False, indent=1), encoding="utf-8")

    parts, last = [], ""
    for it in items:
        m = month_name(it["date"])
        if m != last:
            parts.append(f"<h2>{m}</h2>")
            last = m
        parts.append(article(it))
    desc = "What the people building and governing AI are saying, newest first. Every quote is sourced."
    (ROOT / "index.html").write_text(
        head("Right Now: the AI debate, sourced", desc, BASE + "/")
        + '<h1>Right now</h1><p class="lead">' + e(desc) + "</p>"
        + f'<p class="tools"><span>{len(items)} items</span><a href="/items.csv">Download all sources (CSV)</a>'
        + '<a href="/feed.xml">RSS</a></p>' + "".join(parts) + FOOT, encoding="utf-8")

    (ROOT / "i").mkdir(exist_ok=True)
    for old in (ROOT / "i").glob("*.html"):
        old.unlink()
    for it in items:
        title = f'{it["who"]}: {said(it)}'
        (ROOT / "i" / f'{it["id"]}.html').write_text(
            head(title, it["context"], f'{BASE}/i/{it["id"]}.html')
            + article(it, link=False)
            + f'<p class="tools"><a href="/">All quotes</a><a href="{HOME}">Film Superintelligence</a></p>' + FOOT,
            encoding="utf-8")

    rss = ['<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>',
           f"<title>Right Now: Film Superintelligence</title><link>{BASE}/</link>",
           "<description>What the people building and governing AI are saying. Every quote sourced.</description>"]
    for it in items[:50]:
        d = dt.datetime.fromisoformat(it["date"] + "T12:00:00+00:00")
        rss.append(f'<item><title>{e(it["who"] + ": " + said(it))}</title><link>{BASE}/i/{e(it["id"])}.html</link>'
                   f'<guid>{BASE}/i/{e(it["id"])}.html</guid><pubDate>{format_datetime(d)}</pubDate>'
                   f'<description>{e(it["context"])} Source: {e(it["outlet"])} {e(it["url"])}</description></item>')
    rss.append("</channel></rss>")
    (ROOT / "feed.xml").write_text("".join(rss), encoding="utf-8")

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "who", "role", "kind", "text", "context", "outlet", "source_note", "url", "id"])
    for it in items:
        w.writerow([it["date"], it["who"], it["role"], it["kind"], it["text"], it["context"], it["outlet"],
                    it.get("sourceNote", ""), it["url"], it["id"]])
    (ROOT / "items.csv").write_text(buf.getvalue(), encoding="utf-8")

    urls = [BASE + "/"] + [f'{BASE}/i/{it["id"]}.html' for it in items]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{u}</loc></url>" for u in urls) + "</urlset>", encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")
    print(f"Built {len(items)} items. Newest: {items[0]['date']} {items[0]['who']}")


if __name__ == "__main__":
    main()
