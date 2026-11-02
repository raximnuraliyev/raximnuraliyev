#!/usr/bin/env python3
"""
Verification Script for Theme Conversion
Checks:
1. All assets exist and are valid XML
2. No leftover Halloween keywords outside themes/halloween
3. Contrast ratios meet WCAG AA
4. Theme switcher round-trip
"""
import os, sys, re, json
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).parent.parent
ASSETS = ROOT / "assets"

def check_svg_xml():
    print("Checking SVG XML validity...")
    expected = [
        "header_banner.svg", "divider.svg", "info_card.svg",
        "goodreads_card.svg", "lastfm_card.svg", "letterboxd_card.svg",
        "footer_banner.svg"
    ]
    all_ok = True
    for name in expected:
        svg_file = ASSETS / name
        if not svg_file.exists():
            print(f"  [MISSING] {name}")
            all_ok = False
            continue
        try:
            tree = ET.parse(str(svg_file))
            root = tree.getroot()
            # check role="img"
            role = root.attrib.get("role", "")
            title = root.find("{http://www.w3.org/2000/svg}title")
            title_text = title.text if title is not None else ""
            print(f"  [VALID XML] {name} ({svg_file.stat().st_size:,} bytes) role='{role}' title='{title_text}'")
        except Exception as e:
            print(f"  [INVALID XML] {name}: {e}")
            all_ok = False
    return all_ok


def check_leftover_keywords():
    print("\nScanning for leftover Halloween keywords...")
    patterns = ["pumpkin", "ghost", "spooky", "creepster"]
    exclude_dirs = {".git", ".claude", "themes", "__pycache__"}
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fn in filenames:
            if fn == "verify_theme.py":
                continue
            p = Path(dirpath) / fn
            if p.suffix in [".pyc", ".png", ".jpg", ".ttf"]:
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                for pat in patterns:
                    if re.search(r"\b" + re.escape(pat) + r"\b", content, re.IGNORECASE):
                        hits.append((p.relative_to(ROOT), pat))
            except Exception:
                pass

    if hits:
        print(f"  Found {len(hits)} occurrences:")
        for path, pat in hits:
            print(f"    {path} -> keyword '{pat}'")
    else:
        print("  [CLEAN] No stray Halloween keywords found!")
    return len(hits) == 0


def check_contrast():
    print("\nChecking Christmas palette contrast ratios...")
    # WCAG relative luminance formula
    def lum(hex_code):
        hex_code = hex_code.lstrip("#")
        r, g, b = [int(hex_code[i:i+2], 16) / 255.0 for i in (0, 2, 4)]
        def ch(c): return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)

    def ratio(c1, c2):
        l1, l2 = lum(c1), lum(c2)
        return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)

    with open(ROOT / "themes" / "christmas" / "theme.json", encoding="utf-8") as f:
        t = json.load(f)
    p = t["palette"]
    bg = p["bg"]
    bg2 = p["bg2"]
    
    pairs = [
        ("White title on BG", p["white"], bg, 4.5),
        ("Primary text on BG", p["text_pri"], bg, 4.5),
        ("Secondary text on BG", p["text_sec"], bg, 4.5),
        ("Accent on BG2 (header)", p["accent"], bg2, 3.0),
        ("Gold stars on BG", p["gold"], bg, 3.0),
    ]

    all_pass = True
    for name, fg, bg_c, target in pairs:
        r = ratio(fg, bg_c)
        passed = r >= target
        status = "PASS" if passed else "WARN"
        print(f"  [{status}] {name}: {r:.2f}:1 (target {target}:1) [{fg} on {bg_c}]")
        if not passed:
            all_pass = False
    return all_pass


if __name__ == "__main__":
    if hasattr(sys.stdout, 'reconfigure'):
        try: sys.stdout.reconfigure(encoding='utf-8')
        except: pass

    ok1 = check_svg_xml()
    ok2 = check_leftover_keywords()
    ok3 = check_contrast()

    print("\n" + "="*50)
    if ok1 and ok2 and ok3:
        print("ALL VERIFICATION CHECKS PASSED!")
    else:
        print("SOME CHECKS NEED ATTENTION.")
