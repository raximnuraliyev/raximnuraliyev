#!/usr/bin/env python3
"""
Black & White Gothic Halloween — GitHub Profile SVG Generator
Monochrome ink-etching aesthetic. No purple. Steam-style clean headers.
"""
import re, urllib.request, urllib.parse, base64, json, random
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT   = Path(__file__).parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# ── COLOR PALETTE: Monochrome Gothic ───────────────────────
BG        = "#0D0D0D"   # Near-black
BG2       = "#161616"   # Slightly lighter panel
BG3       = "#1E1E1E"   # Card surface
BORDER    = "#2A2A2A"   # Subtle border
BORDER_LT = "#3A3A3A"   # Lighter border accent
TEXT_PRI  = "#E0E0E0"   # Primary text — warm white
TEXT_SEC  = "#999999"   # Secondary text
TEXT_DIM  = "#555555"   # Dim text
ACCENT    = "#C8C8C8"   # Light accent for headers
GOLD      = "#B8860B"   # Dark goldenrod for stars — the ONLY color accent
WHITE     = "#FFFFFF"

try:
    from datetime import timezone
    NOW = datetime.now(timezone.utc).strftime("%d %b %Y UTC")
except ImportError:
    NOW = datetime.utcnow().strftime("%d %b %Y UTC")

def get_icon_b64(idx):
    try:
        with open(ASSETS / f"processed_icons/icon_{idx}.png", "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")
    except:
        return ""

def svg_defs():
    return (
        '<defs>'
        '<linearGradient id="fadeEdge" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{BORDER}" stop-opacity="0"/>'
        f'<stop offset="15%" stop-color="{BORDER}" stop-opacity="0.6"/>'
        f'<stop offset="50%" stop-color="{BORDER}" stop-opacity="1"/>'
        f'<stop offset="85%" stop-color="{BORDER}" stop-opacity="0.6"/>'
        f'<stop offset="100%" stop-color="{BORDER}" stop-opacity="0"/>'
        '</linearGradient>'
        '</defs>'
    )

def svg_card_bg(w, h, icons=None):
    """Minimal dark card background with thin border and optional faded icons."""
    r = f'<rect width="{w}" height="{h}" rx="6" fill="{BG}"/>'
    r += f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="5" fill="none" stroke="{BORDER}" stroke-width="1"/>'
    if icons:
        for (ib, x, y, s, o) in icons:
            if ib:
                r += f'<image href="{ib}" x="{x}" y="{y}" width="{s}" height="{s}" opacity="{o}"/>'
    return r

def svg_steam_header(w, label):
    """Steam-style header bar — clean, no emoji, just text with thin line."""
    return (
        f'<rect x="0" y="0" width="{w}" height="38" rx="6" fill="{BG2}"/>'
        f'<rect x="0" y="30" width="{w}" height="8" fill="{BG2}"/>'
        f'<text x="18" y="25" font-family="Georgia, serif" font-size="11" fill="{ACCENT}" '
        f'letter-spacing="3" font-weight="400" text-transform="uppercase">{label}</text>'
        f'<line x1="15" y1="38" x2="{w-15}" y2="38" stroke="{BORDER_LT}" stroke-width="0.5"/>'
    )

def svg_footer(w, h):
    return (
        f'<line x1="15" y1="{h-20}" x2="{w-15}" y2="{h-20}" stroke="{BORDER}" stroke-width="0.3"/>'
        f'<text x="{w-12}" y="{h-7}" font-family="Georgia, serif" font-size="8" fill="{TEXT_DIM}" '
        f'text-anchor="end" font-style="italic">{NOW}</text>'
    )

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def trunc(s, n):
    s = s.strip()
    return esc(s[:n-1] + "\u2026") if len(s) > n else esc(s)

