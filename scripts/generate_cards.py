#!/usr/bin/env python3
"""
Gothic Halloween — GitHub Profile SVG Generator

The README is one continuous dark canvas cut into horizontal slices.
Every slice is 800 units wide, painted the same BG colour, and stacked with
no gaps, so the etched frame (assets/ornaments/frame_*.png) and the thin side
rules flow from slice to slice. Ornament PNGs come from process_icons.py.
"""
import re, urllib.request, urllib.parse, base64, json
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT     = Path(__file__).parent.parent
ASSETS   = ROOT / "assets"
ORN      = ASSETS / "ornaments"

# ── PALETTE ────────────────────────────────────────────────
BG        = "#0B0B0C"   # the one canvas colour, everywhere
LINE      = "#2E2C29"   # panel borders
LINE_LT   = "#4A4741"   # ornamental accents
TEXT_PRI  = "#E8E2D6"   # bone white
TEXT_SEC  = "#9A948A"   # aged paper grey
TEXT_DIM  = "#5E5A54"
PUMPKIN   = "#E8742A"   # the only warm accent
GOLD      = "#C9A44C"   # star ratings

W     = 800
RULE_L, RULE_R = 40, 760          # continuous side rules
FRAME_S = W / 675                 # frame PNGs are 675 px wide
FRAME_TOP_H = round(670 * FRAME_S)
FRAME_BOT_H = round(530 * FRAME_S)
HEADER_H  = 560
PROFILE_H = 460

NOW = datetime.now(timezone.utc).strftime("%d %b %Y")

TITLE_FONT = "Creepster, 'Chiller', fantasy"
SERIF      = "Georgia, 'Times New Roman', serif"
MONO       = "Consolas, 'Courier New', monospace"


# ── helpers ────────────────────────────────────────────────
_cache = {}
def orn(name):
    """Base64 data URI for an ornament PNG."""
    if name not in _cache:
        try:
            _cache[name] = "data:image/png;base64," + base64.b64encode((ORN / f"{name}.png").read_bytes()).decode()
        except OSError:
            _cache[name] = ""
    return _cache[name]

def creepster_face():
    try:
        b = base64.b64encode((ROOT / "Creepster.ttf").read_bytes()).decode()
        return f"@font-face{{font-family:Creepster;src:url(data:font/ttf;base64,{b}) format('truetype');}}"
    except OSError:
        return ""

FELL = "'IM Fell English', Georgia, serif"

def fell_faces():
    """IM Fell English (OFL), trimmed to the glyphs the header uses."""
    out = ""
    for style, f in (("normal", "imfell-rm.ttf"), ("italic", "imfell-it.ttf")):
        try:
            b = base64.b64encode((ASSETS / "fonts" / f).read_bytes()).decode()
        except OSError:
            continue
        out += (f"@font-face{{font-family:'IM Fell English';font-style:{style};"
                f"src:url(data:font/ttf;base64,{b}) format('truetype');}}")
    return out

