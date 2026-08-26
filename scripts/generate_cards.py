#!/usr/bin/env python3
import re, urllib.request
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT   = Path(__file__).parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

BG           = "#0d1117"
BG2          = "#161b22"
BORDER       = "#21262d"
TEXT_PRI     = "#e6edf3"
TEXT_MUT     = "#8b949e"
TEXT_FAINT   = "#484f58"
GREEN        = "#3fb950"
RED          = "#e06c75"
YELLOW       = "#f9c74f"

# Use timezone-aware UTC now
try:
    from datetime import timezone
    NOW = datetime.now(timezone.utc).strftime("%d %b %Y UTC")
except ImportError:
    NOW = datetime.utcnow().strftime("%d %b %Y UTC")

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def trunc(s, n):
    s = s.strip()
    return esc(s[:n-1] + "\u2026") if len(s) > n else esc(s)

def fetch_xml(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return ET.fromstring(r.read())
    except Exception:
        return None

# ── GOODREADS ──────────────────────────────────────────────
def goodreads_card():
    root = fetch_xml("https://www.goodreads.com/review/list_rss/202996478-ajax?shelf=currently-reading")
    books = []
    if root is not None:
        ch = root.find("channel")
        for item in (ch.findall("item") if ch is not None else [])[:5]:
            raw = (item.findtext("title") or "").strip()
            if " by " in raw:
                t, a = raw.rsplit(" by ", 1)
                books.append((trunc(t, 60), trunc(a, 40)))
            else:
                books.append((trunc(raw, 80), ""))

    if not books:
        books = [("No books currently reading", "")]

    W, ROW_H, Y0 = 800, 32, 60
    H = Y0 + len(books) * ROW_H + 20

    rows = ""
    for i, (t, a) in enumerate(books):
        y = Y0 + i * ROW_H
        rows += f'<text x="20" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="14" fill="{TEXT_PRI}" font-weight="500">{t}</text>'
        if a:
            rows += f'<text x="{W-20}" y="{y}" text-anchor="end" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="{TEXT_MUT}">by {a}</text>'
        if i < len(books)-1:
            rows += f'<line x1="20" y1="{y+12}" x2="{W-20}" y2="{y+12}" stroke="{BORDER}" stroke-width="1" opacity="0.6"/>'

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{W}" height="{H}" rx="0" fill="{BG}"/>'
        f'<rect width="{W-2}" height="{H-2}" x="1" y="1" rx="0" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect width="{W}" height="36" rx="0" fill="{BG2}"/>'
        f'<rect y="28" width="{W}" height="8" fill="{BG2}"/>'
        f'<text x="20" y="23" font-family="Segoe UI,Arial,sans-serif" font-size="10" fill="{GREEN}" letter-spacing="1.2" font-weight="700">CURRENTLY READING \u00b7 goodreads.com/202996478-ajax</text>'
        f'<line x1="20" y1="36" x2="{W-20}" y2="36" stroke="{BORDER}" stroke-width="1"/>'
        f'{rows}'
        f'<line x1="20" y1="{H-18}" x2="{W-20}" y2="{H-18}" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{W-20}" y="{H-7}" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="{TEXT_FAINT}" text-anchor="end">{NOW}</text>'
        f'</svg>'
    )

# ── LETTERBOXD ─────────────────────────────────────────────
def star_str(rating_str):
    if not rating_str: return ""
    try:
        r = float(rating_str)
        full  = int(r)
        half  = 1 if (r - full) >= 0.5 else 0
        empty = 5 - full - half
        return "\u2605" * full + ("\u00bd" if half else "") + "\u2606" * empty
    except Exception:
        return ""

def letterboxd_card():
    LB = "https://letterboxd.com"
    root = fetch_xml("https://letterboxd.com/ajax_rn/rss/")
    films = []
    if root is not None:
        ch = root.find("channel")
        for item in (ch.findall("item") if ch is not None else [])[:5]:
            raw   = (item.findtext("title") or "").strip()
            # Remove the white stars from the title text (e.g. " - ★★★★½")
            title = re.sub(r"\s*-\s*[★½☆]+.*$", "", raw).strip()
            rating = (item.findtext(f"{{{LB}}}memberRating") or
                      item.findtext(f"{{{LB}}}rating") or "")
            films.append((trunc(title, 60), star_str(rating)))
    if not films:
        films = [("No recent films found", "")]

    W, ROW_H, Y0 = 800, 32, 60
    H = Y0 + len(films) * ROW_H + 20
    rows = ""
    for i, (film, stars) in enumerate(films):
        y = Y0 + i * ROW_H
        rows += f'<text x="20" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="14" fill="{TEXT_PRI}" font-weight="500">{film}</text>'
        if stars:
            rows += f'<text x="{W-20}" y="{y}" text-anchor="end" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="{YELLOW}">{esc(stars)}</text>'
        if i < len(films)-1:
            rows += f'<line x1="20" y1="{y+12}" x2="{W-20}" y2="{y+12}" stroke="{BORDER}" stroke-width="1" opacity="0.6"/>'

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{W}" height="{H}" rx="0" fill="{BG}"/>'
        f'<rect width="{W-2}" height="{H-2}" x="1" y="1" rx="0" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect width="{W}" height="36" rx="0" fill="{BG2}"/>'
        f'<rect y="28" width="{W}" height="8" fill="{BG2}"/>'
        f'<text x="20" y="23" font-family="Segoe UI,Arial,sans-serif" font-size="10" fill="{RED}" letter-spacing="1.2" font-weight="700">RECENTLY WATCHED \u00b7 letterboxd.com/ajax_rn</text>'
        f'<line x1="20" y1="36" x2="{W-20}" y2="36" stroke="{BORDER}" stroke-width="1"/>'
        f'{rows}'
        f'<line x1="20" y1="{H-18}" x2="{W-20}" y2="{H-18}" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{W-20}" y="{H-7}" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="{TEXT_FAINT}" text-anchor="end">{NOW}</text>'
        f'</svg>'
    )

if __name__ == "__main__":
    (ASSETS / "goodreads_card.svg").write_text(goodreads_card(), encoding="utf-8")
    (ASSETS / "letterboxd_card.svg").write_text(letterboxd_card(), encoding="utf-8")
    print("SVGs generated (multiple books, no white stars).")
