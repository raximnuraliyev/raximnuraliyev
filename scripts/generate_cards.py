#!/usr/bin/env python3
"""
Illustrated Cozy Gothic Adventure — GitHub Profile SVG Generator
Generates all SVG assets for raximnuraliyev's Halloween-themed profile.
"""
import re, urllib.request, urllib.parse, base64, json, random
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT   = Path(__file__).parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# ── COLOR PALETTE: Illustrated Cozy Gothic ─────────────────
BG        = "#1A0F2B"
BG2       = "#120A1F"
BG3       = "#241540"
BORDER    = "#3D2A5C"
GLOW      = "#4ADE80"
ORANGE    = "#F97316"
PARCHMENT = "#F7E7C8"
TEXT_PRI  = "#E8D5B5"
TEXT_MUT  = "#9B8BB0"
TEXT_FAINT= "#5C4A7A"
GOLD      = "#D4A843"
CRIMSON   = "#8B2252"

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

def svg_gothic_defs(w, h):
    return (
        '<defs>'
        '<radialGradient id="bgGlow" cx="50%" cy="40%" r="70%">'
        '<stop offset="0%" stop-color="#2A1845"/>'
        f'<stop offset="60%" stop-color="{BG}"/>'
        '<stop offset="100%" stop-color="#0D0718"/>'
        '</radialGradient>'
        '<filter id="greenGlow" x="-20%" y="-20%" width="140%" height="140%">'
        '<feGaussianBlur stdDeviation="2" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
        '<filter id="orangeGlow" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="4" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
        '</defs>'
    )

def svg_gothic_bg(w, h, corner_icons=None):
    result = f'<rect width="{w}" height="{h}" rx="12" fill="url(#bgGlow)"/>'
    result += f'<rect x="2" y="2" width="{w-4}" height="{h-4}" rx="10" fill="none" stroke="{BORDER}" stroke-width="1.5" stroke-dasharray="4,2"/>'
    result += f'<rect x="5" y="5" width="{w-10}" height="{h-10}" rx="8" fill="none" stroke="{BORDER}" stroke-width="0.5" opacity="0.5"/>'
    random.seed(42)
    for _ in range(15):
        fx, fy = random.randint(10, w-10), random.randint(10, h-10)
        fr, fo = random.uniform(1, 3), random.uniform(0.05, 0.15)
        result += f'<circle cx="{fx}" cy="{fy}" r="{fr:.1f}" fill="{GLOW}" opacity="{fo:.2f}"/>'
    if corner_icons:
        for (ib, x, y, s, o) in corner_icons:
            if ib:
                result += f'<image href="{ib}" x="{x}" y="{y}" width="{s}" height="{s}" opacity="{o}"/>'
    return result

def svg_header_bar(w, label, color=None):
    c = color or GLOW
    return (
        f'<rect x="5" y="5" width="{w-10}" height="36" rx="4" fill="{BG2}"/>'
        f'<rect x="5" y="33" width="{w-10}" height="8" rx="0" fill="{BG2}"/>'
        f'<line x1="20" y1="41" x2="{w-20}" y2="41" stroke="{BORDER}" stroke-width="1"/>'
        f'<text x="20" y="28" font-family="Georgia, serif" font-size="11" fill="{c}" '
        f'letter-spacing="2" font-weight="700" filter="url(#greenGlow)">{label}</text>'
    )

def svg_footer(w, h):
    return (
        f'<line x1="20" y1="{h-22}" x2="{w-20}" y2="{h-22}" stroke="{BORDER}" stroke-width="0.5" opacity="0.5"/>'
        f'<text x="{w-15}" y="{h-8}" font-family="Georgia, serif" font-size="8" fill="{TEXT_FAINT}" '
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
#  HEADER BANNER
# ═══════════════════════════════════════════════════════════
def header_banner():
    W, H = 800, 200
    icon_tl = get_icon_b64(2)
    icon_tr = get_icon_b64(3)
    icon_bl = get_icon_b64(6)
    icon_br = get_icon_b64(1)
    corners = []
    if icon_tl: corners.append((icon_tl, 15, 15, 80, 0.4))
    if icon_tr: corners.append((icon_tr, W-95, 15, 80, 0.4))
    if icon_bl: corners.append((icon_bl, 30, H-75, 55, 0.25))
    if icon_br: corners.append((icon_br, W-85, H-75, 55, 0.25))

    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_gothic_defs(W, H)}'
        f'{svg_gothic_bg(W, H, corner_icons=corners)}'
        f'<text x="{W//2}" y="90" text-anchor="middle" font-family="Georgia, serif" font-size="42" font-weight="700" fill="{ORANGE}" opacity="0.3" filter="url(#orangeGlow)">Rakhim Nuraliyev</text>'
        f'<text x="{W//2}" y="90" text-anchor="middle" font-family="Georgia, serif" font-size="42" font-weight="700" fill="{PARCHMENT}">Rakhim Nuraliyev</text>'
        f'<text x="{W//2}" y="120" text-anchor="middle" font-family="Georgia, serif" font-size="13" fill="{GLOW}" font-style="italic" filter="url(#greenGlow)" letter-spacing="3">PDP University \u2014 B.S. Software Development</text>'
        f'<line x1="{W//2-120}" y1="135" x2="{W//2+120}" y2="135" stroke="{BORDER}" stroke-width="1"/>'
        f'<circle cx="{W//2}" cy="135" r="3" fill="{GLOW}" opacity="0.5"/>'
        f'<circle cx="{W//2-120}" cy="135" r="2" fill="{ORANGE}" opacity="0.4"/>'
        f'<circle cx="{W//2+120}" cy="135" r="2" fill="{ORANGE}" opacity="0.4"/>'
        f'<text x="{W//2}" y="165" text-anchor="middle" font-family="Georgia, serif" font-size="10" fill="{TEXT_MUT}" letter-spacing="5">\u2620 ILLUSTRATED COZY GOTHIC ADVENTURE \u2620</text>'
        f'</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  DIVIDER