def fetch_xml(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return ET.fromstring(r.read())
    except:
        return None

def get_b64_image(url):
    if not url: return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ctype = r.headers.get('Content-Type', 'image/jpeg')
            b64 = base64.b64encode(r.read()).decode('utf-8')
            return f"data:{ctype};base64,{b64}"
    except:
        return ""


# ═══════════════════════════════════════════════════════════
#  HEADER BANNER — Clean monochrome with scattered stickers
# ═══════════════════════════════════════════════════════════
def header_banner():
    W, H = 800, 180
    icon_tl = get_icon_b64(2)
    icon_tr = get_icon_b64(3)
    icon_bl = get_icon_b64(6)
    icon_br = get_icon_b64(1)
    corners = []
    if icon_tl: corners.append((icon_tl, 12, 10, 75, 0.35))
    if icon_tr: corners.append((icon_tr, W-87, 10, 75, 0.35))
    if icon_bl: corners.append((icon_bl, 25, H-65, 50, 0.2))
    if icon_br: corners.append((icon_br, W-75, H-65, 50, 0.2))

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'{svg_card_bg(W, H, icons=corners)}'
        # Title
        f'<text x="{W//2}" y="82" text-anchor="middle" font-family="Georgia, serif" font-size="40" font-weight="700" fill="{WHITE}">Rakhim Nuraliyev</text>'
        # Thin ornamental line
        f'<line x1="{W//2-100}" y1="100" x2="{W//2+100}" y2="100" stroke="url(#fadeEdge)" stroke-width="1"/>'
        # Subtitle
        f'<text x="{W//2}" y="120" text-anchor="middle" font-family="Georgia, serif" font-size="12" fill="{TEXT_SEC}" font-style="italic" letter-spacing="2">PDP University \u2014 B.S. Software Development</text>'
        # Bottom tagline
        f'<text x="{W//2}" y="155" text-anchor="middle" font-family="Georgia, serif" font-size="9" fill="{TEXT_DIM}" letter-spacing="6">SOFTWARE ENGINEER \u00b7 GAME DEV \u00b7 CREATIVE</text>'
        f'</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  DIVIDER — Minimal ornamental
# ═══════════════════════════════════════════════════════════
def divider_svg():
    W, H = 800, 20
    mid = W // 2
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'<line x1="100" y1="{H//2}" x2="{W-100}" y2="{H//2}" stroke="url(#fadeEdge)" stroke-width="0.5"/>'
        f'<circle cx="{mid}" cy="{H//2}" r="2" fill="{BORDER_LT}"/>'
        f'<circle cx="{mid-30}" cy="{H//2}" r="1" fill="{BORDER}" opacity="0.5"/>'
        f'<circle cx="{mid+30}" cy="{H//2}" r="1" fill="{BORDER}" opacity="0.5"/>'
        f'</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  INFO CARD — Clean dark card (no parchment)
# ═══════════════════════════════════════════════════════════
def info_card():
    W, H = 800, 310
    lines_data = [
        ("name:", "Rakhim Nuraliyev"),
        ("education:", "PDP University \u2014 B.S. Software Development"),
        ("age:", "19"),
        ("", ""),
        ("experience:", ""),
        ("  -", "{ role: SWE Intern, org: UIC Games }"),
        ("  -", "{ role: Full-Stack Dev, org: BOGATIR Textile }"),
        ("", ""),
        ("events:", ""),
        ("  2026:", ""),
        ("    -", "ICT WEEK \u00b7 GameFest \u00b7 ETHOnline Hackathon"),
        ("    -", "35 LVL Game Jam \u00b7 GDG Build with AI"),
        ("    -", "PAYNET x ITPU Hackathon  # Team Mars"),
        ("  2025:", ""),
        ("    -", "GDG DevFest Uzbekistan"),
    ]
    icon_deco = get_icon_b64(9)
    icons = []
    if icon_deco: icons.append((icon_deco, W-100, 15, 65, 0.12))

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'{svg_card_bg(W, H, icons=icons)}'
        f'{svg_steam_header(W, "PROFILE")}'
    )
    
    y_start = 60
    line_h = 17
    for i, (key, val) in enumerate(lines_data):
        y = y_start + i * line_h
        if key:
            result += f'<text x="22" y="{y}" font-family="Consolas, monospace" font-size="12" fill="{ACCENT}" font-weight="700">{esc(key)}</text>'
        if val:
            x_off = 22 + len(key) * 7.2 + 6 if key else 22
            result += f'<text x="{x_off}" y="{y}" font-family="Consolas, monospace" font-size="12" fill="{TEXT_SEC}">{esc(val)}</text>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  GOODREADS
