#!/usr/bin/env python3
"""
Christmas 2026 — GitHub Profile SVG Generator

Same idea as the Halloween canvas: the README is one continuous midnight
page cut into horizontal 800-wide slices, stacked with no gaps, so the gold
side rules, the falling snow and the pine garlands flow from slice to slice.

Everything festive (garlands, string lights, baubles, the snowy village,
snow caps) is drawn procedurally here — seeded, so every daily run paints
the exact same scene. Sticker PNGs come from scripts/process_icons.py.
"""
import re, urllib.request, urllib.parse, base64, json, math, random
from datetime import datetime, timezone, timedelta, date
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT   = Path(__file__).parent.parent
ASSETS = ROOT / "assets"
ORN    = ASSETS / "ornaments"
FONTS  = ASSETS / "fonts"

# ── PALETTE ────────────────────────────────────────────────
BG        = "#0A0F14"   # midnight — the one canvas colour, everywhere
LINE      = "#22303A"   # panel borders
LINE_LT   = "#3A4C57"
TEXT_PRI  = "#F3EDE0"   # fresh snow
TEXT_SEC  = "#A3A89F"   # frosted glass
TEXT_DIM  = "#5E6A68"
GOLD      = "#D9B45E"
GOLD_DIM  = "#8A7140"
RED       = "#C8283F"   # cranberry
RED_LT    = "#E2485C"
PINE      = ("#14352A", "#1F4A39", "#2D624B", "#3F7A5D")   # dark → light needles
SNOW      = "#EEF3F6"
WARM      = "#FFC86B"   # lit windows

LIGHT_COLORS = ("#FF4D5E", "#FFD36B", "#62E39A", "#6EC8FF", "#FFF1D0")

W = 800
RULE_L, RULE_R = 40, 760        # continuous side rules
HEADER_H  = 590
PROFILE_H = 470
FOOTER_H  = 470

TASHKENT = timezone(timedelta(hours=5))
TODAY = datetime.now(TASHKENT).date()
NOW = TODAY.strftime("%d %b %Y")

CINZEL = "'Cinzel Decorative', 'Cinzel', Georgia, serif"
FELL   = "'IM Fell English', Georgia, serif"
SCRIPT = "'Great Vibes', 'Brush Script MT', cursive"
SERIF  = "Georgia, 'Times New Roman', serif"
MONO   = "Consolas, 'Courier New', monospace"


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

def font_face(family, file, style="normal"):
    try:
        b = base64.b64encode((FONTS / file).read_bytes()).decode()
    except OSError:
        return ""
    return (f"@font-face{{font-family:'{family}';font-style:{style};"
            f"src:url(data:font/ttf;base64,{b}) format('truetype');}}")

def cinzel_face():  return font_face("Cinzel Decorative", "cinzel-dec-bold.ttf")
def script_face():  return font_face("Great Vibes", "greatvibes.ttf")
def fell_faces():
    return font_face("IM Fell English", "imfell-rm.ttf") + font_face("IM Fell English", "imfell-it.ttf", "italic")

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
    """Items fade up in their brand colour, hold, then sink back.
    (GitHub renders README SVGs as images, so no hover — they light on their own.)"""
    return (f".lit{{opacity:0;animation:lit {period}s ease-in-out infinite}}"
            "@keyframes lit{0%{opacity:0}7%,17%{opacity:1}28%,100%{opacity:0}}")

GLOW_FILTER = ('<filter id="bloom" x="-30%" y="-60%" width="160%" height="220%">'
               '<feGaussianBlur stdDeviation="4"/></filter>')
BULB_FILTER = ('<filter id="bulbGlow" x="-200%" y="-200%" width="500%" height="500%">'
               '<feGaussianBlur stdDeviation="3.2"/></filter>')

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def trunc(s, n):
    s = s.strip()
    return esc(s[:n-1] + "…") if len(s) > n else esc(s)

def png_size(name):
    with open(ORN / f"{name}.png", "rb") as f:
        head = f.read(24)
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")

def img(name, x, y, w, h=None, opacity=1, extra=""):
    uri = orn(name)
    if not uri: return ""
    if h is None:
        pw, ph = png_size(name)
        h = round(w * ph / pw, 1)
    return f'<image href="{uri}" x="{x}" y="{y}" width="{w}" height="{h}" opacity="{opacity}" {extra}/>'

def f1(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"

def svg_open(h, faces="", defs="", css=""):
    style = f"<style>{faces}{css}{REDUCED_MOTION if css else ''}</style>" if (faces or css) else ""
    return (
        f'<svg width="{W}" height="{h}" viewBox="0 0 {W} {h}" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>{style}'
        '<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{GOLD_DIM}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{GOLD}"/>'
        f'<stop offset="1" stop-color="{GOLD_DIM}" stop-opacity="0"/>'
        '</linearGradient>'
        f'{defs}</defs>'
        f'<rect width="{W}" height="{h}" fill="{BG}"/>'
    )

def side_rules(h, l=(0, None), r=(0, None)):
    """Thin gold double rules down both edges; (start, end) in slice-local y."""
    out = ""
    for x, (y0, y1) in ((RULE_L, l), (RULE_R, r)):
        if y0 is None: continue
        y1 = h if y1 is None else y1
        x2 = x + 4 if x < W / 2 else x - 4
        out += (f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y1}" stroke="{GOLD_DIM}" stroke-width=".8" opacity=".75"/>'
                f'<line x1="{x2}" y1="{y0}" x2="{x2}" y2="{y1}" stroke="{LINE_LT}" stroke-width=".5"/>')
    return out

def vignette_defs(cx=.6, cy=.42):
    return (f'<radialGradient id="vigG" cx="{cx}" cy="{cy}" r=".62">'
            '<stop offset=".45" stop-color="#fff"/><stop offset="1" stop-color="#000"/></radialGradient>'
            '<mask id="vig" maskContentUnits="objectBoundingBox">'
            '<rect width="1" height="1" fill="url(#vigG)"/></mask>')

# shared looping motions
SWAY = (".sway{transform-box:fill-box;transform-origin:50% 0;animation:sway 5s ease-in-out infinite}"
        "@keyframes sway{0%,100%{transform:rotate(-5deg)}50%{transform:rotate(5deg)}}")
BOB  = (".bob{animation:bob 4.5s ease-in-out infinite}"
        "@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}")
BLINK = (".blink{transform-box:fill-box;transform-origin:50% 50%;animation:blink 8s ease-in-out infinite}"
         "@keyframes blink{0%,45%,51%,100%{transform:scaleY(1)}48%{transform:scaleY(.06)}}")
TWINKLE = (".tw{animation:tw 2.6s ease-in-out infinite}"
           "@keyframes tw{0%,100%{opacity:.25}50%{opacity:1}}")


# ═══════════════════════════════════════════════════════════
#  SNOW — flakes fall the full height of a slice, already mid-fall on load
# ═══════════════════════════════════════════════════════════
def snow(h, count, seed, x0=0, x1=W, rmin=.7, rmax=2.3, opacity=(.35, .9)):
    rnd = random.Random(seed)
    css = (f"@keyframes fall{h}{{from{{transform:translateY(-12px)}}to{{transform:translateY({h + 12}px)}}}}"
           ".drift{animation:drift 5s ease-in-out infinite alternate}"
           "@keyframes drift{from{transform:translateX(-9px)}to{transform:translateX(9px)}}")
    out = ""
    for _ in range(count):
        x = rnd.uniform(x0, x1)
        r = rnd.uniform(rmin, rmax)
        dur = rnd.uniform(9, 19) * (1.25 - r / rmax * .4) * max(h, 200) / 400
        delay = -rnd.uniform(0, dur)
        out += (f'<g style="animation:fall{h} {dur:.1f}s linear {delay:.1f}s infinite">'
                f'<circle class="drift" cx="{x:.0f}" cy="0" r="{r:.1f}" fill="{SNOW}" '
                f'opacity="{rnd.uniform(*opacity):.2f}" style="animation-delay:{-rnd.uniform(0, 5):.1f}s"/></g>')
    return css, out


# ═══════════════════════════════════════════════════════════
#  PINE GARLAND — thousands of needles, merged into one path per shade
# ═══════════════════════════════════════════════════════════
def swag(x0, y0, x1, y1, sag, n=None):
    """Points along a hanging garland between two nails."""
    n = n or max(8, int(math.hypot(x1 - x0, y1 - y0) / 5))
    return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + sag * math.sin(math.pi * t))
            for t in (i / n for i in range(n + 1))]