# ═══════════════════════════════════════════════════════════
def divider_svg():
    W, H = 800, 30
    mid = W // 2
    return (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="divFade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0%" stop-color="{BORDER}" stop-opacity="0"/>'
        f'<stop offset="30%" stop-color="{BORDER}" stop-opacity="1"/>'
        f'<stop offset="70%" stop-color="{BORDER}" stop-opacity="1"/>'
        f'<stop offset="100%" stop-color="{BORDER}" stop-opacity="0"/>'
        f'</linearGradient></defs>'
        f'<line x1="50" y1="{H//2}" x2="{W-50}" y2="{H//2}" stroke="url(#divFade)" stroke-width="1"/>'
        f'<polygon points="{mid},{H//2-6} {mid+6},{H//2} {mid},{H//2+6} {mid-6},{H//2}" fill="{BG}" stroke="{GLOW}" stroke-width="1"/>'
        f'<circle cx="{mid}" cy="{H//2}" r="2" fill="{GLOW}" opacity="0.6"/>'
        f'<circle cx="{mid-40}" cy="{H//2}" r="1.5" fill="{ORANGE}" opacity="0.4"/>'
        f'<circle cx="{mid+40}" cy="{H//2}" r="1.5" fill="{ORANGE}" opacity="0.4"/>'
        f'<circle cx="{mid-80}" cy="{H//2}" r="1" fill="{BORDER}" opacity="0.6"/>'
        f'<circle cx="{mid+80}" cy="{H//2}" r="1" fill="{BORDER}" opacity="0.6"/>'
        f'</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  PARCHMENT INFO CARD
# ═══════════════════════════════════════════════════════════
def info_card():
    W, H = 800, 340
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
    icon_scroll = get_icon_b64(9)
    
    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_gothic_defs(W, H)}'
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#bgGlow)"/>'
        f'<rect x="3" y="3" width="{W-6}" height="{H-6}" rx="10" fill="none" stroke="{BORDER}" stroke-width="1.5" stroke-dasharray="4,2"/>'
        f'<rect x="30" y="25" width="{W-60}" height="{H-50}" rx="6" fill="{PARCHMENT}" opacity="0.92"/>'
        f'<rect x="30" y="25" width="{W-60}" height="{H-50}" rx="6" fill="none" stroke="#8B7355" stroke-width="2"/>'
        f'<rect x="33" y="28" width="{W-66}" height="{H-56}" rx="4" fill="none" stroke="#A08060" stroke-width="0.5" opacity="0.5"/>'
        f'<ellipse cx="{W//2}" cy="25" rx="{(W-60)//2}" ry="6" fill="#D4C4A0"/>'
        f'<ellipse cx="{W//2}" cy="25" rx="{(W-60)//2}" ry="4" fill="{PARCHMENT}"/>'
        f'<ellipse cx="{W//2}" cy="{H-25}" rx="{(W-60)//2}" ry="6" fill="#D4C4A0"/>'
        f'<ellipse cx="{W//2}" cy="{H-25}" rx="{(W-60)//2}" ry="4" fill="{PARCHMENT}"/>'
    )
    
    if icon_scroll:
        result += f'<image href="{icon_scroll}" x="{W-130}" y="40" width="70" height="70" opacity="0.15"/>'
    
    y_start = 55
    line_h = 18
    for i, (key, val) in enumerate(lines_data):
        y = y_start + i * line_h
        if key:
            result += f'<text x="55" y="{y}" font-family="Georgia, serif" font-size="12" fill="#4F2421" font-weight="700">{esc(key)}</text>'
        if val:
            x_off = 55 + len(key) * 7.2 + 5 if key else 55
            result += f'<text x="{x_off}" y="{y}" font-family="Georgia, serif" font-size="12" fill="#6D472F">{esc(val)}</text>'
    
    random.seed(99)
    for _ in range(10):
        fx = random.randint(5, W-5)
        fy = random.choice(list(range(5, 25)) + list(range(H-25, H-5)))
        fr = random.uniform(1, 2.5)
        result += f'<circle cx="{fx}" cy="{fy}" r="{fr:.1f}" fill="{GLOW}" opacity="0.08"/>'
    
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  GOODREADS — Leatherbound Tome
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

    W, ROW_H, Y0 = 800, 75, 70
    H = Y0 + len(books) * ROW_H + 30
    icon_tome = get_icon_b64(0)
    corners = []
    if icon_tome: corners.append((icon_tome, W-90, 8, 50, 0.25))

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_gothic_defs(W, H)}'
        f'{svg_gothic_bg(W, H, corner_icons=corners)}'
        f'<rect x="5" y="5" width="12" height="{H-10}" rx="2" fill="#3D2211" opacity="0.6"/>'
        f'<line x1="11" y1="10" x2="11" y2="{H-10}" stroke="#5C3A20" stroke-width="1" opacity="0.5"/>'
        f'{svg_header_bar(W, "\U0001F4D6 CURRENTLY READING \u00b7 goodreads.com/202996478-ajax", GLOW)}'
    )
    
    for i, (t, a, pub, img) in enumerate(books):
        y = Y0 + i * ROW_H
        if img:
            result += f'<rect x="28" y="{y+4}" width="44" height="64" rx="2" fill="{BORDER}" opacity="0.5"/>'
            result += f'<image x="30" y="{y+6}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            result += f'<rect x="30" y="{y+6}" width="40" height="60" rx="2" fill="{BG3}"/>'
        result += f'<text x="85" y="{y+28}" font-family="Georgia, serif" font-size="14" fill="{TEXT_PRI}" font-weight="600">{t}</text>'
        sub = []
        if a: sub.append(f"by {a}")
        if pub: sub.append(f"({pub})")
        if sub:
            result += f'<text x="85" y="{y+48}" font-family="Georgia, serif" font-size="11" fill="{TEXT_MUT}" font-style="italic">{" ".join(sub)}</text>'
        if i < len(books)-1:
            result += f'<line x1="30" y1="{y+ROW_H}" x2="{W-30}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="0.5" opacity="0.4" stroke-dasharray="3,3"/>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  LAST.FM — Cursed Music Record
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

    W, ROW_H, Y0 = 800, 55, 70
    H = Y0 + len(sorted_tags) * ROW_H + 30
    icon_music = get_icon_b64(5)
    corners = []
    if icon_music: corners.append((icon_music, W-85, 8, 45, 0.25))
    bar_colors = [GLOW, ORANGE, GOLD, CRIMSON, TEXT_FAINT]

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_gothic_defs(W, H)}'
        f'{svg_gothic_bg(W, H, corner_icons=corners)}'
        f'<circle cx="30" cy="{H//2}" r="15" fill="none" stroke="{BORDER}" stroke-width="0.5" opacity="0.3"/>'
        f'<circle cx="30" cy="{H//2}" r="10" fill="none" stroke="{BORDER}" stroke-width="0.5" opacity="0.2"/>'
        f'<circle cx="30" cy="{H//2}" r="5" fill="{GLOW}" opacity="0.1"/>'
        f'{svg_header_bar(W, "\U0001F3B5 TOP TAGS (LAST 30 DAYS) \u00b7 last.fm/user/ajaxmanson", ORANGE)}'
    )
    
    for i, (tag, score) in enumerate(sorted_tags):
        y = Y0 + i * ROW_H
        color = bar_colors[i % len(bar_colors)]
        result += f'<text x="30" y="{y+32}" font-family="Georgia, serif" font-size="15" fill="{TEXT_PRI}" font-weight="600">{esc(tag)}</text>'
        if tag != "just chilling... no music lately":
            bar_max = 460
            bar_width = max(20, int((score / max_score) * bar_max))
            bar_x = W - 30 - bar_max
            result += f'<rect x="{bar_x}" y="{y+18}" width="{bar_max}" height="20" rx="10" fill="{BG2}" opacity="0.8"/>'
            result += f'<rect x="{bar_x}" y="{y+18}" width="{bar_width}" height="20" rx="10" fill="{color}" opacity="0.8"/>'
            result += f'<text x="{bar_x+12}" y="{y+33}" font-family="Georgia, serif" font-size="10" fill="#ffffff" font-weight="700">~{score}</text>'
        if i < len(sorted_tags)-1:
            result += f'<line x1="30" y1="{y+ROW_H}" x2="{W-30}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="0.5" opacity="0.3" stroke-dasharray="3,3"/>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  LETTERBOXD — Skeletal Film Reel
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

    W, ROW_H, Y0 = 800, 75, 70
    H = Y0 + len(films) * ROW_H + 30
    icon_film = get_icon_b64(4)
    corners = []
    if icon_film: corners.append((icon_film, W-85, 8, 45, 0.25))

    result = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'{svg_gothic_defs(W, H)}'
        f'{svg_gothic_bg(W, H, corner_icons=corners)}'
        f'<rect x="5" y="5" width="14" height="{H-10}" rx="2" fill="{BG2}" opacity="0.5"/>'
    )
    for j in range(0, H-20, 20):
        result += f'<rect x="7" y="{j+8}" width="10" height="8" rx="2" fill="{BG}" opacity="0.6"/>'
    
    result += svg_header_bar(W, "\U0001F3AC RECENTLY WATCHED \u00b7 letterboxd.com/ajax_rn", CRIMSON)
    
    for i, (film, stars, img) in enumerate(films):
        y = Y0 + i * ROW_H
        if img:
            result += f'<rect x="28" y="{y+4}" width="44" height="64" rx="2" fill="{BORDER}" opacity="0.5"/>'
            result += f'<image x="30" y="{y+6}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{img}"/>'
        else:
            result += f'<rect x="30" y="{y+6}" width="40" height="60" rx="2" fill="{BG3}"/>'
        result += f'<text x="85" y="{y+35}" font-family="Georgia, serif" font-size="14" fill="{TEXT_PRI}" font-weight="600">{film}</text>'
        if stars:
            result += f'<text x="{W-30}" y="{y+35}" text-anchor="end" font-family="Georgia, serif" font-size="14" fill="{GOLD}">{esc(stars)}</text>'
        if i < len(films)-1:
            result += f'<line x1="30" y1="{y+ROW_H}" x2="{W-30}" y2="{y+ROW_H}" stroke="{BORDER}" stroke-width="0.5" opacity="0.4" stroke-dasharray="3,3"/>'
    
    result += svg_footer(W, H)
    result += '</svg>'
    return result