# ═══════════════════════════════════════════════════════════
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
                books.append((trunc(t, 50), trunc(a, 35), pub, b64))
            else:
                books.append((trunc(raw, 50), "", pub, b64))
    if not books:
        books = [("No books currently reading", "", "", "")]

    W, ROW_H, Y0 = 800, 72, 55
    H = Y0 + len(books) * ROW_H + 25
    icon = get_icon_b64(0)
    icons = []
    if icon: icons.append((icon, W-75, 5, 40, 0.15))

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'{svg_card_bg(W, H, icons=icons)}'
        f'{svg_steam_header(W, "CURRENTLY READING")}'
    )
    
    for i, (t, a, pub, img) in enumerate(books):
        y = Y0 + i * ROW_H
        if img:
            result += f'<rect x="17" y="{y+3}" width="42" height="62" rx="2" fill="{BORDER}"/>'
            result += f'<image x="18" y="{y+4}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            result += f'<rect x="18" y="{y+4}" width="40" height="60" rx="2" fill="{BG3}"/>'
        result += f'<text x="72" y="{y+26}" font-family="Georgia, serif" font-size="14" fill="{TEXT_PRI}" font-weight="600">{t}</text>'
        sub = []
        if a: sub.append(f"by {a}")
        if pub: sub.append(f"({pub})")
        if sub:
            result += f'<text x="72" y="{y+45}" font-family="Georgia, serif" font-size="11" fill="{TEXT_SEC}" font-style="italic">{" ".join(sub)}</text>'
        if i < len(books)-1:
            result += f'<line x1="18" y1="{y+ROW_H}" x2="{W-18}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="0.5" stroke-dasharray="2,4"/>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  LAST.FM
# ═══════════════════════════════════════════════════════════
def lastfm_card():
    API_KEY = "b25b959554ed76058ac220b7b2e0a026"
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user=ajaxmanson&api_key={API_KEY}&period=1month&format=json&limit=15"
    tag_counts = {}
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
            for a in data.get("topartists", {}).get("artist", []):
                name = a.get("name")
                scrobbles = int(a.get("playcount", 0))
                a_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={urllib.parse.quote(name)}&api_key={API_KEY}&format=json"
                try:
                    a_req = urllib.request.Request(a_url, headers={"User-Agent":"Mozilla/5.0"})
                    with urllib.request.urlopen(a_req, timeout=10) as ar:
                        for t in json.loads(ar.read()).get("toptags", {}).get("tag", [])[:3]:
                            tn = t.get("name").lower()
                            tag_counts[tn] = tag_counts.get(tn, 0) + scrobbles
                except:
                    pass
    except:
        pass

    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    if not sorted_tags:
        sorted_tags = [("just chilling... no music lately", 1)]
    max_score = sorted_tags[0][1] if sorted_tags[0][1] > 0 else 1

    W, ROW_H, Y0 = 800, 50, 55
    H = Y0 + len(sorted_tags) * ROW_H + 25
    icon = get_icon_b64(5)
    icons = []
    if icon: icons.append((icon, W-75, 5, 40, 0.15))
    # Monochrome gradient bars — white to gray
    bar_shades = ["#E0E0E0", "#BBBBBB", "#999999", "#777777", "#555555"]

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'{svg_card_bg(W, H, icons=icons)}'
        f'{svg_steam_header(W, "TOP TAGS \u00b7 LAST 30 DAYS")}'
    )
    
    for i, (tag, score) in enumerate(sorted_tags):
        y = Y0 + i * ROW_H
        shade = bar_shades[i % len(bar_shades)]
        result += f'<text x="22" y="{y+30}" font-family="Georgia, serif" font-size="14" fill="{TEXT_PRI}" font-weight="600">{esc(tag)}</text>'
        if tag != "just chilling... no music lately":
            bar_max = 440
            bar_width = max(18, int((score / max_score) * bar_max))
            bar_x = W - 22 - bar_max
            result += f'<rect x="{bar_x}" y="{y+16}" width="{bar_max}" height="18" rx="9" fill="{BG3}"/>'
            result += f'<rect x="{bar_x}" y="{y+16}" width="{bar_width}" height="18" rx="9" fill="{shade}" opacity="0.7"/>'
            result += f'<text x="{bar_x+10}" y="{y+30}" font-family="Georgia, serif" font-size="9" fill="{BG}" font-weight="700">~{score}</text>'
        if i < len(sorted_tags)-1:
            result += f'<line x1="22" y1="{y+ROW_H}" x2="{W-22}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="0.3" stroke-dasharray="2,4"/>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  LETTERBOXD
# ═══════════════════════════════════════════════════════════
def star_str(rating_str):
    if not rating_str: return ""
    try:
        r = float(rating_str)
        full = int(r)
        half = 1 if (r - full) >= 0.5 else 0
        empty = 5 - full - half
        return "\u2605" * full + ("\u00bd" if half else "") + "\u2606" * empty
    except:
        return ""