def drape(x, y0, y1, amp=6, waves=2.5):
    """Points down a vertical garland, gently twisting."""
    n = max(8, int((y1 - y0) / 5))
    return [(x + amp * math.sin(waves * 2 * math.pi * i / n), y0 + (y1 - y0) * i / n) for i in range(n + 1)]

def garland(pts, seed, thick=1.0, snowy=.45, berries=True):
    rnd = random.Random(seed)
    layers = {c: [] for c in PINE}
    snow_d, berry = [], ""
    for i, (px, py) in enumerate(pts):
        for shade in PINE:
            for _ in range(3):
                a = rnd.uniform(0, 2 * math.pi)
                ln = rnd.uniform(6, 12) * thick
                sx, sy = px + rnd.uniform(-3, 3) * thick, py + rnd.uniform(-3, 3) * thick
                layers[shade].append(f"M{sx:.0f} {sy:.0f}l{ln*math.cos(a):.0f} {ln*math.sin(a):.0f}")
        if rnd.random() < snowy:           # snow settles on the top side
            a = rnd.uniform(-2.6, -.5)
            ln = rnd.uniform(4, 8) * thick
            snow_d.append(f"M{px + rnd.uniform(-4, 4):.0f} {py - 2:.0f}l{ln*math.cos(a):.0f} {ln*math.sin(a):.0f}")
        if berries and i % 9 == 4 and rnd.random() < .7:
            bx, by = px + rnd.uniform(-4, 4), py + rnd.uniform(0, 5)
            for dx, dy in ((0, 0), (3.6, 1.6), (1.2, 3.8)):
                berry += (f'<circle cx="{bx+dx:.1f}" cy="{by+dy:.1f}" r="2.4" fill="{RED}"/>'
                          f'<circle cx="{bx+dx-.8:.1f}" cy="{by+dy-.8:.1f}" r=".7" fill="#FFB3BD"/>')
    out = "".join(f'<path d="{"".join(d)}" stroke="{c}" stroke-width="{f1(2.1*thick)}" stroke-linecap="round"/>'
                  for c, d in layers.items())
    if snow_d:
        out += f'<path d="{"".join(snow_d)}" stroke="{SNOW}" stroke-width="{f1(2.4*thick)}" stroke-linecap="round" opacity=".85"/>'
    return out + berry

def string_lights(pts, seed, every=5, r=3.2, cls="bulb"):
    """A wire through the garland with bulbs that twinkle out of step."""
    rnd = random.Random(seed)
    d = "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    out = f'<path d="{d}" fill="none" stroke="#0E1A14" stroke-width="1"/>'
    glow, bulbs = "", ""
    for j, (x, y) in enumerate(pts[::every]):
        c = LIGHT_COLORS[j % len(LIGHT_COLORS)]
        delay = -rnd.uniform(0, 2.6)
        dur = rnd.uniform(1.8, 3.4)
        st = f'style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s"'
        glow  += f'<circle class="tw" cx="{x:.0f}" cy="{y+r+1:.0f}" r="{r*2.4:.1f}" fill="{c}" {st}/>'
        bulbs += (f'<rect x="{x-1.6:.1f}" y="{y-1:.1f}" width="3.2" height="2.6" fill="#44513F"/>'
                  f'<ellipse cx="{x:.0f}" cy="{y+r+1:.1f}" rx="{r*.8:.1f}" ry="{r*1.15:.1f}" fill="{c}"/>'
                  f'<ellipse class="tw" cx="{x:.0f}" cy="{y+r+1:.1f}" rx="{r*.8:.1f}" ry="{r*1.15:.1f}" fill="#fff" {st} opacity=".5"/>')
    return out + f'<g filter="url(#bulbGlow)" opacity=".85">{glow}</g>' + bulbs

BAUBLE_DEFS = (
    '<radialGradient id="bRed" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#FF8A96"/>'
    f'<stop offset=".35" stop-color="{RED}"/><stop offset="1" stop-color="#4A0812"/></radialGradient>'
    '<radialGradient id="bGold" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#FFF1C4"/>'
    f'<stop offset=".4" stop-color="{GOLD}"/><stop offset="1" stop-color="#4E3A12"/></radialGradient>'
    '<radialGradient id="bIce" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#FFFFFF"/>'
    '<stop offset=".4" stop-color="#8FC3DD"/><stop offset="1" stop-color="#1B3A4E"/></radialGradient>'
    '<radialGradient id="bPine" cx=".35" cy=".3" r=".75"><stop offset="0" stop-color="#B9F0CF"/>'
    '<stop offset=".4" stop-color="#2E8A5E"/><stop offset="1" stop-color="#0A2A1C"/></radialGradient>'
)

def bauble(cx, top, drop, r, grad="bRed", cls="sway", delay=0, pattern=True):
    """A glass ornament on a thread, swinging from (cx, top)."""
    cy = top + drop + r + 4
    deco = ""
    if pattern:   # a little painted band of snowflake dots
        deco = (f'<path d="M{cx-r*.92:.1f} {cy:.1f} Q{cx:.1f} {cy+r*.32:.1f} {cx+r*.92:.1f} {cy:.1f}" '
                f'fill="none" stroke="{SNOW}" stroke-width=".9" stroke-dasharray="1.2,3" opacity=".8"/>')
    return (f'<g class="{cls}" style="animation-delay:{delay:.1f}s">'
            f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{top+drop}" stroke="{GOLD_DIM}" stroke-width=".8"/>'
            f'<rect x="{cx-r*.28:.1f}" y="{top+drop:.1f}" width="{r*.56:.1f}" height="5" rx="1" fill="{GOLD}"/>'
            f'<circle cx="{cx}" cy="{cy:.1f}" r="{r}" fill="url(#{grad})"/>'
            f'{deco}'
            f'<ellipse cx="{cx-r*.38:.1f}" cy="{cy-r*.42:.1f}" rx="{r*.22:.1f}" ry="{r*.13:.1f}" fill="#fff" opacity=".7" '
            f'transform="rotate(-35 {cx-r*.38:.1f} {cy-r*.42:.1f})"/></g>')

def bow(cx, cy, s=1.0, color=RED):
    """Velvet ribbon bow, centred on (cx, cy)."""
    k = lambda v: f"{v*s:.1f}"
    return (f'<g transform="translate({cx} {cy})">'
            f'<path d="M0 0 C-{k(6)} {k(6)} -{k(9)} {k(16)} -{k(12)} {k(22)} L-{k(6)} {k(20)} L-{k(5)} {k(25)} C-{k(2)} {k(16)} -{k(1)} {k(6)} 0 0Z" fill="#8E1426"/>'
            f'<path d="M0 0 C{k(6)} {k(6)} {k(9)} {k(16)} {k(12)} {k(22)} L{k(6)} {k(20)} L{k(5)} {k(25)} C{k(2)} {k(16)} {k(1)} {k(6)} 0 0Z" fill="#8E1426"/>'
            f'<path d="M0 0 C-{k(6)} -{k(10)} -{k(16)} -{k(9)} -{k(15)} -{k(1)} C-{k(14)} {k(5)} -{k(6)} {k(4)} 0 0Z" fill="{color}"/>'
            f'<path d="M0 0 C{k(6)} -{k(10)} {k(16)} -{k(9)} {k(15)} -{k(1)} C{k(14)} {k(5)} {k(6)} {k(4)} 0 0Z" fill="{color}"/>'
            f'<path d="M-{k(11)} -{k(4)} C-{k(8)} -{k(6)} -{k(4)} -{k(4)} -{k(2)} -{k(1)}" stroke="#FF8A96" stroke-width="{k(1)}" fill="none" opacity=".6"/>'
            f'<ellipse cx="0" cy="0" rx="{k(3.4)}" ry="{k(3)}" fill="#A8182D"/></g>')

def holly(cx, cy, s=1.0, flip=False):
    """Two holly leaves and three berries — the heading ornament."""
    m = -1 if flip else 1
    leaf = ("M0 0 C3 -3 6 -2 8 -5 C9 -3 11 -3 13 -5 C13 -2 15 -1 17 -2 C15 1 13 3 9 4 "
            "C10 6 8 7 6 6 C5 8 3 8 1 6 C1 4 0 2 0 0Z")
    return (f'<g transform="translate({cx} {cy}) scale({m*s:.2f} {s:.2f})">'
            f'<path d="{leaf}" fill="{PINE[2]}" transform="rotate(-18)"/>'
            f'<path d="{leaf}" fill="{PINE[1]}" transform="rotate(28) scale(.9)"/>'
            f'<circle cx="-1" cy="-1" r="2.6" fill="{RED}"/><circle cx="2.4" cy="1.6" r="2.3" fill="{RED_LT}"/>'
            f'<circle cx="-1.8" cy="2.6" r="2.1" fill="{RED}"/><circle cx="-1.8" cy="-1.8" r=".7" fill="#FFC2C9"/></g>')

