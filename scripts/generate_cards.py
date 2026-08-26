#!/usr/bin/env python3
import re, urllib.request, base64
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

def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode('utf-8')
    except Exception:
        return ""

def get_b64_image(url):
    if not url: return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ctype = r.headers.get('Content-Type', 'image/jpeg')
            b64 = base64.b64encode(r.read()).decode('utf-8')
            return f"data:{ctype};base64,{b64}"
    except Exception:
        return ""

# ── GOODREADS ──────────────────────────────────────────────
def goodreads_card():
    root = fetch_xml("https://www.goodreads.com/review/list_rss/202996478-ajax?shelf=currently-reading")
    books = []
    if root is not None:
        ch = root.find("channel")
        for item in (ch.findall("item") if ch is not None else [])[:5]:
            raw = (item.findtext("title") or "").strip()
            pub = (item.findtext("book_published") or "").strip()
            img_url = (item.findtext("book_large_image_url") or "").strip()
            b64 = get_b64_image(img_url)

            if " by " in raw:
                t, a = raw.rsplit(" by ", 1)
                books.append((trunc(t, 55), trunc(a, 40), pub, b64))
            else:
                books.append((trunc(raw, 55), "", pub, b64))

    if not books:
        books = [("No books currently reading", "", "", "")]

    W, ROW_H, Y0 = 800, 70, 60
    H = Y0 + len(books) * ROW_H + 20

    rows = ""
    for i, (t, a, pub, img) in enumerate(books):
        y = Y0 + i * ROW_H
        if img:
            rows += f'<image x="20" y="{y+5}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            rows += f'<rect x="20" y="{y+5}" width="40" height="60" fill="#21262d"/>'

        rows += f'<text x="75" y="{y+25}" font-family="Segoe UI,Arial,sans-serif" font-size="15" fill="{TEXT_PRI}" font-weight="600">{t}</text>'

        subtext = []
        if a: subtext.append(f"by {a}")
        if pub: subtext.append(f"({pub})")
        subtext_str = " ".join(subtext)

        if subtext_str:
            rows += f'<text x="75" y="{y+45}" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="{TEXT_MUT}">{subtext_str}</text>'

        if i < len(books)-1:
            rows += f'<line x1="20" y1="{y+ROW_H}" x2="{W-20}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="1" opacity="0.6"/>'

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
            title = re.sub(r"\s*-\s*[★½☆]+.*$", "", raw).strip()
            rating = (item.findtext(f"{{{LB}}}memberRating") or
                      item.findtext(f"{{{LB}}}rating") or "")

            desc_html = item.findtext("description") or ""
            img_url = ""
            m = re.search(r'<img.*?src="(.*?)"', desc_html)
            if m:
                img_url = m.group(1)
            b64 = get_b64_image(img_url)

            films.append((trunc(title, 55), star_str(rating), b64))

    if not films:
        films = [("No recent films found", "", "")]

    W, ROW_H, Y0 = 800, 70, 60
    H = Y0 + len(films) * ROW_H + 20
    rows = ""
    for i, (film, stars, img) in enumerate(films):
        y = Y0 + i * ROW_H
        if img:
            rows += f'<image x="20" y="{y+5}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            rows += f'<rect x="20" y="{y+5}" width="40" height="60" fill="#21262d"/>'

        rows += f'<text x="75" y="{y+35}" font-family="Segoe UI,Arial,sans-serif" font-size="15" fill="{TEXT_PRI}" font-weight="600">{film}</text>'
        if stars:
            rows += f'<text x="{W-20}" y="{y+35}" text-anchor="end" font-family="Segoe UI,Arial,sans-serif" font-size="14" fill="{YELLOW}">{esc(stars)}</text>'
        if i < len(films)-1:
            rows += f'<line x1="20" y1="{y+ROW_H}" x2="{W-20}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="1" opacity="0.6"/>'

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