def letterboxd_card():
    LB = "https://letterboxd.com"
    root = fetch_xml("https://letterboxd.com/ajax_rn/rss/")
    films = []
    if root is not None:
        ch = root.find("channel")
        for item in (ch.findall("item") if ch is not None else [])[:5]:
            raw = (item.findtext("title") or "").strip()
            title = re.sub(r"\s*-\s*[\u2605\u00bd\u2606]+.*$", "", raw).strip()
            rating = item.findtext(f"{{{LB}}}memberRating") or item.findtext(f"{{{LB}}}rating") or ""
            desc_html = item.findtext("description") or ""
            img_url = ""
            m = re.search(r'<img.*?src="(.*?)"', desc_html)
            if m: img_url = m.group(1)
            b64 = get_b64_image(img_url)
            films.append((trunc(title, 50), star_str(rating), b64))
    if not films:
        films = [("No recent films found", "", "")]

    W, ROW_H, Y0 = 800, 72, 55
    H = Y0 + len(films) * ROW_H + 25
    icon = get_icon_b64(4)
    icons = []
    if icon: icons.append((icon, W-75, 5, 40, 0.15))

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'{svg_card_bg(W, H, icons=icons)}'
        f'{svg_steam_header(W, "RECENTLY WATCHED")}'
    )
    
    for i, (film, stars, img) in enumerate(films):
        y = Y0 + i * ROW_H
        if img:
            result += f'<rect x="17" y="{y+3}" width="42" height="62" rx="2" fill="{BORDER}"/>'
            result += f'<image x="18" y="{y+4}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            result += f'<rect x="18" y="{y+4}" width="40" height="60" rx="2" fill="{BG3}"/>'
        result += f'<text x="72" y="{y+35}" font-family="Georgia, serif" font-size="14" fill="{TEXT_PRI}" font-weight="600">{film}</text>'
        if stars:
            result += f'<text x="{W-22}" y="{y+35}" text-anchor="end" font-family="Georgia, serif" font-size="14" fill="{GOLD}">{esc(stars)}</text>'
        if i < len(films)-1:
            result += f'<line x1="18" y1="{y+ROW_H}" x2="{W-18}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="0.5" stroke-dasharray="2,4"/>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  FOOTER BANNER
# ═══════════════════════════════════════════════════════════
def footer_banner():
    W, H = 800, 50
    icon_a = get_icon_b64(8)
    icon_b = get_icon_b64(4)
    r = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_defs()}'
        f'<rect width="{W}" height="{H}" fill="{BG}"/>'
        f'<line x1="100" y1="15" x2="{W-100}" y2="15" stroke="url(#fadeEdge)" stroke-width="0.5"/>'
    )
    if icon_a:
        r += f'<image href="{icon_a}" x="15" y="5" width="38" height="38" opacity="0.15"/>'
    if icon_b:
        r += f'<image href="{icon_b}" x="{W-53}" y="5" width="38" height="38" opacity="0.15"/>'
    r += (
        f'<text x="{W//2}" y="35" text-anchor="middle" font-family="Georgia, serif" font-size="9" fill="{TEXT_DIM}" letter-spacing="4" font-style="italic">'
        f'crafted with dark magic</text>'
        f'</svg>'
    )
    return r


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Generating Black & White Gothic profile assets...")
    (ASSETS / "header_banner.svg").write_text(header_banner(), encoding="utf-8")
    print("  done: header_banner.svg")
    (ASSETS / "divider.svg").write_text(divider_svg(), encoding="utf-8")
    print("  done: divider.svg")
    (ASSETS / "info_card.svg").write_text(info_card(), encoding="utf-8")
    print("  done: info_card.svg")
    (ASSETS / "goodreads_card.svg").write_text(goodreads_card(), encoding="utf-8")
    print("  done: goodreads_card.svg")
    (ASSETS / "lastfm_card.svg").write_text(lastfm_card(), encoding="utf-8")
    print("  done: lastfm_card.svg")
    (ASSETS / "letterboxd_card.svg").write_text(letterboxd_card(), encoding="utf-8")
    print("  done: letterboxd_card.svg")
    (ASSETS / "footer_banner.svg").write_text(footer_banner(), encoding="utf-8")
    print("  done: footer_banner.svg")
    print("\nAll B&W Gothic assets generated.")
