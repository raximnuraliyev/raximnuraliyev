"""
Generate Christmas-themed icon PNGs (100x100, transparent background)
for use as subtle watermark decorations in SVG profile cards.

Icons:
  icon_0.png — Snowflake
  icon_1.png — Christmas star
  icon_2.png — Holly leaf with berries
  icon_3.png — Pine tree
  icon_4.png — Ornament / bauble
  icon_5.png — Candy cane
  icon_6.png — Gift box
  icon_8.png — Snowman
  icon_9.png — Gingerbread man
"""

import os, shutil, math
from PIL import Image, ImageDraw

# ── Palette ──────────────────────────────────────────────────────────────
CRANBERRY   = (139, 32, 48)
GOLD        = (199, 169, 78)
WARM_SNOW   = (255, 248, 240)
PINE_GREEN  = (45, 64, 56)
CANDLELIGHT = (212, 200, 176)

SIZE = 100

# Output dirs
ICONS_DIR      = os.path.join(os.path.dirname(__file__), '..', 'themes', 'christmas', 'icons')
PROCESSED_DIR  = os.path.join(os.path.dirname(__file__), '..', 'assets', 'processed_icons')


def new_img():
    return Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))


# ─── icon_0: Snowflake ──────────────────────────────────────────────────
def draw_snowflake():
    img = new_img()
    d = ImageDraw.Draw(img)
    cx, cy = 50, 50
    length = 38
    w = 3
    for angle_deg in range(0, 360, 60):
        a = math.radians(angle_deg)
        ex, ey = cx + length * math.cos(a), cy + length * math.sin(a)
        d.line([(cx, cy), (ex, ey)], fill=WARM_SNOW, width=w)
        # small branches
        for frac in (0.45, 0.7):
            bx, by = cx + length * frac * math.cos(a), cy + length * frac * math.sin(a)
            for side in (-1, 1):
                ba = a + side * math.radians(45)
                bex = bx + 10 * math.cos(ba)
                bey = by + 10 * math.sin(ba)
                d.line([(bx, by), (bex, bey)], fill=WARM_SNOW, width=2)
    # centre dot
    d.ellipse([cx-4, cy-4, cx+4, cy+4], fill=CANDLELIGHT)
    return img


# ─── icon_1: Christmas Star ─────────────────────────────────────────────
def draw_star():
    img = new_img()
    d = ImageDraw.Draw(img)
    cx, cy = 50, 48
    outer_r, inner_r = 40, 16
    points = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        r = outer_r if i % 2 == 0 else inner_r
        points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(points, fill=GOLD, outline=CANDLELIGHT)
    # highlight dot
    d.ellipse([cx-5, cy-5, cx+5, cy+5], fill=CANDLELIGHT)
    return img


# ─── icon_2: Holly Leaf with Berries ────────────────────────────────────
def draw_holly():
    img = new_img()
    d = ImageDraw.Draw(img)
    # Two leaves as rotated ellipses (approximated with polygons)
    def leaf(cx, cy, angle, size=30):
        pts = []
        for i in range(20):
            t = i / 20 * 2 * math.pi
            # leaf shape: wider in middle
            rx = size
            ry = size * 0.4
            x = rx * math.cos(t)
            y = ry * math.sin(t)
            # add pointy tips via slight distortion
            if abs(math.cos(t)) > 0.7:
                y *= 0.6
            # rotate
            ra = math.radians(angle)
            xr = x * math.cos(ra) - y * math.sin(ra)
            yr = x * math.sin(ra) + y * math.cos(ra)
            pts.append((cx + xr, cy + yr))
        d.polygon(pts, fill=PINE_GREEN, outline=CANDLELIGHT)
        # vein
        x1 = cx - size * 0.7 * math.cos(math.radians(angle))
        y1 = cy - size * 0.7 * math.sin(math.radians(angle))
        x2 = cx + size * 0.7 * math.cos(math.radians(angle))
        y2 = cy + size * 0.7 * math.sin(math.radians(angle))
        d.line([(x1, y1), (x2, y2)], fill=CANDLELIGHT, width=1)

    leaf(42, 52, -30)
    leaf(58, 52, 30)
    # Berries
    for bx, by in [(50, 38), (42, 42), (58, 42)]:
        d.ellipse([bx-6, by-6, bx+6, by+6], fill=CRANBERRY, outline=GOLD)
    return img