def snowcap(x, y, w, seed, drips=2):
    """A soft lump of snow resting on an edge from x to x+w at height y."""
    rnd = random.Random(seed)
    n = max(3, int(w / 14))
    d = f"M{x-2:.1f} {y+1:.1f}"
    for i in range(n):
        xa = x + w * (i + .5) / n
        xb = x + w * (i + 1) / n
        d += f" Q{xa:.1f} {y - rnd.uniform(3.5, 6.5):.1f} {xb:.1f} {y - rnd.uniform(.5, 2):.1f}"
    d += f" L{x+w+2:.1f} {y+1:.1f}"
    for _ in range(drips):     # icicle-ish drips hanging off the front
        dx = rnd.uniform(x + 6, x + w - 6)
        dl = rnd.uniform(2.5, 5)
        d += f" L{dx+2.4:.1f} {y+1:.1f} Q{dx:.1f} {y+1+dl*2:.1f} {dx-2.4:.1f} {y+1:.1f}"
    d += "Z"
    return f'<path d="{d}" fill="{SNOW}"/>'

def diamond(cx, cy, r=3.5, fill=GOLD_DIM):
    return f'<path d="M{cx} {cy-r} L{cx+r} {cy} L{cx} {cy+r} L{cx-r} {cy} Z" fill="{fill}"/>'

def sparkle(cx, cy, r, delay=0.0, color=GOLD):
    return (f'<path class="tw" style="animation-delay:{delay:.1f}s" d="M{cx} {cy-r} Q{cx} {cy} {cx+r} {cy} '
            f'Q{cx} {cy} {cx} {cy+r} Q{cx} {cy} {cx-r} {cy} Q{cx} {cy} {cx} {cy-r}Z" fill="{color}"/>')

CINZEL_ADV = {' ': 250, 'A': 705, 'B': 691, 'C': 826, 'D': 862, 'E': 670, 'F': 657, 'G': 861, 'H': 861,
              'I': 456, 'J': 390, 'K': 761, 'L': 427, 'M': 968, 'N': 865, 'O': 930, 'P': 705, 'Q': 925,
              'R': 731, 'S': 623, 'T': 698, 'U': 824, 'V': 719, 'W': 960, 'X': 729, 'Y': 667, 'Z': 649,
              'a': 716, 'b': 673, 'c': 780, 'd': 828, 'e': 631, 'f': 595, 'g': 836, 'h': 861, 'i': 386,
              'j': 384, 'k': 756, 'l': 616, 'm': 953, 'n': 865, 'o': 879, 'p': 655, 'q': 894, 'r': 746,
              's': 578, 't': 666, 'u': 821, 'v': 727, 'w': 971, 'x': 729, 'y': 702, 'z': 660,
              "'": 250, '&': 800, '.': 250}

def text_width(text, size, track=0):
    return sum(CINZEL_ADV.get(c, 700) for c in text) * size / 1000 + track * (len(text) - 1)

def heading(y, text, size=26):
    """Cinzel section title flanked by fading gold rules and holly sprigs."""
    half = text_width(text, size, 2) / 2 + 26
    cx, ly = W // 2, y - size * 0.34
    return (
        f'<text x="{cx}" y="{y}" text-anchor="middle" font-family="{CINZEL}" font-size="{size}" '
        f'fill="{TEXT_PRI}" letter-spacing="2">{esc(text)}</text>'
        f'<line x1="{cx-half-150:.0f}" y1="{ly:.0f}" x2="{cx-half-10:.0f}" y2="{ly:.0f}" stroke="url(#fade)"/>'
        f'<line x1="{cx+half+10:.0f}" y1="{ly:.0f}" x2="{cx+half+150:.0f}" y2="{ly:.0f}" stroke="url(#fade)"/>'
        f'{holly(cx-half+2, ly, .85, flip=True)}{holly(cx+half-2, ly, .85)}'
    )

def panel(x, y, w, h):
    """Etched panel — canvas-coloured, gold corner brackets."""
    c = 10
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="{LINE}" stroke-width="1"/>'
    for px, py, dx, dy in ((x, y, 1, 1), (x+w, y, -1, 1), (x, y+h, 1, -1), (x+w, y+h, -1, -1)):
        s += (f'<path d="M{px} {py+dy*c} L{px} {py} L{px+dx*c} {py}" fill="none" stroke="{GOLD_DIM}" stroke-width="1.2"/>'
              f'{diamond(px+dx*4, py+dy*4, 1.6, GOLD)}')
    return s

def card_title(x, y, text):
    return (f'<text x="{x}" y="{y}" font-family="{SERIF}" font-size="12" fill="{GOLD}" '
            f'letter-spacing="4">{esc(text)}</text>')

def stamp(x, y):
    return (f'<text x="{x}" y="{y}" text-anchor="end" font-family="{SERIF}" font-size="9" '
            f'fill="{TEXT_DIM}" font-style="italic">wrapped {NOW}</text>')

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

def sleeps_line():
    """'38 sleeps till Christmas' — repainted every morning by the Action."""
    xmas = date(TODAY.year, 12, 25)
    days = (xmas - TODAY).days
    if days > 1:   return f"{days} sleeps till Christmas"
    if days == 1:  return "one more sleep till Christmas"
    if days == 0:  return "it's Christmas Day!"
    if TODAY.month == 12: return f"happy holidays · see you in {TODAY.year + 1}"
    return "happy new year"


# ═══════════════════════════════════════════════════════════
#  THE NAME — letters drift down like snow, settle, sway gently
#  under a gold shimmer, and wear little caps of snow.
# ═══════════════════════════════════════════════════════════
NAME_SIZE, NAME_TRACK = 52, 3
CAPPED = {0: .62, 3: .7, 7: .66, 11: .6, 15: .66}   # letter index → cap width (fraction of advance)

NAME_CSS = """
.land{animation:land 2.2s cubic-bezier(.25,.9,.3,1) both}
.ltr{transform-box:fill-box;transform-origin:50% 0;animation:swing 6s ease-in-out infinite}
.halo{animation:halo 5s ease-in-out infinite}
.moon{animation:moon 9s ease-in-out infinite}
.flicker{animation:flicker 4s steps(1) infinite}
.smoke{animation:smoke 6s ease-out infinite}
.fly{animation:fly 22s linear infinite}
.trail{animation:trail 1.1s ease-out infinite}
@keyframes land{0%{opacity:0;transform:translateY(-60px) rotate(-8deg);filter:blur(6px)}
  60%{opacity:1;filter:none}100%{opacity:1;transform:none}}
@keyframes swing{0%,100%{transform:rotate(-1.4deg)}50%{transform:rotate(1.4deg)}}
@keyframes halo{0%,100%{opacity:.22}50%{opacity:.5}}
@keyframes moon{0%,100%{opacity:.85}50%{opacity:1}}
@keyframes flicker{0%,100%{opacity:1}37%{opacity:.82}41%{opacity:1}73%{opacity:.9}}
@keyframes smoke{0%{opacity:0;transform:translate(0,0) scale(.6)}25%{opacity:.35}
  100%{opacity:0;transform:translate(16px,-46px) scale(1.8)}}
@keyframes fly{0%{transform:translate(-260px,150px) rotate(4deg)}
  45%{transform:translate(380px,40px) rotate(-6deg)}
  70%{transform:translate(1000px,10px) rotate(-8deg)}100%{transform:translate(1000px,10px)}}
@keyframes trail{0%{opacity:.9;transform:scale(1)}100%{opacity:0;transform:translate(-24px,8px) scale(.3)}}
"""

