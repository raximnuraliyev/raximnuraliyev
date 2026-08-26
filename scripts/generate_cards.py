#!/usr/bin/env python3
"""
generate_cards.py
Fetches RSS feeds and writes dark-themed SVG cards into assets/.
"""
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
NOW          = datetime.utcnow().strftime("%d %b %Y UTC")


def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def trunc(s, n):
    s = s.strip()
    return esc(s[:n-1] + "\u2026") if len(s) > n else esc(s)

def fetch_xml(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; ProfileBot/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return ET.fromstring(r.read())
    except Exception as e:
        print(f"  [WARN] {url}: {e}")
        return None


# ── GOODREADS ──────────────────────────────────────────────

def goodreads_card():
    root = fetch_xml("https://www.goodreads.com/review/list_rss/202996478-ajax?shelf=currently-reading")
    title, author = "No book on shelf right now", ""
    if root is not None:
        ch = root.find("channel")
        items = ch.findall("item") if ch is not None else []
        if items:
            raw = (items[0].findtext("title") or "").strip()
            if " by " in raw:
                t, a = raw.rsplit(" by ", 1)
                title, author = trunc(t, 32), trunc(a, 28)
            else:
                title = trunc(raw, 32)
    else:
        title = "Could not reach Goodreads"

    book = (
        '<rect x="20" y="24" width="52" height="74" rx="3" fill="#161b22" stroke="#3fb950" stroke-width="1.5"/>'
        '<rect x="26" y="30" width="3" height="62" rx="1" fill="#3fb950" opacity="0.35"/>'
        '<rect x="31" y="38" width="32" height="2" rx="1" fill="#3fb950" opacity="0.65"/>'
        '<rect x="31" y="45" width="26" height="2" rx="1" fill="#8b949e" opacity="0.5"/>'
        '<rect x="31" y="52" width="29" height="2" rx="1" fill="#8b949e" opacity="0.5"/>'
        '<rect x="31" y="59" width="22" height="2" rx="1" fill="#8b949e" opacity="0.5"/>'
        '<rect x="31" y="66" width="27" height="2" rx="1" fill="#8b949e" opacity="0.5"/>'
    )
    author_el = f'<text x="88" y="83" font-family="Segoe UI,Arial,sans-serif" font-size="12" fill="{TEXT_MUT}">by {author}</text>' if author else ""

    return (
        f'<svg width="380" height="135" viewBox="0 0 380 135" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="380" height="135" rx="8" fill="{BG}"/>'
        f'<rect width="378" height="133" x="1" y="1" rx="8" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'{book}'
        f'<text x="88" y="40" font-family="Segoe UI,Arial,sans-serif" font-size="10" fill="{GREEN}" letter-spacing="1.2" font-weight="700">CURRENTLY READING</text>'
        f'<text x="88" y="65" font-family="Segoe UI,Arial,sans-serif" font-size="15" fill="{TEXT_PRI}" font-weight="600">{title}</text>'
        f'{author_el}'
        f'<line x1="16" y1="118" x2="364" y2="118" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="16" y="129" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="{TEXT_FAINT}">goodreads.com / 202996478-ajax</text>'
        f'<text x="364" y="129" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="{TEXT_FAINT}" text-anchor="end">{NOW}</text>'
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
            title = re.sub(r",\s*\d{1,2}\s+\w+\s+\d{4}.*$", "", raw).strip()
            rating = (item.findtext(f"{{{LB}}}memberRating") or
                      item.findtext(f"{{{LB}}}rating") or "")
            films.append((trunc(title, 48), star_str(rating)))
    if not films:
        films = [("No recent films found", "")]

    W, ROW_H, Y0 = 760, 27, 52
    H = Y0 + len(films) * ROW_H + 30
    rows = ""
    for i, (film, stars) in enumerate(films):
        y = Y0 + i * ROW_H
        rows += f'<text x="20" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="{TEXT_PRI}" font-weight="500">{film}</text>'
        if stars:
            rows += f'<text x="{W-20}" y="{y}" text-anchor="end" font-family="Segoe UI,Arial,sans-serif" font-size="12" fill="{YELLOW}">{esc(stars)}</text>'
        if i < len(films)-1:
            rows += f'<line x1="20" y1="{y+9}" x2="{W-20}" y2="{y+9}" stroke="{BORDER}" stroke-width="1" opacity="0.6"/>'

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{W}" height="{H}" rx="8" fill="{BG}"/>'
        f'<rect width="{W-2}" height="{H-2}" x="1" y="1" rx="8" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect width="{W}" height="36" rx="8" fill="{BG2}"/>'
        f'<rect y="28" width="{W}" height="8" fill="{BG2}"/>'
        f'<text x="20" y="23" font-family="Segoe UI,Arial,sans-serif" font-size="10" fill="{RED}" letter-spacing="1.2" font-weight="700">RECENTLY WATCHED \u00b7 letterboxd.com/ajax_rn</text>'
        f'<line x1="20" y1="36" x2="{W-20}" y2="36" stroke="{BORDER}" stroke-width="1"/>'
        f'{rows}'
        f'<line x1="20" y1="{H-18}" x2="{W-20}" y2="{H-18}" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{W-20}" y="{H-7}" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="{TEXT_FAINT}" text-anchor="end">{NOW}</text>'
        f'</svg>'
    )

if __name__ == "__main__":
    print("Generating Goodreads card...")
    (ASSETS / "goodreads_card.svg").write_text(goodreads_card(), encoding="utf-8")
    print("  -> assets/goodreads_card.svg")
    print("Generating Letterboxd card...")
    (ASSETS / "letterboxd_card.svg").write_text(letterboxd_card(), encoding="utf-8")
    print("  -> assets/letterboxd_card.svg")
    print("Done.")