# ── LAST.FM (TOP TRACKS) ───────────────────────────────────
def lastfm_card():
    API_KEY = "b25b959554ed76058ac220b7b2e0a026"
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks&user=ajaxmanson&api_key={API_KEY}&period=1month&format=json&limit=5"
    
    tracks = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            import json
            data = json.loads(r.read())
            for track in data.get("toptracks", {}).get("track", []):
                t = track.get("name", "")
                a = track.get("artist", {}).get("name", "")
                
                img_url = ""
                images = track.get("image", [])
                for img in images:
                    if img.get("size") == "large" or img.get("size") == "extralarge":
                        img_url = img.get("#text", img_url)
                
                b64 = get_b64_image(img_url) if img_url else ""
                playcount = int(track.get("playcount", 0))
                
                tracks.append((trunc(t, 45), trunc(a, 35), b64, playcount))
    except Exception:
        pass

    if not tracks:
        tracks = [("No top tracks found", "", "", 0)]

    max_scrobbles = max(tracks, key=lambda x: x[3])[3] if tracks and tracks[0][3] > 0 else 1

    W, ROW_H, Y0 = 800, 70, 60
    H = Y0 + len(tracks) * ROW_H + 20
    rows = ""
    for i, (t, a, img, count) in enumerate(tracks):
        y = Y0 + i * ROW_H
        if img:
            rows += f'<image x="20" y="{y+10}" width="50" height="50" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            rows += f'<rect x="20" y="{y+10}" width="50" height="50" fill="#21262d"/>'
            
        rows += f'<text x="85" y="{y+32}" font-family="Segoe UI,Arial,sans-serif" font-size="15" fill="{TEXT_PRI}" font-weight="600">{t}</text>'
        if a:
            rows += f'<text x="85" y="{y+52}" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="{TEXT_MUT}">{a}</text>'
            
        # Scrobble Bar
        if count > 0:
            # Max bar width is 300px, starting at W - 320
            bar_max = 300
            bar_width = max(30, int((count / max_scrobbles) * bar_max))
            bar_x = W - 20 - bar_width
            
            rows += f'<rect x="{bar_x}" y="{y+20}" width="{bar_width}" height="30" rx="4" fill="#bd2f2f"/>'
            
            count_text = f"{count} scrobbles" if i == 0 else f"{count}"
            rows += f'<text x="{bar_x + 10}" y="{y+40}" font-family="Segoe UI,Arial,sans-serif" font-size="13" fill="#ffffff" font-weight="600">{count_text}</text>'

        if i < len(tracks)-1:
            rows += f'<line x1="20" y1="{y+ROW_H}" x2="{W-20}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="1" opacity="0.6"/>'

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{W}" height="{H}" rx="0" fill="{BG}"/>'
        f'<rect width="{W-2}" height="{H-2}" x="1" y="1" rx="0" fill="none" stroke="{BORDER}" stroke-width="1"/>'
        f'<rect width="{W}" height="36" rx="0" fill="{BG2}"/>'
        f'<rect y="28" width="{W}" height="8" fill="{BG2}"/>'
        f'<text x="20" y="23" font-family="Segoe UI,Arial,sans-serif" font-size="10" fill="#D51007" letter-spacing="1.2" font-weight="700">TOP TRACKS (LAST 30 DAYS) \u00b7 last.fm/user/ajaxmanson</text>'
        f'<line x1="20" y1="36" x2="{W-20}" y2="36" stroke="{BORDER}" stroke-width="1"/>'
        f'{rows}'
        f'<line x1="20" y1="{H-18}" x2="{W-20}" y2="{H-18}" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="{W-20}" y="{H-7}" font-family="Segoe UI,Arial,sans-serif" font-size="9" fill="{TEXT_FAINT}" text-anchor="end">{NOW}</text>'
        f'</svg>'
    )

if __name__ == "__main__":
    (ASSETS / "goodreads_card.svg").write_text(goodreads_card(), encoding="utf-8")
    (ASSETS / "letterboxd_card.svg").write_text(letterboxd_card(), encoding="utf-8")
    (ASSETS / "lastfm_card.svg").write_text(lastfm_card(), encoding="utf-8")
    print("SVGs generated (with Base64 covers and Last.fm scraper).")