# ═══════════════════════════════════════════════════════════
#  FOOTER BANNER
# ═══════════════════════════════════════════════════════════
def footer_banner():
    W, H = 800, 60
    icon_a = get_icon_b64(8)
    icon_b = get_icon_b64(4)
    r = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs><linearGradient id="footGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{BG}" stop-opacity="0"/>'
        f'<stop offset="100%" stop-color="#0D0718"/>'
        f'</linearGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="url(#footGrad)"/>'
    )
    if icon_a:
        r += f'<image href="{icon_a}" x="20" y="5" width="45" height="45" opacity="0.2"/>'
    if icon_b:
        r += f'<image href="{icon_b}" x="{W-65}" y="5" width="45" height="45" opacity="0.2"/>'
    r += (
        f'<text x="{W//2}" y="35" text-anchor="middle" font-family="Georgia, serif" font-size="10" fill="{TEXT_FAINT}" letter-spacing="3" font-style="italic">'
        f'\u2620 crafted with dark magic \u2620</text>'
        f'</svg>'
    )
    return r


# ═══════════════════════════════════════════════════════════
#  GENERATE ALL
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Generating Illustrated Cozy Gothic profile assets...")
    (ASSETS / "header_banner.svg").write_text(header_banner(), encoding="utf-8")
    print("  \u2713 header_banner.svg")
    (ASSETS / "divider.svg").write_text(divider_svg(), encoding="utf-8")
    print("  \u2713 divider.svg")
    (ASSETS / "info_card.svg").write_text(info_card(), encoding="utf-8")
    print("  \u2713 info_card.svg")
    (ASSETS / "goodreads_card.svg").write_text(goodreads_card(), encoding="utf-8")
    print("  \u2713 goodreads_card.svg")
    (ASSETS / "lastfm_card.svg").write_text(lastfm_card(), encoding="utf-8")
    print("  \u2713 lastfm_card.svg")
    (ASSETS / "letterboxd_card.svg").write_text(letterboxd_card(), encoding="utf-8")
    print("  \u2713 letterboxd_card.svg")
    (ASSETS / "footer_banner.svg").write_text(footer_banner(), encoding="utf-8")
    print("  \u2713 footer_banner.svg")
    print("\n\U0001F383 All Illustrated Cozy Gothic assets generated!")
