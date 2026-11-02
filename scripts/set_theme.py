#!/usr/bin/env python3
"""
Theme Switcher — copies the active theme's icons into assets/processed_icons
and regenerates static SVGs (header, divider, info_card, footer).

Usage:
    python scripts/set_theme.py christmas
    python scripts/set_theme.py halloween
"""
import sys, shutil, json, subprocess, re
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT = Path(__file__).parent.parent
THEMES = ROOT / "themes"
ASSETS = ROOT / "assets"
ICONS_DEST = ASSETS / "processed_icons"
ACTIVE_THEME_FILE = ROOT / "active_theme.json"


def set_theme(name: str) -> None:
    theme_dir = THEMES / name
    if not theme_dir.exists():
        avail = [d.name for d in THEMES.iterdir() if d.is_dir()]
        print(f"Error: theme '{name}' not found. Available: {avail}")
        sys.exit(1)

    theme_json = theme_dir / "theme.json"
    if not theme_json.exists():
        print(f"Error: {theme_json} not found.")
        sys.exit(1)
    theme_data = json.loads(theme_json.read_text(encoding="utf-8"))

    # 1. Copy icons
    icons_src = theme_dir / "icons"
    if icons_src.exists():
        ICONS_DEST.mkdir(parents=True, exist_ok=True)
        # Remove old icons
        for f in ICONS_DEST.glob("icon_*.png"):
            f.unlink()
        # Copy new ones
        copied = 0
        for png in sorted(icons_src.glob("icon_*.png")):
            shutil.copy2(png, ICONS_DEST / png.name)
            copied += 1
        print(f"  Copied {copied} icons -> assets/processed_icons/")
    else:
        print(f"  Warning: no icons directory in theme '{name}'")

    # 2. Write active_theme pointer
    ACTIVE_THEME_FILE.write_text(json.dumps({"theme": name}, indent=2), encoding="utf-8")
    print(f"  Wrote active_theme.json -> {name}")

    # 3. Regenerate all SVGs with the new theme
    print("  Regenerating SVGs with generate_cards.py...")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_cards.py")], check=True)

    # 4. Update README.md section titles & badge colors
    update_readme(theme_data)

    print(f"\n[OK] Theme '{name}' activated successfully.")


def update_readme(theme_data: dict) -> None:
    readme_path = ROOT / "README.md"
    if not readme_path.exists():
        return
    
    content = readme_path.read_text(encoding="utf-8")
    labels = theme_data.get("labels", {})
    hits = theme_data.get("hits_badge", {})
    typing = theme_data.get("typing_svg", {})

    # Section titles
    if "section_stack" in labels:
        content = re.sub(
            r'### (The Apothecary|The Workshop[^\n]*)',
            f"### {labels['section_stack']}",
            content
        )
    if "section_archives" in labels:
        content = re.sub(
            r'### (The Archives|The Advent Calendar[^\n]*)',
            f"### {labels['section_archives']}",
            content
        )
    if "footer_alt" in labels:
        content = re.sub(
            r'<img src="\./assets/footer_banner\.svg"[^/]*/>',
            f'<img src="./assets/footer_banner.svg" alt="{labels["footer_alt"]}" width="100%" />',
            content
        )

    # Badge colors
    if "color" in hits and "label_color" in hits:
        content = re.sub(
            r'(hits\.sh/github\.com/raximnuraliyev/views\.svg\?style=for-the-badge&label=Profile%20Views&color=)[0-9A-Fa-f]{6}&labelColor=[0-9A-Fa-f]{6}',
            rf"\g<1>{hits['color']}&labelColor={hits['label_color']}",
            content
        )
    if "color" in typing:
        content = re.sub(
            r'(readme-typing-svg\.demolab\.com\?[^"\n]*&color=)[0-9A-Fa-f]{6}',
            rf"\g<1>{typing['color']}",
            content
        )

    readme_path.write_text(content, encoding="utf-8")
    print("  Updated README.md section titles and badge styles.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/set_theme.py <theme_name>")
        print("  e.g. python scripts/set_theme.py christmas")
        sys.exit(1)
    name = sys.argv[1].strip().lower()
    print(f"Switching theme to: {name}")
    set_theme(name)