def snowy_name(text, baseline):
    k = NAME_SIZE / 1000
    widths = [CINZEL_ADV.get(c, 700) * k for c in text]
    x = W / 2 - (sum(widths) + NAME_TRACK * (len(text) - 1)) / 2
    font = f'font-family="{CINZEL}" font-size="{NAME_SIZE}"'
    halo, letters = "", ""
    cap_y = baseline - 0.7 * NAME_SIZE
    for i, (c, w) in enumerate(zip(text, widths)):
        if c != " ":
            ch = esc(c)
            halo += f'<text x="{x:.1f}" y="{baseline}" {font}>{ch}</text>'
            cap = ""
            if i in CAPPED:
                cw = w * CAPPED[i]
                cap = snowcap(x + (w - cw) / 2 + w * .02, cap_y, cw, seed=i, drips=1)
            letters += (f'<g class="land" style="animation-delay:{0.2 + i * 0.11:.2f}s">'
                        f'<g class="ltr" style="animation-delay:-{(i * .53) % 6:.2f}s;animation-duration:{5.2 + (i % 4) * .7:.1f}s">'
                        f'<text x="{x:.1f}" y="{baseline}" {font} fill="url(#gild)">{ch}</text>{cap}</g></g>')
        x += w + NAME_TRACK
    gild = ('<linearGradient id="gild" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="260" y2="0" spreadMethod="reflect">'
            f'<stop offset="0" stop-color="{TEXT_PRI}"/><stop offset=".42" stop-color="{TEXT_PRI}"/>'
            f'<stop offset=".5" stop-color="#FFE7A8"/><stop offset=".58" stop-color="{TEXT_PRI}"/>'
            f'<stop offset="1" stop-color="{TEXT_PRI}"/>'
            '<animateTransform attributeName="gradientTransform" type="translate" from="-260 0" to="520 0" dur="7s" repeatCount="indefinite"/>'
            '</linearGradient>')
    return gild, (f'<g class="halo" fill="{GOLD}" filter="url(#glow)">{halo}</g>{letters}')


# ═══════════════════════════════════════════════════════════
#  WINTER VILLAGE — pines, a cabin with lit windows, snowy hills
# ═══════════════════════════════════════════════════════════
def pine_tree(x, base, h, fill, snowy=True, seed=0, lights=False):
    rnd = random.Random(seed)
    tiers = 4 if h > 60 else 3
    w = h * .5
    out = f'<rect x="{x-h*.035:.1f}" y="{base-h*.1:.1f}" width="{h*.07:.1f}" height="{h*.1:.1f}" fill="{fill}"/>'
    for t in range(tiers):
        tb = base - h * .08 - t * h * .22           # tier bottom
        tt = tb - h * .38                           # tier top
        tw_ = w * (1 - t * .2) / 2
        out += (f'<path d="M{x:.1f} {tt:.1f} L{x+tw_:.1f} {tb:.1f} Q{x+tw_*.5:.1f} {tb-h*.04:.1f} {x:.1f} {tb:.1f} '
                f'Q{x-tw_*.5:.1f} {tb-h*.04:.1f} {x-tw_:.1f} {tb:.1f}Z" fill="{fill}"/>')
        if snowy:
            out += (f'<path d="M{x-tw_*.82:.1f} {tb-h*.015:.1f} Q{x-tw_*.4:.1f} {tb-h*.07:.1f} {x:.1f} {tb-h*.025:.1f} '
                    f'Q{x+tw_*.4:.1f} {tb-h*.07:.1f} {x+tw_*.82:.1f} {tb-h*.015:.1f} '
                    f'Q{x+tw_*.4:.1f} {tb-h*.035:.1f} {x:.1f} {tb+h*.005:.1f} Q{x-tw_*.4:.1f} {tb-h*.035:.1f} {x-tw_*.82:.1f} {tb-h*.015:.1f}Z" '
                    f'fill="{SNOW}" opacity=".55"/>')
    if lights:
        for j in range(int(h / 3.2)):
            fy = base - h * .1 - rnd.uniform(0, h * .75)
            spread = (fy - (base - h)) / h * w * .42
            fx = x + rnd.uniform(-spread, spread)
            c = LIGHT_COLORS[j % len(LIGHT_COLORS)]
            out += f'<circle class="tw" cx="{fx:.1f}" cy="{fy:.1f}" r="1.7" fill="{c}" style="animation-delay:-{rnd.uniform(0,2.6):.1f}s"/>'
        out += sparkle(x, base - h - 2, 5, 0, GOLD)
    return out

def cabin(x, base, s=1.0):
    """Little log cabin: warm windows, smoking chimney, snowy roof."""
    k = lambda v: v * s
    body = "#121B20"
    return (
        f'<rect x="{x+k(46):.1f}" y="{base-k(70):.1f}" width="{k(9):.1f}" height="{k(24):.1f}" fill="{body}"/>'
        f'<g fill="#9AA6AE">'
        + "".join(f'<circle class="smoke" cx="{x+k(50):.1f}" cy="{base-k(74):.1f}" r="{k(4):.1f}" style="animation-delay:{d}s"/>'
                  for d in (0, 2, 4)) + '</g>'
        f'<rect x="{x:.1f}" y="{base-k(40):.1f}" width="{k(70):.1f}" height="{k(40):.1f}" fill="{body}"/>'
        f'<path d="M{x-k(8):.1f} {base-k(38):.1f} L{x+k(35):.1f} {base-k(68):.1f} L{x+k(78):.1f} {base-k(38):.1f}Z" fill="#0F171B"/>'
        f'<path d="M{x-k(9):.1f} {base-k(37):.1f} L{x+k(35):.1f} {base-k(70):.1f} L{x+k(79):.1f} {base-k(37):.1f} '
        f'L{x+k(72):.1f} {base-k(36):.1f} L{x+k(35):.1f} {base-k(62):.1f} L{x-k(2):.1f} {base-k(36):.1f}Z" fill="{SNOW}" opacity=".9"/>'
        f'<g class="flicker">'
        f'<rect x="{x+k(9):.1f}" y="{base-k(28):.1f}" width="{k(14):.1f}" height="{k(13):.1f}" fill="{WARM}"/>'
        f'<rect x="{x+k(46):.1f}" y="{base-k(28):.1f}" width="{k(14):.1f}" height="{k(13):.1f}" fill="{WARM}"/>'
        f'<rect x="{x+k(28):.1f}" y="{base-k(26):.1f}" width="{k(12):.1f}" height="{k(26):.1f}" fill="#E8A04A" opacity=".8"/>'
        f'<circle cx="{x+k(35):.1f}" cy="{base-k(20):.1f}" r="{k(46):.1f}" fill="url(#warmGlow)"/></g>'
        f'<path d="M{x+k(16):.1f} {base-k(28):.1f} V{base-k(15):.1f} M{x+k(9):.1f} {base-k(21.5):.1f} H{x+k(23):.1f} '
        f'M{x+k(53):.1f} {base-k(28):.1f} V{base-k(15):.1f} M{x+k(46):.1f} {base-k(21.5):.1f} H{x+k(60):.1f}" stroke="{body}" stroke-width="{k(1.6):.1f}"/>'
        + "".join(f'<circle cx="{x+k(4+i*7.5):.1f}" cy="{base-k(39):.1f}" r="1.5" class="tw" fill="{LIGHT_COLORS[i%5]}" '
                  f'style="animation-delay:-{i*.37:.2f}s"/>' for i in range(9))
    )

def village(base, seed, far_fill="#16222A", near_fill="#0F171C"):
    """Two rows of pines on rolling snow, a cabin and one decorated tree."""
    rnd = random.Random(seed)
    out = (f'<path d="M0 {base-30} Q140 {base-62} 300 {base-34} T560 {base-40} T800 {base-28} V{base+60} H0Z" fill="#1A2A33" opacity=".75"/>')
    for i in range(22):                                  # far row
        x = 20 + i * 36 + rnd.uniform(-10, 10)
        out += pine_tree(x, base - 30 - rnd.uniform(0, 14), rnd.uniform(34, 58), far_fill, seed=seed + i)
    out += (f'<path d="M0 {base-6} Q180 {base-34} 380 {base-10} T800 {base-12} V{base+60} H0Z" fill="#22343E"/>'
            f'<path d="M0 {base-6} Q180 {base-34} 380 {base-10} T800 {base-12}" fill="none" stroke="{SNOW}" stroke-opacity=".35" stroke-width="1.2"/>')
    return out