# ─── icon_3: Pine Tree ──────────────────────────────────────────────────
def draw_pine_tree():
    img = new_img()
    d = ImageDraw.Draw(img)
    # Three stacked triangles
    layers = [
        [(50, 10), (28, 42), (72, 42)],
        [(50, 28), (22, 62), (78, 62)],
        [(50, 46), (16, 82), (84, 82)],
    ]
    for tri in layers:
        d.polygon(tri, fill=PINE_GREEN, outline=CANDLELIGHT)
    # Trunk
    d.rectangle([43, 82, 57, 95], fill=CRANBERRY)
    # Star on top
    d.polygon([(50, 5), (47, 14), (53, 14)], fill=GOLD)
    d.ellipse([47, 5, 53, 11], fill=GOLD)
    return img


# ─── icon_4: Ornament / Bauble ──────────────────────────────────────────
def draw_ornament():
    img = new_img()
    d = ImageDraw.Draw(img)
    cx, cy = 50, 55
    r = 30
    # ball
    d.ellipse([cx-r, cy-r, cx+r, cy+r], fill=CRANBERRY, outline=GOLD)
    # shine highlight
    d.ellipse([cx-14, cy-20, cx-4, cy-10], fill=(200, 80, 90, 180))
    # cap
    d.rectangle([44, 22, 56, 30], fill=GOLD)
    # hook
    d.arc([44, 10, 56, 24], start=180, end=0, fill=GOLD, width=2)
    # decorative stripe
    d.arc([cx-r, cy-r, cx+r, cy+r], start=200, end=340, fill=GOLD, width=2)
    return img