def lighten(hex_color, min_lum=0.32):
    """Brand colours too dark to glow on the canvas get mixed toward white."""
    r, g, b = (int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    if lum >= min_lum:
        return hex_color
    t = (min_lum - lum) / (1 - lum) + 0.15
    r, g, b = (round(c + (255 - c) * t) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"

def glow_css(period):
    """Items fade up in their brand colour, hold, then sink back to grey.
    Stagger them with animation-delay to get a wave. (GitHub renders README
    SVGs as images, so there's no hover — this lights them up on its own.)"""
    return (f".lit{{opacity:0;animation:lit {period}s ease-in-out infinite}}"
            "@keyframes lit{0%{opacity:0}7%,17%{opacity:1}28%,100%{opacity:0}}")

GLOW_FILTER = ('<filter id="bloom" x="-30%" y="-60%" width="160%" height="220%">'
               '<feGaussianBlur stdDeviation="4"/></filter>')

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def trunc(s, n):
    s = s.strip()
    return esc(s[:n-1] + "…") if len(s) > n else esc(s)

def png_size(name):
    """(width, height) straight from the PNG header."""
    with open(ORN / f"{name}.png", "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")

def img(name, x, y, w, h=None, opacity=1, extra=""):
    uri = orn(name)
    if not uri: return ""
    if h is None:   # explicit height keeps masks/transform boxes exact
        pw, ph = png_size(name)
        h = round(w * ph / pw, 1)
    return f'<image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h}" opacity="{opacity}" {extra}/>'

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"

def svg_open(h, font=False, defs="", css=""):
    face = creepster_face() if font else ""
    style = f"<style>{face}{css}{REDUCED_MOTION if css else ''}</style>" if (face or css) else ""
    return (
        f'<svg width="{W}" height="{h}" viewBox="0 0 {W} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>{style}'
        '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{LINE_LT}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{LINE_LT}"/>'
        f'<stop offset="1" stop-color="{LINE_LT}" stop-opacity="0"/>'
        '</linearGradient>'
        f'{defs}</defs>'
        f'<rect width="{W}" height="{h}" fill="{BG}"/>'
    )

def side_rules(h, l=(0, None), r=(0, None)):
    """Thin double rules down both edges; (start, end) in slice-local y."""
    out = ""
    for x, (y0, y1) in ((RULE_L, l), (RULE_R, r)):
        if y0 is None: continue
        y1 = h if y1 is None else y1
        out += (f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="{LINE_LT}" stroke-width=".8"/>'
                f'<line x1="{x+4 if x < W/2 else x-4}" y1="{y0}" x2="{x+4 if x < W/2 else x-4}" y2="{y1}" '
                f'stroke="{LINE}" stroke-width=".5"/>')
    return out

def vignette_defs(cx=.6, cy=.42):
    """Mask that dissolves a photo's edges into the canvas (use mask="url(#vig)")."""
    return (f'<radialGradient id="vigG" cx="{cx}" cy="{cy}" r=".62">'
            '<stop offset=".45" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
            '<mask id="vig" maskContentUnits="objectBoundingBox">'
            '<rect width="1" height="1" fill="url(#vigG)"/></mask>')

# little looping motions shared by several slices
SWAY  = (".sway{transform-box:fill-box;transform-origin:50% 0;animation:sway 6s ease-in-out infinite}"
         "@keyframes sway{0%,100%{transform:rotate(-2deg)}50%{transform:rotate(2deg)}}")
BOB   = (".bob{animation:bob 4.5s ease-in-out infinite}"
         "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}")
BLINK = (".blink{transform-box:fill-box;transform-origin:50% 50%;animation:blink 8s ease-in-out infinite}"
         "@keyframes blink{0%,45%,51%,100%{transform:scaleY(1)}48%{transform:scaleY(.06)}}")
DANGLE = (".dangle{animation:dangle 7s ease-in-out infinite}"
          "@keyframes dangle{0%,100%{transform:translateY(0)}40%{transform:translateY(34px)}"
          "55%{transform:translateY(30px)}}")

def diamond(cx, cy, r=3.5, fill=LINE_LT):
    return f'<path d="M{cx} {cy-r} L{cx+r} {cy} L{cx} {cy+r} L{cx-r} {cy} Z" fill="{fill}"/>'

def heading(y, text, size=30):
    """Creepster section title with fading ornamental rules."""
    half = len(text) * size * 0.27 + 24
    cx = W // 2
    return (
        f'<text x="{cx}" y="{y}" text-anchor="middle" font-family="{TITLE_FONT}" font-size="{size}" '
        f'fill="{TEXT_PRI}" letter-spacing="3">{esc(text)}</text>'
        f'<line x1="{cx-half-170}" y1="{y-size*0.32}" x2="{cx-half}" y2="{y-size*0.32}" stroke="url(#fade)"/>'
        f'<line x1="{cx+half}" y1="{y-size*0.32}" x2="{cx+half+170}" y2="{y-size*0.32}" stroke="url(#fade)"/>'
        f'{diamond(cx-half-6, y-size*0.32)}{diamond(cx+half+6, y-size*0.32)}'
    )

def panel(x, y, w, h):
    """Borderline panel — same colour as the canvas, just etched edges."""
    c = 10
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{LINE}" stroke-width="1"/>'
    for px, py, dx, dy in ((x, y, 1, 1), (x+w, y, -1, 1), (x, y+h, 1, -1), (x+w, y+h, -1, -1)):
        s += (f'<path d="M{px} {py+dy*c} L{px} {py} L{px+dx*c} {py}" fill="none" stroke="{TEXT_SEC}" stroke-width="1.2"/>'
              f'{diamond(px+dx*4, py+dy*4, 1.6, TEXT_SEC)}')
    return s

def card_title(x, y, text):
    return (f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="12" fill="{TEXT_SEC}" '
            f'letter-spacing="4">{esc(text)}</text>')

def stamp(x, y):
    return (f'<text x="{x}" y="{y}" text-anchor="end" font-family="{SERIF}" font-size="9" '
            f'fill="{TEXT_DIM}" font-style="italic">summoned {NOW}</text>')

def fetch_xml(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return ET.fromstring(r.read())
    except Exception:
        return None

def get_b64_image(url):
    if not url: return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ctype = r.headers.get('Content-Type', 'image/jpeg')
            return f"data:{ctype};base64,{base64.b64encode(r.read()).decode()}"
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════
#  HAUNTED NAME — letters rise out of the dark, float, flicker
#  like dying candles and drip. Pure CSS inside the SVG, so it
#  plays on GitHub (which renders README SVGs as <img>).
# ═══════════════════════════════════════════════════════════
# Creepster advance widths (units per 1024 em) — avoids needing fontTools in CI
CREEPSTER_ADV = {" ": 241, "A": 456, "E": 430, "H": 468, "I": 315, "K": 504, "L": 366,
                 "M": 672, "N": 529, "R": 474, "U": 497, "V": 440, "Y": 412}
NAME_SIZE, NAME_TRACK = 56, 5

HEADER_CSS = """
.rise{animation:rise 1.6s cubic-bezier(.2,.8,.2,1) both}
.ltr{transform-box:fill-box;transform-origin:50% 60%;
     animation:float 5.5s ease-in-out infinite,flicker 9s linear infinite}
.halo{animation:halo 4.5s ease-in-out infinite}
.drip{transform-box:fill-box;transform-origin:50% 0;animation:drip 5s cubic-bezier(.55,0,.9,.5) infinite}
.moon{animation:moon 8s ease-in-out infinite}
@keyframes rise{from{opacity:0;transform:translateY(22px);filter:blur(8px)}to{opacity:1;transform:none;filter:none}}
@keyframes float{0%,100%{transform:translateY(0) rotate(0)}25%{transform:translateY(-3px) rotate(-2deg)}
  50%{transform:translateY(-5px) rotate(0)}75%{transform:translateY(-2px) rotate(2deg)}}
@keyframes flicker{0%,86%,90%,94%,100%{opacity:1}87%{opacity:.2}88%{opacity:.85}89%{opacity:.1}92%{opacity:.6}}
@keyframes halo{0%,100%{opacity:.18}50%{opacity:.5}}
@keyframes drip{0%{transform:translateY(0) scaleY(.4);opacity:0}12%{opacity:1;transform:translateY(0) scaleY(1)}
  55%{transform:translateY(3px) scaleY(1.6);opacity:1}100%{transform:translateY(46px) scaleY(1);opacity:0}}
@keyframes moon{0%,100%{opacity:.85}50%{opacity:1}}
"""

def haunted_name(text, baseline):
    k = NAME_SIZE / 1024
    widths = [CREEPSTER_ADV.get(c, 450) * k for c in text]
    x = W / 2 - (sum(widths) + NAME_TRACK * (len(text) - 1)) / 2
    font = f'font-family="{TITLE_FONT}" font-size="{NAME_SIZE}"'
    halo, letters, drips = "", "", ""
    for i, (c, w) in enumerate(zip(text, widths)):
        if c != " ":
            ch = esc(c)
            # irregular but deterministic timing per letter
            fd, fl = (i * 0.37) % 2.4, 6 + (i * 1.7) % 5
            halo += f'<text x="{x:.1f}" y="{baseline}" {font}>{ch}</text>'
            letters += (f'<g class="rise" style="animation-delay:{0.15 + i * 0.08:.2f}s">'
                        f'<text class="ltr" x="{x:.1f}" y="{baseline}" {font} fill="{TEXT_PRI}" '
                        f'style="animation-delay:-{fd:.2f}s,-{(i * 2.3) % fl:.2f}s;animation-duration:{5 + (i % 3) * .8:.1f}s,{fl:.1f}s">'
                        f'{ch}</text></g>')
            if c in "KMY":
                cx = x + w * 0.45
                drips += (f'<ellipse class="drip" cx="{cx:.1f}" cy="{baseline + 3}" rx="2" ry="3.2" fill="{TEXT_PRI}" '
                          f'style="animation-delay:{1.8 + (i * 0.9) % 4:.1f}s"/>')
        x += w + NAME_TRACK
    return (f'<g class="halo" fill="{TEXT_PRI}" filter="url(#glow)">{halo}</g>'
            f'{letters}{drips}')


# ═══════════════════════════════════════════════════════════
#  HEADER — castle under a moon, inside the top of the frame
# ═══════════════════════════════════════════════════════════
def header_banner():
    H = HEADER_H
    defs = (
        '<radialGradient id="moon" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#8A8476"/>'
        '<stop offset=".35" stop-color="#4A4740" stop-opacity=".8"/>'
        '<stop offset=".7" stop-color="#22201D" stop-opacity=".5"/>'
        f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="sink" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset=".6" stop-color="#fff"/><stop offset="1" stop-color="#000"/>'
        '</linearGradient>'
        '<mask id="castleFade"><rect x="0" y="0" width="800" height="560" fill="url(#sink)"/></mask>'
    )
    defs += '<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="5"/></filter>'
    return (
        svg_open(H, font=True, defs=defs, css=fell_faces() + HEADER_CSS)
        + f'<circle class="moon" cx="430" cy="250" r="230" fill="url(#moon)"/>'
        + f'<g mask="url(#castleFade)">{img("castle", 170, 120, 420)}</g>'
        + side_rules(H, l=(300, None))
        + img("frame_top", 0, 0, W, FRAME_TOP_H)
        + haunted_name("RAKHIM NURALIYEV", 462)
        + f'<line x1="250" y1="482" x2="550" y2="482" stroke="url(#fade)"/>{diamond(400, 482)}'
        + f'<text x="{W//2}" y="508" text-anchor="middle" font-family="{FELL}" font-size="16" '
          f'fill="{TEXT_SEC}" font-style="italic" letter-spacing=".6">SWE Intern @ UIC Games · Full-Stack @ BOGATIR Textile</text>'
        + f'<text x="{W//2}" y="538" text-anchor="middle" font-family="{FELL}" font-size="11.5" '
          f'fill="#7A756D" letter-spacing="5">SOFTWARE ENGINEER · GAME DEV · CREATIVE</text>'
        + '</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  PROFILE — frame's right pendant still hanging down
# ═══════════════════════════════════════════════════════════
def info_card():
    H = PROFILE_H
    lines_data = [
        ("name:", "Rakhim Nuraliyev"),
        ("education:", "PDP University — B.S. Software Development"),
        ("age:", "19"),
        ("experience:", ""),
        ("  -", "{ role: SWE Intern, org: UIC Games }"),
        ("  -", "{ role: Full-Stack Dev, org: BOGATIR Textile }"),
        ("events:", ""),
        # oldest first, in the order they happened
        ("  2025:", ""),
        ("    -", "HackMars 1.0"),                       # Nov 20 – Dec 23
        ("    -", "GDG DevFest Uzbekistan"),             # Dec 6
        ("  2026:", ""),
        ("    -", "Paynet Corporate Hackathon 2026"),    # spring
        ("    -", "Game Fest 2026"),                     # May 15–16
        ("    -", "GDG Build with AI  # Team Mars"),     # summer
        ("    -", "35 LVL Game Jam"),                    # Aug 21–23
        ("    -", "ICT WEEK"),                           # Sep 22–25
        ("    -", "Yandex Dev Camp 2026"),               # Oct 10–31
    ]
    LINE_H = 19.5
    PX, PY, PW = 70, 78, 580
    PH = round(28 + len(lines_data) * LINE_H)
    out = (
        svg_open(H, font=True, defs=vignette_defs(.5, .4))
        + img("bats", -24, 60, 92, opacity=.4)
        + side_rules(H, l=(0, None), r=(FRAME_TOP_H - HEADER_H, None))
        + img("frame_top", 0, -HEADER_H, W, FRAME_TOP_H)
        + heading(52, "Profile")
        + panel(PX, PY, PW, PH)
        + img("george_russell", 486, PY + 6, 160, opacity=.6, extra='mask="url(#vig)"')
        + img("sticker_63", 664, PY + PH - 56, 88, opacity=.85)
    )
    for i, (key, val) in enumerate(lines_data):
        y = PY + 28 + i * LINE_H
        if key:
            out += f'<text x="{PX+22}" y="{y}" font-family="{MONO}" font-size="12" fill="{TEXT_PRI}" font-weight="700" xml:space="preserve">{esc(key)}</text>'
        if val:
            x = PX + 22 + (max(len(key), 7) + 1) * 7.2
            val, _, note = val.partition("  # ")
            out += f'<text x="{x:.0f}" y="{y}" font-family="{MONO}" font-size="12" fill="{TEXT_SEC}">{esc(val)}'
            if note:   # yaml-style comment, dimmer
                out += f'<tspan fill="{TEXT_DIM}" font-style="italic">  # {esc(note)}</tspan>'
            out += '</text>'
    return out + '</svg>'


# ═══════════════════════════════════════════════════════════
#  SOCIAL ROW — six slices that sit side by side (12.5/18.75%)
# ═══════════════════════════════════════════════════════════
SOCIAL_H = 90
SOCIALS = [   # key, label, subtitle, brand colour
    ("gmail",    "GMAIL",    "write a letter",  "#EA4335"),
    ("telegram", "TELEGRAM", "send a raven",    "#229ED9"),
    ("discord",  "DISCORD",  "join the seance", "#5865F2"),
    ("linkedin", "LINKEDIN", "the guild hall",  "#0A66C2"),
]
SOCIAL_PERIOD = 8   # seconds for the glow to travel across all four

def social_pad(side):
    w = 100
    s = (f'<svg width="{w}" height="{SOCIAL_H}" viewBox="0 0 {w} {SOCIAL_H}" xmlns="http://www.w3.org/2000/svg">'
         f'<rect width="{w}" height="{SOCIAL_H}" fill="{BG}"/>')
    rx = RULE_L if side == "left" else RULE_R - 700
    dx = 4 if side == "left" else -4
    s += (f'<line x1="{rx}" y1="0" x2="{rx}" y2="{SOCIAL_H}" stroke="{LINE_LT}" stroke-width=".8"/>'
          f'<line x1="{rx+dx}" y1="0" x2="{rx+dx}" y2="{SOCIAL_H}" stroke="{LINE}" stroke-width=".5"/>')
    return s + '</svg>'

def social_button(label, sub, color, index):
    w = 150
    c = lighten(color)
    title = (f'<text x="{w/2}" y="44" text-anchor="middle" font-family="{SERIF}" font-size="13" '
             f'letter-spacing="3" fill="{{}}">{label}</text>')
    s = (f'<svg width="{w}" height="{SOCIAL_H}" viewBox="0 0 {w} {SOCIAL_H}" xmlns="http://www.w3.org/2000/svg">'
         f'<defs>{GLOW_FILTER}<style>{glow_css(SOCIAL_PERIOD)}{REDUCED_MOTION}</style></defs>'
         f'<rect width="{w}" height="{SOCIAL_H}" fill="{BG}"/>')
    s += panel(10, 18, w - 20, 54)
    s += (title.format(TEXT_PRI)
          + f'<text x="{w/2}" y="61" text-anchor="middle" font-family="{SERIF}" font-size="9" '
          f'fill="{TEXT_SEC}" font-style="italic" letter-spacing="1">{sub}</text>')
    # the lit state: bloom + brand-coloured edge + brand-coloured title
    s += (f'<g class="lit" style="animation-delay:{index * SOCIAL_PERIOD / len(SOCIALS):.2f}s">'
          f'<rect x="10" y="18" width="{w-20}" height="54" fill="{c}" fill-opacity=".10" stroke="{c}" stroke-width="3" filter="url(#bloom)"/>'
          f'<rect x="10" y="18" width="{w-20}" height="54" fill="none" stroke="{c}" stroke-width="1.2"/>'
          + title.format(c) + '</g>')
    return s + '</svg>'


# ═══════════════════════════════════════════════════════════
#  THE APOTHECARY — tech stack as labelled vials
# ═══════════════════════════════════════════════════════════
STACK = [  # name, brand colour
    (".NET", "#512BD4"), ("Node.js", "#5FA04E"), ("PostgreSQL", "#4169E1"), ("MongoDB", "#47A248"),
    ("Git", "#F05032"), ("Unity", "#FFFFFF"), ("Blender", "#E87D0D"), ("Krita", "#3BABFF"),
    ("Figma", "#F24E1E"), ("DaVinci Resolve", "#233A51"), ("Agile", "#0052CC"), ("Scrum", "#6DB33F"),
]
STACK_STEP = 0.8   # seconds between one vial lighting and the next

def stack_card():
    cols, cw, ch, gx, gy = 4, 146, 36, 14, 14
    rows = (len(STACK) + cols - 1) // cols
    x0 = (W - (cols * cw + (cols - 1) * gx)) // 2
    y0 = 108
    H = y0 + rows * (ch + gy) + 26
    ellie_h = H - 6
    ellie_w = round(ellie_h * png_size("ellie")[0] / png_size("ellie")[1])
    period = round(STACK_STEP * len(STACK), 2)
    out = (svg_open(H, font=True, css=SWAY + BOB + glow_css(period),
                    defs=vignette_defs(.5, .4) + GLOW_FILTER) + side_rules(H)
           + img("ellie", (W - ellie_w) / 2, 6, ellie_w, ellie_h, opacity=.28, extra='mask="url(#vig)"')
           + f'<g class="sway">{img("spiderweb", 44, 0, 76, opacity=.75)}</g>'
           + f'<g class="bob">{img("ghost", 642, 14, 50)}</g>'
           + heading(64, "The Apothecary"))
    # light them in reading order, but hop around a little so it feels alive
    order = [0, 5, 2, 7, 4, 9, 6, 11, 8, 1, 10, 3]
    for i, (name, brand) in enumerate(STACK):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        col = lighten(brand)
        label = (f'<text x="{x+cw/2+6}" y="{y+ch/2+4.5}" text-anchor="middle" font-family="{SERIF}" '
                 f'font-size="12.5" letter-spacing="1" fill="{{}}">{esc(name)}</text>')
        out += (f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="3" fill="none" stroke="{LINE}" stroke-width="1"/>'
                f'<rect x="{x+3}" y="{y+3}" width="{cw-6}" height="{ch-6}" rx="2" fill="none" stroke="{LINE}" stroke-width=".5" stroke-dasharray="1,3"/>'
                f'{diamond(x+14, y+ch/2, 2.5, LINE_LT)}'
                + label.format(TEXT_PRI)
                + f'<g class="lit" style="animation-delay:{order.index(i) * STACK_STEP:.2f}s">'
                f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="3" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-width="3" filter="url(#bloom)"/>'
                f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="3" fill="none" stroke="{col}" stroke-width="1.1"/>'
                f'{diamond(x+14, y+ch/2, 2.8, col)}'
                + label.format(col) + '</g>')
    return out + '</svg>'


# ═══════════════════════════════════════════════════════════
#  YOU WITH ME — the one that matters most, front and centre
# ═══════════════════════════════════════════════════════════
def you_with_me_card():
    H = 190
    defs = ('<radialGradient id="halo" cx=".5" cy=".5" r=".5">'
            '<stop offset="0" stop-color="#5A564D" stop-opacity=".55"/>'
            f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>')
    css = (".breathe{animation:breathe 5s ease-in-out infinite}"
           "@keyframes breathe{0%,100%{opacity:.55}50%{opacity:1}}")
    w = 320
    h = round(w * png_size("you_with_me")[1] / png_size("you_with_me")[0])
    return (
        svg_open(H, defs=defs, css=css) + side_rules(H)
        + f'<ellipse class="breathe" cx="400" cy="{H/2}" rx="260" ry="80" fill="url(#halo)"/>'
        + img("you_with_me", (W - w) / 2, (H - h) / 2, w, h)
        + '</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  THE ARCHIVES — title among the keepsakes
# ═══════════════════════════════════════════════════════════
def archives_title():
    H = 100
    return svg_open(H, font=True) + side_rules(H) + heading(68, "The Archives") + '</svg>'


# ═══════════════════════════════════════════════════════════
#  GOODREADS
# ═══════════════════════════════════════════════════════════
def goodreads_card():
    root = fetch_xml("https://www.goodreads.com/review/list_rss/202996478-ajax?shelf=currently-reading")
    if root is None:
        return None
    books = []
    ch = root.find("channel")
    for item in (ch.findall("item") if ch is not None else [])[:5]:
        raw = (item.findtext("title") or "").strip()
        pub = (item.findtext("book_published") or "").strip()
        b64 = get_b64_image((item.findtext("book_large_image_url") or "").strip())
        if " by " in raw:
            t, a = raw.rsplit(" by ", 1)
            books.append((trunc(t, 44), trunc(a, 35), pub, b64))
        else:
            books.append((trunc(raw, 44), "", pub, b64))
    if not books:
        books = [("No books currently reading", "", "", "")]

    PX, PW, ROW_H, Y0 = 80, 640, 74, 78
    H = Y0 + len(books) * ROW_H + 52
    out = (svg_open(H) + side_rules(H)
           + panel(PX, 22, PW, H - 44)
           + img("billie_letter", PX + PW - 290, 70, 150, opacity=.16)
           + img("journal_3", PX + PW - 104, H - 150, 80, opacity=.6)
           + card_title(PX + 22, 54, "CURRENTLY READING")
           + img("snoopy", PX + PW - 118, 6, 104)
           + f'<line x1="{PX+22}" y1="66" x2="{PX+PW-130}" y2="66" stroke="{LINE}" stroke-width=".6"/>')
    for i, (t, a, pub, cover) in enumerate(books):
        y = Y0 + i * ROW_H
        out += f'<rect x="{PX+21}" y="{y+5}" width="42" height="62" fill="none" stroke="{LINE_LT}" stroke-width="1"/>'
        if cover:
            out += f'<image x="{PX+22}" y="{y+6}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{cover}"/>'
        out += f'<text x="{PX+78}" y="{y+30}" font-family="{SERIF}" font-size="15" fill="{TEXT_PRI}">{t}</text>'
        sub = " ".join(x for x in (f"by {a}" if a else "", f"({pub})" if pub else "") if x)
        if sub:
            out += f'<text x="{PX+78}" y="{y+50}" font-family="{SERIF}" font-size="11.5" fill="{TEXT_SEC}" font-style="italic">{sub}</text>'
        if i < len(books) - 1:
            out += f'<line x1="{PX+22}" y1="{y+ROW_H}" x2="{PX+PW-22}" y2="{y+ROW_H}" stroke="{LINE}" stroke-width=".6" stroke-dasharray="2,5"/>'
    return out + stamp(PX + PW - 14, H - 32) + '</svg>'


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
        if "error" in data:          # e.g. rate limited — keep yesterday's card
            return None
        artists = data.get("topartists", {}).get("artist", [])
        for a in artists:
            name, scrobbles = a.get("name"), int(a.get("playcount", 0))
            a_url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptags&artist={urllib.parse.quote(name)}&api_key={API_KEY}&format=json"
            try:
                a_req = urllib.request.Request(a_url, headers={"User-Agent":"Mozilla/5.0"})
                with urllib.request.urlopen(a_req, timeout=10) as ar:
                    for t in json.loads(ar.read()).get("toptags", {}).get("tag", [])[:3]:
                        tn = t.get("name").lower()
                        tag_counts[tn] = tag_counts.get(tn, 0) + scrobbles
            except Exception:
                pass
    except Exception:
        return None
    if artists and not tag_counts:   # artists came back but every tag lookup failed
        return None

    tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    empty = not tags
    if empty:
        tags = [("just chilling... no music lately", 1)]
    max_score = tags[0][1] or 1

    PX, PW, ROW_H, Y0 = 80, 640, 46, 82
    H = Y0 + len(tags) * ROW_H + 52
    shades = ["#E8E2D6", "#C2BCB0", "#9A948A", "#7A756D", "#5E5A54"]
    ew = PW - 2
    eh = round(ew * png_size("eyes")[1] / png_size("eyes")[0])
    out = (svg_open(H, css=BLINK + BOB) + side_rules(H)
           + f'<g class="bob">{img("snake", 4, min(90, H - 112), 60, opacity=.85)}</g>'
           + f'<clipPath id="panelClip"><rect x="{PX}" y="22" width="{PW}" height="{H - 44}"/></clipPath>'
           + f'<g clip-path="url(#panelClip)">'
           + img("eyes", PX + 1, 22 + (H - 44 - eh) / 2, ew, eh, opacity=.45, extra='class="blink"')
           + '</g>'
           + panel(PX, 22, PW, H - 44)
           + card_title(PX + 22, 54, "TOP TAGS · LAST 30 DAYS")
           + f'<rect x="{PX+PW-133}" y="33" width="114" height="142" fill="none" stroke="{LINE_LT}" stroke-width="1"/>'
           + img("spotify_code", PX + PW - 132, 34, 112, 140)
           + img("blohsh", 734, 40, 22, opacity=.8)
           + f'<line x1="{PX+22}" y1="66" x2="{PX+PW-150}" y2="66" stroke="{LINE}" stroke-width=".6"/>')
    for i, (tag, score) in enumerate(tags):
        y = Y0 + i * ROW_H
        out += f'<text x="{PX+22}" y="{y+27}" font-family="{SERIF}" font-size="15" fill="{TEXT_PRI}">{esc(tag)}</text>'
        if not empty:
            bar_max = 250
            bw = max(18, int(score / max_score * bar_max))
            bx = PX + PW - 150 - bar_max
            out += (f'<rect x="{bx}" y="{y+13}" width="{bar_max}" height="16" rx="8" fill="none" stroke="{LINE}" stroke-width="1"/>'
                    f'<rect x="{bx}" y="{y+13}" width="{bw}" height="16" rx="8" fill="{shades[i % 5]}" opacity=".8"/>'
                    f'<text x="{bx+10}" y="{y+25}" font-family="{SERIF}" font-size="9" fill="{BG}" font-weight="700">~{score}</text>')
        if i < len(tags) - 1:
            out += f'<line x1="{PX+22}" y1="{y+ROW_H-2}" x2="{PX+PW-150}" y2="{y+ROW_H-2}" stroke="{LINE}" stroke-width=".6" stroke-dasharray="2,5"/>'
    return out + stamp(PX + PW - 14, H - 32) + '</svg>'


# ═══════════════════════════════════════════════════════════
#  LETTERBOXD
# ═══════════════════════════════════════════════════════════
def star_str(rating_str):
    try:
        r = float(rating_str)
    except (TypeError, ValueError):
        return ""
    full, half = int(r), 1 if r - int(r) >= .5 else 0
    return "★" * full + ("½" if half else "") + "☆" * (5 - full - half)

def letterboxd_card():
    LB = "https://letterboxd.com"
    root = fetch_xml("https://letterboxd.com/ajax_rn/rss/")
    if root is None:
        return None
    films = []
    ch = root.find("channel")
    for item in (ch.findall("item") if ch is not None else [])[:5]:
        raw = (item.findtext("title") or "").strip()
        title = re.sub(r"\s*-\s*[★½☆]+.*$", "", raw).strip()
        rating = item.findtext(f"{{{LB}}}memberRating") or item.findtext(f"{{{LB}}}rating") or ""
        m = re.search(r'<img.*?src="(.*?)"', item.findtext("description") or "")
        films.append((trunc(title, 44), star_str(rating), get_b64_image(m.group(1) if m else "")))
    if not films:
        films = [("No recent films found", "", "")]

    PX, PW, ROW_H, Y0 = 80, 640, 74, 78
    H = Y0 + len(films) * ROW_H + 52
    crawl = ("@keyframes crawl{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(14px) rotate(3deg)}}"
             ".crawl{transform-box:fill-box;transform-origin:50% 0;animation:crawl 3.2s ease-in-out infinite}")
    nh = min(H - 46, 330)
    nw = round(nh * png_size("newt_1")[0] / png_size("newt_1")[1])
    spider = (f'<g class="dangle"><line x1="745" y1="-80" x2="745" y2="96" stroke="{TEXT_SEC}" stroke-width=".7"/>'
              f'{img("spider", 727, 90, 36)}</g>')
    out = (svg_open(H, css=crawl + DANGLE, defs=vignette_defs(.62, .38)) + side_rules(H)
           + spider
           + f'<g class="crawl">{img("centipede", 24, 70, 38)}</g>'
           + img("newt_1", PX + PW - nw - 4, H - 23 - nh, nw, nh, opacity=.42, extra='mask="url(#vig)"')
           + panel(PX, 22, PW, H - 44)
           + card_title(PX + 22, 54, "RECENTLY WATCHED")
           + f'<line x1="{PX+22}" y1="66" x2="{PX+PW-110}" y2="66" stroke="{LINE}" stroke-width=".6"/>')
    for i, (film, stars, poster) in enumerate(films):
        y = Y0 + i * ROW_H
        out += f'<rect x="{PX+21}" y="{y+5}" width="42" height="62" fill="none" stroke="{LINE_LT}" stroke-width="1"/>'
        if poster:
            out += f'<image x="{PX+22}" y="{y+6}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{poster}"/>'
        out += f'<text x="{PX+78}" y="{y+41}" font-family="{SERIF}" font-size="15" fill="{TEXT_PRI}">{film}</text>'
        if stars:
            out += f'<text x="{PX+PW-24}" y="{y+41}" text-anchor="end" font-family="{SERIF}" font-size="15" fill="{GOLD}">{esc(stars)}</text>'
        if i < len(films) - 1:
            out += f'<line x1="{PX+22}" y1="{y+ROW_H}" x2="{PX+PW-22}" y2="{y+ROW_H}" stroke="{LINE}" stroke-width=".6" stroke-dasharray="2,5"/>'
    return out + stamp(PX + PW - 14, H - 32) + '</svg>'


# ═══════════════════════════════════════════════════════════
#  FOOTER — lettering, graveyard in the fog, bottom of the frame
# ═══════════════════════════════════════════════════════════
def footer_banner():
    H = FRAME_BOT_H
    defs = (
        '<radialGradient id="fog" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#3A3732" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="sinkV" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset=".55" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
        '<mask id="fadeBottom" maskContentUnits="objectBoundingBox">'
        '<rect width="1" height="1" fill="url(#sinkV)"/></mask>'
    )
    return (
        svg_open(H, defs=defs)
        + side_rules(H, l=(0, 40), r=(0, 350))
        + img("happy_halloween", 225, 18, 350)
        + f'<text x="{W//2}" y="170" text-anchor="middle" font-family="{SERIF}" font-size="10" '
          f'fill="{TEXT_SEC}" letter-spacing="5" font-style="italic">crafted with dark magic</text>'
        + f'<ellipse cx="400" cy="250" rx="300" ry="70" fill="url(#fog)"/>'
        + img("graveyard", 130, 205, 540)
        + img("signature", 612, 60, 120, opacity=.75)
        + img("frame_bottom", 0, 0, W, FRAME_BOT_H)
        + '</svg>'
    )


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("Generating gothic canvas slices...")
    out = {
        "header_banner.svg":  header_banner(),
        "info_card.svg":      info_card(),
        "social_pad_l.svg":   social_pad("left"),
        "social_pad_r.svg":   social_pad("right"),
        "you_with_me.svg":    you_with_me_card(),
        "stack_card.svg":     stack_card(),
        "archives_title.svg": archives_title(),
        "goodreads_card.svg": goodreads_card(),
        "lastfm_card.svg":    lastfm_card(),
        "letterboxd_card.svg": letterboxd_card(),
        "footer_banner.svg":  footer_banner(),
    }
    for i, (key, label, sub, color) in enumerate(SOCIALS):
        out[f"social_{key}.svg"] = social_button(label, sub, color, i)
    for name, svg in out.items():
        if svg is None:
            # feed unreachable — keep yesterday's card rather than blanking it
            print(f"  kept: {name} (fetch failed)")
            continue
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"  done: {name}")