# ═══════════════════════════════════════════════════════════
#  HEADER — midnight sky, moon, Snoopy's sleigh, village, garland
# ═══════════════════════════════════════════════════════════
def header_banner():
    H = HEADER_H
    rnd = random.Random(7)
    defs = (
        '<radialGradient id="moonG" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#BFD3E0" stop-opacity=".55"/>'
        '<stop offset=".3" stop-color="#5D7A8C" stop-opacity=".3"/>'
        f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="moonFace" cx=".4" cy=".38" r=".7">'
        '<stop offset="0" stop-color="#FFFBEF"/><stop offset=".7" stop-color="#E9E3D2"/>'
        '<stop offset="1" stop-color="#C9C2AE"/></radialGradient>'
        '<radialGradient id="warmGlow" cx=".5" cy=".5" r=".5">'
        f'<stop offset="0" stop-color="{WARM}" stop-opacity=".35"/><stop offset="1" stop-color="{WARM}" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="sink" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset=".7" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>'
        '<mask id="sceneFade"><rect width="800" height="420" fill="url(#sink)"/></mask>'
        '<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
        + BULB_FILTER + BAUBLE_DEFS
    )
    snow_css, flakes = snow(H, 70, seed=11)
    gild, name = snowy_name("Rakhim Nuraliyev", 470)

    stars = "".join(
        f'<circle class="tw" cx="{rnd.uniform(60, 740):.0f}" cy="{rnd.uniform(95, 300):.0f}" r="{rnd.uniform(.5, 1.3):.1f}" '
        f'fill="#fff" style="animation-delay:-{rnd.uniform(0, 2.6):.1f}s;animation-duration:{rnd.uniform(2, 4.5):.1f}s"/>'
        for _ in range(55))

    sleigh = (f'<g class="fly">'
              + "".join(f'<circle class="trail" cx="{-4 - j*9}" cy="{70 + j*2}" r="{2.2 - j*.3:.1f}" fill="{GOLD}" style="animation-delay:{j*.15:.2f}s"/>'
                        for j in range(6))
              # the sticker faces left; mirror it so the reindeer lead the way
              + f'<g transform="translate(120 0) scale(-1 1)">{img("snoopy_sleigh", 0, 0, 120)}</g></g>')

    # the top garland: three swags from four nails, a vertical drape on each side
    nails = [(-10, 24), (262, 34), (538, 34), (810, 24)]
    top, lights = "", ""
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(nails, nails[1:])):
        pts = swag(x0, y0, x1, y1, 58)
        top += garland(pts, seed=100 + i, thick=1.15)
        lights += string_lights(swag(x0, y0 + 6, x1, y1 + 6, 66), seed=200 + i, every=5)
    left = drape(30, 20, 330, amp=7)
    right = drape(770, 20, 330, amp=7, waves=2.2)
    top = garland(left, 300, thick=1.05) + garland(right, 301, thick=1.05) + top
    lights = string_lights(drape(34, 26, 320, amp=10), 310, every=6) + \
             string_lights(drape(766, 26, 320, amp=10, waves=2.2), 311, every=6) + lights
    ornaments = (bauble(262, 40, 28, 13, "bGold", delay=-1.2) + bauble(538, 40, 34, 12, "bRed", delay=-2.6)
                 + bauble(140, 82, 10, 9, "bIce", delay=-.4) + bauble(400, 92, 14, 10, "bPine", delay=-3.1)
                 + bauble(660, 82, 8, 9, "bIce", delay=-1.9)
                 + bauble(30, 330, 18, 11, "bRed", delay=-.8) + bauble(770, 330, 24, 11, "bGold", delay=-2.2))
    bows = bow(262, 34, 1.15) + bow(538, 34, 1.15) + bow(30, 22, 1.0) + bow(770, 22, 1.0)

    scene = (village(392, seed=21)
             + pine_tree(196, 380, 120, "#173528", seed=41, lights=True)
             + cabin(520, 386, 1.05)
             + pine_tree(640, 388, 74, "#0E171C", seed=42)
             + pine_tree(120, 386, 66, "#0E171C", seed=43)
             + pine_tree(318, 388, 52, "#0E171C", seed=44))

    return (
        svg_open(H, faces=cinzel_face() + fell_faces() + script_face(), defs=defs + gild,
                 css=NAME_CSS + TWINKLE + SWAY + snow_css)
        + stars
        + f'<circle class="moon" cx="430" cy="190" r="210" fill="url(#moonG)"/>'
        + f'<circle cx="430" cy="190" r="54" fill="url(#moonFace)" opacity=".95"/>'
        + '<g fill="#BDB6A2" opacity=".35"><circle cx="414" cy="176" r="9"/><circle cx="447" cy="203" r="6"/><circle cx="440" cy="168" r="4"/></g>'
        + sleigh
        + f'<g mask="url(#sceneFade)">{scene}</g>'
        + side_rules(H, l=(340, None), r=(340, None))
        + top + lights + bows + ornaments
        + name
        + f'<line x1="250" y1="494" x2="550" y2="494" stroke="url(#fade)"/>{diamond(400, 494, 3.5, GOLD)}'
        + f'<text x="{W//2}" y="522" text-anchor="middle" font-family="{FELL}" font-size="16" '
          f'fill="{TEXT_SEC}" font-style="italic" letter-spacing=".6">Game Developer @ UIC Games · Full-Stack @ BOGATIR Textile</text>'
        + f'<text x="{W//2}" y="550" text-anchor="middle" font-family="{FELL}" font-size="11.5" '
          f'fill="#7F877F" letter-spacing="5">SOFTWARE ENGINEER · GAME DEV</text>'
        + f'<text x="{W//2}" y="578" text-anchor="middle" font-family="{SCRIPT}" font-size="21" fill="{GOLD}">{esc(sleeps_line())}</text>'
        + sparkle(W // 2 - 128, 571, 4, -.6) + sparkle(W // 2 + 128, 571, 4, -1.7)
        + flakes
        + '</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  PROFILE
# ═══════════════════════════════════════════════════════════
def info_card():
    H = PROFILE_H
    lines_data = [
        ("name:", "Rakhim Nuraliyev"),
        ("education:", "PDP University — B.S. Software Development"),
        ("age:", "19"),
        ("experience:", ""),
        ("  -", "{ role: Game Developer, org: UIC Games }"),
        ("  -", "{ role: Full-Stack Dev, org: BOGATIR Textile }"),
        ("events:", ""),
        # oldest first, in the order they happened
        ("  2025:", ""),
        ("    -", "HackMars 1.0"),
        ("    -", "GDG DevFest Uzbekistan"),
        ("  2026:", ""),
        ("    -", "Paynet Corporate Hackathon 2026"),
        ("    -", "Game Fest 2026"),
        ("    -", "GDG Build with AI  # Team Mars"),
        ("    -", "35 LVL Game Jam"),
        ("    -", "ICT WEEK"),
        ("    -", "Yandex Dev Camp 2026"),
    ]
    LINE_H = 19.5
    PX, PY, PW = 70, 82, 580
    PH = round(28 + len(lines_data) * LINE_H)
    snow_css, flakes = snow(H, 26, seed=12, rmax=1.8, opacity=(.2, .6))
    out = (
        svg_open(H, faces=cinzel_face(), defs=vignette_defs(.5, .4) + BAUBLE_DEFS,
                 css=SWAY + BOB + TWINKLE + snow_css)
        + side_rules(H)
        + heading(52, "Profile")
        + panel(PX, PY, PW, PH)
        + snowcap(PX + 30, PY, 160, seed=5, drips=3) + snowcap(PX + PW - 200, PY, 120, seed=6, drips=2)
        + img("george_russell", 486, PY + 6, 160, opacity=.6, extra='mask="url(#vig)"')
        + img("sticker_63", 664, PY + PH - 56, 88, opacity=.85)
        + f'<g class="bob">{img("snoopy_gingerbread", -6, 120, 74)}</g>'
        + bauble(724, 0, 70, 12, "bGold", delay=-1.4) + bauble(744, 0, 40, 9, "bRed", delay=-3)
    )
    for i, (key, val) in enumerate(lines_data):
        y = PY + 28 + i * LINE_H
        if key:
            out += f'<text x="{PX+22}" y="{y}" font-family="{MONO}" font-size="12" fill="{TEXT_PRI}" font-weight="700" xml:space="preserve">{esc(key)}</text>'
        if val:
            x = PX + 22 + (max(len(key), 7) + 1) * 7.2
            val, _, note = val.partition("  # ")
            out += f'<text x="{x:.0f}" y="{y}" font-family="{MONO}" font-size="12" fill="{TEXT_SEC}">{esc(val)}'
            if note:
                out += f'<tspan fill="{TEXT_DIM}" font-style="italic">  # {esc(note)}</tspan>'
            out += '</text>'
    return out + flakes + '</svg>'


# ═══════════════════════════════════════════════════════════
#  SOCIAL ROW — six slices side by side (12.5 / 18.75 %)
# ═══════════════════════════════════════════════════════════
SOCIAL_H = 96
SOCIALS = [   # key, label, subtitle, brand colour
    ("gmail",    "GMAIL",    "write to the north pole", "#EA4335"),
    ("telegram", "TELEGRAM", "send a reindeer",         "#229ED9"),
    ("discord",  "DISCORD",  "join the carols",         "#5865F2"),
    ("linkedin", "LINKEDIN", "the elves' guild",        "#0A66C2"),
]
SOCIAL_PERIOD = 8

def social_pad(side):
    w = 100
    s = (f'<svg width="{w}" height="{SOCIAL_H}" viewBox="0 0 {w} {SOCIAL_H}" xmlns="http://www.w3.org/2000/svg">'
         f'<rect width="{w}" height="{SOCIAL_H}" fill="{BG}"/>')
    rx = RULE_L if side == "left" else RULE_R - 700
    dx = 4 if side == "left" else -4
    s += (f'<line x1="{rx}" y1="0" x2="{rx}" y2="{SOCIAL_H}" stroke="{GOLD_DIM}" stroke-width=".8" opacity=".75"/>'
          f'<line x1="{rx+dx}" y1="0" x2="{rx+dx}" y2="{SOCIAL_H}" stroke="{LINE_LT}" stroke-width=".5"/>')
    return s + '</svg>'

def social_button(label, sub, color, index):
    w = 150
    c = lighten(color)
    title = (f'<text x="{w/2}" y="50" text-anchor="middle" font-family="{SERIF}" font-size="13" '
             f'letter-spacing="3" fill="{{}}">{label}</text>')
    s = (f'<svg width="{w}" height="{SOCIAL_H}" viewBox="0 0 {w} {SOCIAL_H}" xmlns="http://www.w3.org/2000/svg">'
         f'<defs>{GLOW_FILTER}<style>{glow_css(SOCIAL_PERIOD)}{REDUCED_MOTION}</style></defs>'
         f'<rect width="{w}" height="{SOCIAL_H}" fill="{BG}"/>')
    s += panel(10, 24, w - 20, 54)
    s += (title.format(TEXT_PRI)
          + f'<text x="{w/2}" y="67" text-anchor="middle" font-family="{SERIF}" font-size="9" '
          f'fill="{TEXT_SEC}" font-style="italic" letter-spacing=".8">{esc(sub)}</text>')
    s += (f'<g class="lit" style="animation-delay:{index * SOCIAL_PERIOD / len(SOCIALS):.2f}s">'
          f'<rect x="10" y="24" width="{w-20}" height="54" fill="{c}" fill-opacity=".10" stroke="{c}" stroke-width="3" filter="url(#bloom)"/>'
          f'<rect x="10" y="24" width="{w-20}" height="54" fill="none" stroke="{c}" stroke-width="1.2"/>'
          + title.format(c) + '</g>')
    s += snowcap(18, 24, w - 36, seed=40 + index, drips=2)
    return s + '</svg>'


# ═══════════════════════════════════════════════════════════
#  SANTA'S WORKSHOP — tech stack as gift tags
# ═══════════════════════════════════════════════════════════
STACK = [
    (".NET", "#512BD4"), ("Node.js", "#5FA04E"), ("PostgreSQL", "#4169E1"), ("MongoDB", "#47A248"),
    ("Git", "#F05032"), ("Unity", "#FFFFFF"), ("Blender", "#E87D0D"), ("Krita", "#3BABFF"),
    ("Figma", "#F24E1E"), ("DaVinci Resolve", "#233A51"), ("Agile", "#0052CC"), ("Scrum", "#6DB33F"),
]
STACK_STEP = 0.8

def stack_card():
    cols, cw, ch, gx, gy = 4, 146, 36, 14, 18
    rows = (len(STACK) + cols - 1) // cols
    x0 = (W - (cols * cw + (cols - 1) * gx)) // 2
    y0 = 112
    H = y0 + rows * (ch + gy) + 26
    ellie_h = H - 6
    ellie_w = round(ellie_h * png_size("ellie")[0] / png_size("ellie")[1])
    period = round(STACK_STEP * len(STACK), 2)
    snow_css, flakes = snow(H, 22, seed=13, rmax=1.8, opacity=(.2, .55))
    out = (svg_open(H, faces=cinzel_face(), css=SWAY + BOB + TWINKLE + glow_css(period) + snow_css,
                    defs=vignette_defs(.5, .4) + GLOW_FILTER + BAUBLE_DEFS) + side_rules(H)
           + img("ellie", (W - ellie_w) / 2, 6, ellie_w, ellie_h, opacity=.26, extra='mask="url(#vig)"')
           + bauble(78, 0, 46, 14, "bRed", delay=-.6) + bauble(104, 0, 22, 10, "bGold", delay=-2.1)
           + f'<g class="bob">{img("snoopy_puffer", 640, 6, 76)}</g>'
           + heading(68, "Santa's Workshop"))
    order = [0, 5, 2, 7, 4, 9, 6, 11, 8, 1, 10, 3]
    for i, (name, brand) in enumerate(STACK):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cw + gx), y0 + r * (ch + gy)
        col = lighten(brand)
        label = (f'<text x="{x+cw/2+6}" y="{y+ch/2+4.5}" text-anchor="middle" font-family="{SERIF}" '
                 f'font-size="12.5" letter-spacing="1" fill="{{}}">{esc(name)}</text>')
        # a gift tag: punched hole + twine on the left
        out += (f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="3" fill="none" stroke="{LINE}" stroke-width="1"/>'
                f'<rect x="{x+3}" y="{y+3}" width="{cw-6}" height="{ch-6}" rx="2" fill="none" stroke="{LINE}" stroke-width=".5" stroke-dasharray="1,3"/>'
                f'<circle cx="{x+14}" cy="{y+ch/2}" r="3" fill="none" stroke="{GOLD_DIM}" stroke-width="1"/>'
                + label.format(TEXT_PRI)
                + f'<g class="lit" style="animation-delay:{order.index(i) * STACK_STEP:.2f}s">'
                f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="3" fill="{col}" fill-opacity=".12" stroke="{col}" stroke-width="3" filter="url(#bloom)"/>'
                f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="3" fill="none" stroke="{col}" stroke-width="1.1"/>'
                f'<circle cx="{x+14}" cy="{y+ch/2}" r="3" fill="{col}"/>'
                + label.format(col) + '</g>'
                + snowcap(x + 22, y, cw - 44, seed=60 + i, drips=1))
    return out + flakes + '</svg>'


# ═══════════════════════════════════════════════════════════
#  YOU WITH ME — front and centre, in a little halo of lights
# ═══════════════════════════════════════════════════════════
def you_with_me_card():
    H = 190
    defs = ('<radialGradient id="halo" cx=".5" cy=".5" r=".5">'
            f'<stop offset="0" stop-color="{GOLD}" stop-opacity=".22"/>'
            f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>' + BULB_FILTER)
    css = (".breathe{animation:breathe 5s ease-in-out infinite}"
           "@keyframes breathe{0%,100%{opacity:.55}50%{opacity:1}}")
    snow_css, flakes = snow(H, 18, seed=14, rmax=1.6, opacity=(.2, .5))
    w = 320
    h = round(w * png_size("you_with_me")[1] / png_size("you_with_me")[0])
    ring = [(400 + 250 * math.cos(a), H / 2 + 62 * math.sin(a))
            for a in (i / 60 * 2 * math.pi for i in range(61))]
    return (
        svg_open(H, defs=defs, css=css + TWINKLE + snow_css) + side_rules(H)
        + f'<ellipse class="breathe" cx="400" cy="{H/2}" rx="260" ry="80" fill="url(#halo)"/>'
        + string_lights(ring[30:61], seed=500, every=3, r=2.4)
        + img("you_with_me", (W - w) / 2, (H - h) / 2, w, h)
        + sparkle(220, 60, 5, -.3) + sparkle(590, 130, 4, -1.4) + sparkle(560, 48, 3, -2)
        + flakes + '</svg>'
    )


# ═══════════════════════════════════════════════════════════
#  UNDER THE TREE — archives title
# ═══════════════════════════════════════════════════════════
def archives_title():
    H = 110
    snow_css, flakes = snow(H, 10, seed=15, rmax=1.6, opacity=(.2, .5))
    return (svg_open(H, faces=cinzel_face(), css=BOB + TWINKLE + snow_css) + side_rules(H)
            + f'<g class="bob" style="animation-delay:-1s">{img("plaid_star", 112, 30, 44)}</g>'
            + f'<g class="bob" style="animation-delay:-2.5s">{img("cocoa_mug", 650, 26, 40)}</g>'
            + heading(76, "Under the Tree") + flakes + '</svg>')


# ═══════════════════════════════════════════════════════════
#  GOODREADS — fireside reading
# ═══════════════════════════════════════════════════════════
GOODREADS_CACHE = ASSETS / "cache" / "goodreads.json"

GOODREADS_USER = "202996478-ajax"

def fetch_text(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return ""

def _unhtml(t):
    import html
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()

def goodreads_from_profile():
    """The public profile's "Currently Reading" box: title, author, cover, page progress.
    (The shelf RSS started 404ing in late Oct 2026; the profile page still renders.)"""
    page = fetch_text(f"https://www.goodreads.com/user/show/{GOODREADS_USER}")
    start = page.find('id="currentlyReadingReviews"')
    if start < 0:
        return None
    end = page.find('class="bigBoxBottom"', start)
    books = []
    for chunk in page[start:end].split('<div class="Updates')[1:6]:
        title = re.search(r'class="bookTitle"[^>]*>(.*?)</a>', chunk, re.S)
        if not title:
            continue
        author = re.search(r'class="authorName"[^>]*>(.*?)</a>', chunk, re.S)
        cover = re.search(r'<img alt="[^"]*" src="([^"]+)"', chunk)
        prog = re.search(r"page (\d+) of (\d+)", chunk)
        cover_url = re.sub(r"\._S[XY]\d+_", "", cover.group(1)) if cover else ""
        books.append({"title": _unhtml(title.group(1)), "author": _unhtml(author.group(1)) if author else "",
                      "pub": "", "cover": get_b64_image(cover_url),
                      "page": int(prog.group(1)) if prog else 0, "pages": int(prog.group(2)) if prog else 0})
    return books

def goodreads_from_rss():
    root = fetch_xml(f"https://www.goodreads.com/review/list_rss/{GOODREADS_USER}?shelf=currently-reading")
    ch = root.find("channel") if root is not None else None
    if ch is None:
        return None
    books = []
    for item in ch.findall("item")[:5]:
        raw = (item.findtext("title") or "").strip()
        t, _, a = raw.rpartition(" by ") if " by " in raw else (raw, "", "")
        books.append({"title": t, "author": a or (item.findtext("author_name") or "").strip(),
                      "pub": (item.findtext("book_published") or "").strip(),
                      "cover": get_b64_image((item.findtext("book_large_image_url") or "").strip())})
    return books

def goodreads_books():
    """Profile page first, then the RSS feed, then the last good fetch."""
    books = goodreads_from_profile()
    if books is None:
        books = goodreads_from_rss()
    if books is not None:
        GOODREADS_CACHE.parent.mkdir(exist_ok=True)
        GOODREADS_CACHE.write_text(json.dumps(books, ensure_ascii=False), encoding="utf-8")
        return books
    try:
        return json.loads(GOODREADS_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

def goodreads_card():
    data = goodreads_books()
    if data is None:
        return None
    books = [(trunc(b["title"], 44), trunc(b["author"], 35), b.get("pub", ""), b["cover"],
              b.get("page", 0), b.get("pages", 0)) for b in data]
    if not books:
        books = [("No books currently reading", "", "", "", 0, 0)]

    PX, PW, ROW_H, Y0 = 80, 640, 74, 78
    H = Y0 + len(books) * ROW_H + 52
    snow_css, flakes = snow(H, 16, seed=16, rmax=1.6, opacity=(.15, .45))
    out = (svg_open(H, css=TWINKLE + snow_css, defs=cane_defs()) + side_rules(H)
           + panel(PX, 22, PW, H - 44)
           + snowcap(PX + 40, 22, 150, seed=71, drips=2)
           + img("billie_letter", PX + PW - 290, 70, 150, opacity=.16)
           + img("journal_3", PX + PW - 104, H - 150, 80, opacity=.5)
           + card_title(PX + 22, 54, "FIRESIDE READING")
           + img("snoopy", PX + PW - 118, 6, 104)
           + f'<line x1="{PX+22}" y1="66" x2="{PX+PW-130}" y2="66" stroke="{LINE}" stroke-width=".6"/>')
    for i, (t, a, pub, cover, page, pages) in enumerate(books):
        y = Y0 + i * ROW_H
        out += f'<rect x="{PX+21}" y="{y+5}" width="42" height="62" fill="none" stroke="{GOLD_DIM}" stroke-width="1"/>'
        if cover:
            out += f'<image x="{PX+22}" y="{y+6}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{cover}"/>'
        out += f'<text x="{PX+78}" y="{y+30}" font-family="{SERIF}" font-size="15" fill="{TEXT_PRI}">{t}</text>'
        sub = " ".join(x for x in (f"by {a}" if a else "", f"({pub})" if pub else "") if x)
        if sub:
            out += f'<text x="{PX+78}" y="{y+50}" font-family="{SERIF}" font-size="11.5" fill="{TEXT_SEC}" font-style="italic">{sub}</text>'
        if pages:   # reading progress as a little candy-cane ribbon
            bx, bw = PX + 300, 120
            fw = max(6, round(bw * page / pages))
            out += (f'<rect x="{bx}" y="{y+42}" width="{bw}" height="8" rx="4" fill="none" stroke="{LINE_LT}" stroke-width=".8"/>'
                    f'<rect x="{bx}" y="{y+42}" width="{fw}" height="8" rx="4" fill="url(#cane{i % 5})"/>'
                    f'<text x="{bx+bw+8}" y="{y+49}" font-family="{SERIF}" font-size="9.5" fill="{TEXT_DIM}" '
                    f'font-style="italic">page {page} of {pages}</text>')
        if i < len(books) - 1:
            out += f'<line x1="{PX+22}" y1="{y+ROW_H}" x2="{PX+PW-22}" y2="{y+ROW_H}" stroke="{LINE}" stroke-width=".6" stroke-dasharray="2,5"/>'
    return out + stamp(PX + PW - 14, H - 32) + flakes + '</svg>'


# ═══════════════════════════════════════════════════════════
#  LAST.FM — carols on repeat, candy-cane bars
# ═══════════════════════════════════════════════════════════
CANE_COLORS = [(RED, SNOW), ("#2E8A5E", SNOW), (GOLD, "#FFF6DC"), ("#4E8FB5", SNOW), ("#8A6BB5", SNOW)]

def cane_defs():
    out = ""
    for i, (a, b) in enumerate(CANE_COLORS):
        out += (f'<pattern id="cane{i}" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                f'<rect width="12" height="12" fill="{b}"/><rect width="6" height="12" fill="{a}"/>'
                f'<animateTransform attributeName="patternTransform" type="translate" additive="sum" from="0 0" to="12 0" dur="{1.4 + i*.3:.1f}s" repeatCount="indefinite"/>'
                '</pattern>')
    return out

def lastfm_card():
    API_KEY = "b25b959554ed76058ac220b7b2e0a026"
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user=ajaxmanson&api_key={API_KEY}&period=1month&format=json&limit=15"
    tag_counts = {}
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        if "error" in data:
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
    if artists and not tag_counts:
        return None

    tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    empty = not tags
    if empty:
        tags = [("just chilling... no carols lately", 1)]
    max_score = tags[0][1] or 1

    PX, PW, ROW_H, Y0 = 80, 640, 46, 82
    H = Y0 + len(tags) * ROW_H + 52
    ew = PW - 2
    eh = round(ew * png_size("eyes")[1] / png_size("eyes")[0])
    snow_css, flakes = snow(H, 14, seed=17, rmax=1.6, opacity=(.15, .45))
    out = (svg_open(H, css=BLINK + BOB + TWINKLE + snow_css, defs=cane_defs()) + side_rules(H)
           + f'<g class="bob">{img("snowman", 0, min(70, H - 150), 52)}</g>'
           + f'<clipPath id="panelClip"><rect x="{PX}" y="22" width="{PW}" height="{H - 44}"/></clipPath>'
           + f'<g clip-path="url(#panelClip)">'
           + img("eyes", PX + 1, 22 + (H - 44 - eh) / 2, ew, eh, opacity=.4, extra='class="blink"')
           + '</g>'
           + panel(PX, 22, PW, H - 44)
           + snowcap(PX + 30, 22, 120, seed=72, drips=2)
           + card_title(PX + 22, 54, "CAROLS ON REPEAT · LAST 30 DAYS")
           + f'<rect x="{PX+PW-133}" y="33" width="114" height="142" fill="none" stroke="{GOLD_DIM}" stroke-width="1"/>'
           + img("spotify_code", PX + PW - 132, 34, 112, 140)
           + snowcap(PX + PW - 128, 33, 104, seed=73, drips=2)
           + img("blohsh", 734, 40, 22, opacity=.8)
           + f'<line x1="{PX+22}" y1="66" x2="{PX+PW-150}" y2="66" stroke="{LINE}" stroke-width=".6"/>')
    for i, (tag, score) in enumerate(tags):
        y = Y0 + i * ROW_H
        out += f'<text x="{PX+22}" y="{y+27}" font-family="{SERIF}" font-size="15" fill="{TEXT_PRI}">{esc(tag)}</text>'
        if not empty:
            bar_max = 220
            bw = max(18, int(score / max_score * bar_max))
            bx = PX + PW - 186 - bar_max
            out += (f'<rect x="{bx}" y="{y+13}" width="{bar_max}" height="16" rx="8" fill="none" stroke="{LINE}" stroke-width="1"/>'
                    f'<rect x="{bx}" y="{y+13}" width="{bw}" height="16" rx="8" fill="url(#cane{i % 5})" opacity=".9"/>'
                    f'<rect x="{bx}" y="{y+14}" width="{bw}" height="5" rx="2.5" fill="#fff" opacity=".22"/>'
                    f'<text x="{bx+bar_max+8}" y="{y+25}" font-family="{SERIF}" font-size="10" fill="{TEXT_SEC}" font-style="italic">~{score}</text>')
        if i < len(tags) - 1:
            out += f'<line x1="{PX+22}" y1="{y+ROW_H-2}" x2="{PX+PW-150}" y2="{y+ROW_H-2}" stroke="{LINE}" stroke-width=".6" stroke-dasharray="2,5"/>'
    return out + stamp(PX + PW - 14, H - 32) + flakes + '</svg>'


# ═══════════════════════════════════════════════════════════
#  LETTERBOXD — the holiday matinee
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
    nh = min(H - 46, 330)
    nw = round(nh * png_size("newt_1")[0] / png_size("newt_1")[1])
    dangle = (".dangle{animation:dangle 7s ease-in-out infinite}"
              "@keyframes dangle{0%,100%{transform:translateY(0)}40%{transform:translateY(30px)}55%{transform:translateY(26px)}}")
    snow_css, flakes = snow(H, 18, seed=18, rmax=1.6, opacity=(.15, .45))
    out = (svg_open(H, css=dangle + SWAY + BOB + TWINKLE + snow_css, defs=vignette_defs(.62, .38) + BAUBLE_DEFS)
           + side_rules(H)
           + f'<g class="dangle">{bauble(745, -40, 120, 13, "bIce", delay=-1)}</g>'
           + f'<g class="bob" style="animation-delay:-2s">{img("snoopy_scarf", 2, 80, 70)}</g>'
           + img("newt_1", PX + PW - nw - 4, H - 23 - nh, nw, nh, opacity=.4, extra='mask="url(#vig)"')
           + panel(PX, 22, PW, H - 44)
           + snowcap(PX + PW - 250, 22, 170, seed=74, drips=3)
           + card_title(PX + 22, 54, "THE HOLIDAY MATINEE")
           + f'<line x1="{PX+22}" y1="66" x2="{PX+PW-110}" y2="66" stroke="{LINE}" stroke-width=".6"/>')
    for i, (film, stars, poster) in enumerate(films):
        y = Y0 + i * ROW_H
        out += f'<rect x="{PX+21}" y="{y+5}" width="42" height="62" fill="none" stroke="{GOLD_DIM}" stroke-width="1"/>'
        if poster:
            out += f'<image x="{PX+22}" y="{y+6}" width="40" height="60" preserveAspectRatio="xMidYMid slice" href="{poster}"/>'
        out += f'<text x="{PX+78}" y="{y+41}" font-family="{SERIF}" font-size="15" fill="{TEXT_PRI}">{film}</text>'
        if stars:
            out += f'<text x="{PX+PW-24}" y="{y+41}" text-anchor="end" font-family="{SERIF}" font-size="15" fill="{GOLD}">{esc(stars)}</text>'
        if i < len(films) - 1:
            out += f'<line x1="{PX+22}" y1="{y+ROW_H}" x2="{PX+PW-22}" y2="{y+ROW_H}" stroke="{LINE}" stroke-width=".6" stroke-dasharray="2,5"/>'
    return out + stamp(PX + PW - 14, H - 32) + flakes + '</svg>'


# ═══════════════════════════════════════════════════════════
#  FOOTER — Merry Christmas over a sleeping snowy town
# ═══════════════════════════════════════════════════════════
def footer_banner():
    H = FOOTER_H
    defs = (
        '<radialGradient id="warmGlow" cx=".5" cy=".5" r=".5">'
        f'<stop offset="0" stop-color="{WARM}" stop-opacity=".35"/><stop offset="1" stop-color="{WARM}" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="mist" cx=".5" cy=".5" r=".5">'
        '<stop offset="0" stop-color="#2A3E4A" stop-opacity=".9"/>'
        f'<stop offset="1" stop-color="{BG}" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="gildF" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="300" y2="0" spreadMethod="reflect">'
        f'<stop offset="0" stop-color="{GOLD}"/><stop offset=".45" stop-color="{GOLD}"/>'
        '<stop offset=".5" stop-color="#FFF3CF"/><stop offset=".55" stop-color="' + GOLD + '"/>'
        f'<stop offset="1" stop-color="{GOLD}"/>'
        '<animateTransform attributeName="gradientTransform" type="translate" from="-300 0" to="600 0" dur="6s" repeatCount="indefinite"/>'
        '</linearGradient>'
        '<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="7"/></filter>'
        + BULB_FILTER + BAUBLE_DEFS
    )
    snow_css, flakes = snow(H, 50, seed=19)
    css = (NAME_CSS + TWINKLE + SWAY + snow_css
           + ".pulse{animation:halo 5s ease-in-out infinite}")
    # bottom garland: swags rising to the corners, and drapes climbing the sides
    nails = [(-10, H - 92), (262, H - 80), (538, H - 80), (810, H - 92)]
    gar, lights = "", ""
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(nails, nails[1:])):
        gar += garland(swag(x0, y0, x1, y1, 50), seed=400 + i, thick=1.1)
        lights += string_lights(swag(x0, y0 + 6, x1, y1 + 6, 56), seed=410 + i, every=5)
    gar = (garland(drape(30, H - 250, H - 84, amp=7), 420, thick=1.05)
           + garland(drape(770, H - 250, H - 84, amp=7, waves=2.2), 421, thick=1.05) + gar)
    lights = (string_lights(drape(34, H - 245, H - 90, amp=10), 430, every=6)
              + string_lights(drape(766, H - 245, H - 90, amp=10, waves=2.2), 431, every=6) + lights)
    town = (village(H - 70, seed=31)
            + cabin(150, H - 82, .9) + cabin(560, H - 80, .8)
            + pine_tree(400, H - 74, 110, "#173528", seed=51, lights=True)
            + pine_tree(300, H - 76, 60, "#0E171C", seed=52) + pine_tree(490, H - 78, 54, "#0E171C", seed=53)
            + pine_tree(680, H - 76, 64, "#0E171C", seed=54) + pine_tree(80, H - 78, 50, "#0E171C", seed=55))
    return (
        svg_open(H, faces=script_face() + fell_faces(), defs=defs, css=css)
        + side_rules(H, l=(0, H - 252), r=(0, H - 252))
        + f'<g class="pulse" filter="url(#glow)"><text x="{W//2}" y="104" text-anchor="middle" font-family="{SCRIPT}" '
          f'font-size="66" fill="{GOLD}">Merry Christmas</text></g>'
        + f'<text x="{W//2}" y="104" text-anchor="middle" font-family="{SCRIPT}" font-size="66" fill="url(#gildF)">Merry Christmas</text>'
        + f'<text x="{W//2}" y="138" text-anchor="middle" font-family="{FELL}" font-size="12.5" fill="{TEXT_PRI}" '
          f'letter-spacing="6">&amp; A HAPPY NEW YEAR · {TODAY.year + (1 if TODAY.month >= 9 else 0)}</text>'
        + f'<text x="{W//2}" y="166" text-anchor="middle" font-family="{SERIF}" font-size="10" '
          f'fill="{TEXT_SEC}" letter-spacing="5" font-style="italic">crafted with winter magic</text>'
        + sparkle(222, 70, 6, -.2) + sparkle(588, 54, 5, -1.1) + sparkle(560, 112, 3.5, -2)
        + holly(400 - 228, 133, .8, flip=True) + holly(400 + 228, 133, .8)
        + img("signature", 612, 150, 110, opacity=.8)
        + f'<ellipse cx="400" cy="{H-120}" rx="330" ry="70" fill="url(#mist)"/>'
        + town
        + gar + lights
        + bow(262, H - 80, 1.15) + bow(538, H - 80, 1.15)
        + bauble(262, H - 74, 14, 11, "bGold", delay=-1.3) + bauble(538, H - 74, 10, 11, "bRed", delay=-2.4)
        + bauble(30, H - 262, 16, 10, "bGold", delay=-.5) + bauble(770, H - 262, 20, 10, "bRed", delay=-1.8)
        + flakes
        + '</svg>'
    )


# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    print("Generating Christmas canvas slices...")
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
            print(f"  kept: {name} (fetch failed)")
            continue
        (ASSETS / name).write_text(svg, encoding="utf-8")
        print(f"  done: {name}  ({len(svg)//1024} KB)")