# ─── icon_5: Candy Cane ─────────────────────────────────────────────────
def draw_candy_cane():
    img = new_img()
    d = ImageDraw.Draw(img)
    # Vertical part (slightly angled)
    w = 12
    # Draw cane shape: vertical shaft + curved hook at top
    # Hook (arc at top)
    hook_cx, hook_cy = 55, 30
    hook_r = 18
    # Draw thick arc for hook
    for offset in range(-w//2, w//2 + 1):
        d.arc([hook_cx - hook_r + offset, hook_cy - hook_r,
               hook_cx + hook_r + offset, hook_cy + hook_r],
              start=180, end=0, fill=WARM_SNOW, width=2)
    # Straight part
    d.rectangle([hook_cx - hook_r - w//2, hook_cy, hook_cx - hook_r + w//2, 90], fill=WARM_SNOW)
    # Red stripes (diagonal)
    for y in range(hook_cy, 91, 12):
        pts = [
            (hook_cx - hook_r - w//2, y),
            (hook_cx - hook_r + w//2, y),
            (hook_cx - hook_r + w//2, y + 6),
            (hook_cx - hook_r - w//2, y + 6),
        ]
        d.polygon(pts, fill=CRANBERRY)
    # Re-draw hook outline
    d.arc([hook_cx - hook_r - w//2, hook_cy - hook_r - w//2,
           hook_cx + hook_r + w//2, hook_cy + hook_r + w//2],
          start=180, end=0, fill=CRANBERRY, width=3)
    return img


# ─── icon_6: Gift Box ───────────────────────────────────────────────────
def draw_gift_box():
    img = new_img()
    d = ImageDraw.Draw(img)
    # Box body
    d.rectangle([18, 40, 82, 85], fill=CRANBERRY, outline=GOLD)
    # Lid
    d.rectangle([14, 30, 86, 42], fill=CRANBERRY, outline=GOLD)
    # Ribbon vertical
    d.rectangle([46, 30, 54, 85], fill=GOLD)
    # Ribbon horizontal
    d.rectangle([18, 55, 82, 63], fill=GOLD)
    # Bow
    d.ellipse([30, 12, 50, 34], fill=GOLD, outline=CANDLELIGHT)
    d.ellipse([50, 12, 70, 34], fill=GOLD, outline=CANDLELIGHT)
    d.ellipse([45, 22, 55, 34], fill=CRANBERRY)
    return img


# ─── icon_8: Snowman ────────────────────────────────────────────────────
def draw_snowman():
    img = new_img()
    d = ImageDraw.Draw(img)
    # Bottom ball
    d.ellipse([25, 58, 75, 98], fill=WARM_SNOW, outline=CANDLELIGHT)
    # Middle ball
    d.ellipse([30, 35, 70, 68], fill=WARM_SNOW, outline=CANDLELIGHT)
    # Head
    d.ellipse([35, 12, 65, 40], fill=WARM_SNOW, outline=CANDLELIGHT)
    # Eyes
    d.ellipse([42, 20, 47, 25], fill=PINE_GREEN)
    d.ellipse([53, 20, 58, 25], fill=PINE_GREEN)
    # Nose (carrot)
    d.polygon([(50, 27), (60, 30), (50, 33)], fill=GOLD)
    # Buttons
    for by in [44, 52, 60]:
        d.ellipse([47, by, 53, by+4], fill=PINE_GREEN)
    # Hat
    d.rectangle([37, 8, 63, 16], fill=PINE_GREEN)
    d.rectangle([40, 0, 60, 10], fill=PINE_GREEN)
    d.rectangle([37, 12, 63, 15], fill=CRANBERRY)
    # Scarf
    d.rectangle([32, 36, 68, 42], fill=CRANBERRY)
    d.rectangle([58, 40, 66, 54], fill=CRANBERRY)
    return img


# ─── icon_9: Gingerbread Man ────────────────────────────────────────────
def draw_gingerbread():
    img = new_img()
    d = ImageDraw.Draw(img)
    brown = (180, 120, 60)
    dark_brown = (140, 90, 40)
    # Head
    d.ellipse([35, 5, 65, 35], fill=brown, outline=dark_brown)
    # Body
    d.ellipse([32, 30, 68, 70], fill=brown, outline=dark_brown)
    # Arms
    d.ellipse([8, 32, 36, 50], fill=brown, outline=dark_brown)
    d.ellipse([64, 32, 92, 50], fill=brown, outline=dark_brown)
    # Legs
    d.ellipse([25, 60, 48, 95], fill=brown, outline=dark_brown)
    d.ellipse([52, 60, 75, 95], fill=brown, outline=dark_brown)
    # Eyes
    d.ellipse([41, 14, 47, 20], fill=WARM_SNOW)
    d.ellipse([53, 14, 59, 20], fill=WARM_SNOW)
    # Mouth
    d.arc([42, 20, 58, 32], start=0, end=180, fill=WARM_SNOW, width=2)
    # Buttons
    for by in [38, 48, 58]:
        d.ellipse([46, by, 54, by+5], fill=CRANBERRY, outline=GOLD)
    # Bow tie
    d.polygon([(42, 32), (50, 37), (42, 42)], fill=CRANBERRY)
    d.polygon([(58, 32), (50, 37), (58, 42)], fill=CRANBERRY)
    # Icing on arms/legs
    d.arc([10, 34, 34, 48], start=0, end=180, fill=WARM_SNOW, width=2)
    d.arc([66, 34, 90, 48], start=0, end=180, fill=WARM_SNOW, width=2)
    return img


# ─── Main ────────────────────────────────────────────────────────────────
def main():
    os.makedirs(ICONS_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    icons = {
        'icon_0.png': ('Snowflake',           draw_snowflake),
        'icon_1.png': ('Christmas Star',       draw_star),
        'icon_2.png': ('Holly Leaf & Berries', draw_holly),
        'icon_3.png': ('Pine Tree',            draw_pine_tree),
        'icon_4.png': ('Ornament / Bauble',    draw_ornament),
        'icon_5.png': ('Candy Cane',           draw_candy_cane),
        'icon_6.png': ('Gift Box',             draw_gift_box),
        'icon_8.png': ('Snowman',              draw_snowman),
        'icon_9.png': ('Gingerbread Man',      draw_gingerbread),
    }

    for fname, (label, draw_fn) in icons.items():
        img = draw_fn()
        path_theme = os.path.join(ICONS_DIR, fname)
        path_proc  = os.path.join(PROCESSED_DIR, fname)
        img.save(path_theme, 'PNG')
        shutil.copy2(path_theme, path_proc)
        print(f'  OK {fname:16s}  {label}')

    print(f'\nSaved {len(icons)} icons to:')
    print(f'  {os.path.abspath(ICONS_DIR)}')
    print(f'  {os.path.abspath(PROCESSED_DIR)}')


if __name__ == '__main__':
    main()
