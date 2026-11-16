#!/usr/bin/env python3
"""
Christmas 2026 — one-off local step: turn the source images in assets/icons/ into
background-free PNGs in assets/ornaments/ that generate_cards.py embeds.

Needs Pillow, numpy and scipy (not used in CI — the PNGs are committed).
The photo cut-outs also need rembg (its u2net model downloads on first use).
    python scripts/process_icons.py
"""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT = Path(__file__).parent.parent
SRC = ROOT / "assets" / "icons"
OUT = ROOT / "assets" / "ornaments"
OUT.mkdir(exist_ok=True)

SILVER = (216, 212, 204)
BONE = (232, 226, 214)


def load(name):
    return np.asarray(Image.open(SRC / name).convert("RGB")).astype(np.float32)


def lum(rgb):
    return rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)


def ink_to_alpha(L, white, black):
    """Dark ink -> opaque, paper -> transparent."""
    return np.clip((white - L) / (white - black), 0, 1)


def flood_background(rgb, tol):
    """Mask of near-white, low-saturation pixels connected to the image border."""
    L = lum(rgb)
    sat = rgb.max(2) - rgb.min(2)
    paper = (L > tol) & (sat < 28)
    lab, _ = nd.label(paper)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    edge = edge[edge != 0]
    return np.isin(lab, edge)


def drop_specks(alpha, keep=0.02):
    """Zero out small disconnected blobs (JPEG noise, stray marks)."""
    lab, n = nd.label(alpha > 0.1)
    if n < 2:
        return alpha
    sizes = nd.sum(np.ones_like(alpha), lab, range(1, n + 1))
    small = np.isin(lab, np.where(sizes < sizes.max() * keep)[0] + 1)
    alpha = alpha.copy()
    alpha[small] = 0
    return alpha


def save(rgb, alpha, name, crop=True, max_w=None, grey=False):
    a = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    img = Image.fromarray(np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), a]), "RGBA")
    if crop:
        bbox = img.getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
        img = img.crop(bbox)
    if max_w and img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.LANCZOS)
    if grey:   # two channels instead of four — photos embed at ~half the size
        img = img.convert("LA")
    img.save(OUT / name, optimize=True)
    print(f"  {name:22s} {img.size}")


def solid(shape, color):
    return np.broadcast_to(np.array(color, np.float32), shape[:2] + (3,)).copy()


def soften(mask, r=1.2):
    return nd.gaussian_filter(mask.astype(np.float32), r)


# ── Stickers: flood the paper away, keep the art ───────────────────
def sticker(src, name, tol, max_w=260):
    rgb = load(src)
    if rgb.shape[1] > 1400:               # huge Pinterest originals: work smaller
        im = Image.open(SRC / src).convert("RGB")
        im.thumbnail((1200, 1200), Image.LANCZOS)
        rgb = np.asarray(im).astype(np.float32)
    bg = flood_background(rgb, tol)
    bg = nd.binary_opening(bg, iterations=1)
    alpha = drop_specks(soften(~bg, 0.8))
    save(rgb, alpha, name, max_w=max_w)


# ── Already-transparent PNG stickers: just trim and shrink ───────
def cutout(src, name, max_w=260):
    im = Image.open(SRC / src).convert("RGBA")
    arr = np.asarray(im).astype(np.float32)
    save(arr[..., :3], arr[..., 3] / 255, name, max_w=max_w)


# ── Ink drawings: black on paper -> silver ink on transparent ─────
def ink(src, name, white=225, black=60, color=SILVER, max_w=360):
    rgb = load(src)
    alpha = ink_to_alpha(lum(rgb), white, black)
    e = 8                                   # scanned page edges
    alpha[:e], alpha[-e:], alpha[:, :e], alpha[:, -e:] = 0, 0, 0, 0
    alpha = drop_specks(alpha, 0.004)
    save(solid(rgb.shape, color), alpha, name, max_w=max_w)


# ── Photos: AI cut-out of the person, toned to monochrome ─────────
def photo(src, name, max_w=420, tone=1.0, keep=0.02, erase=()):
    """tone < 1 sinks bright whites toward the shadows (stark ink portraits)."""
    try:
        from rembg import remove, new_session
    except ImportError:
        print(f"  {name:22s} skipped (pip install rembg)")
        return
    global _rembg
    if "_rembg" not in globals():
        _rembg = new_session("u2net")
    cut = np.asarray(remove(Image.open(SRC / src).convert("RGB"), session=_rembg)).astype(np.float32)
    for x0, y0, x1, y1 in erase:          # stray bits the cut-out kept
        cut[y0:y1, x0:x1, 3] = 0
    grey = lum(cut[..., :3])[..., None] * tone
    alpha = drop_specks(cut[..., 3] / 255, keep)
    save(np.broadcast_to(grey, cut.shape[:2] + (3,)).copy(), alpha, name, max_w=max_w, grey=True)


# ── Close-up eyes: nothing to cut away, so dissolve the edges ─────
def eyes():
    rgb = load("eyes.jpg")
    h, w = rgb.shape[:2]
    ys, xs = np.mgrid[:h, :w]
    r = np.sqrt(((xs - w / 2) / (w * 0.52)) ** 2 + ((ys - h * 0.5) / (h * 0.56)) ** 2)
    alpha = np.clip((1 - r) / 0.6, 0, 1) ** 2
    grey = lum(rgb)[..., None]
    rgb = grey + (rgb - grey) * 0.45        # keep a ghost of the green iris
    save(rgb * 0.85, alpha, "eyes.png", crop=False, max_w=520)   # cropping would clip the fade


if __name__ == "__main__":
    print("Processing ornaments...")
    # Christmas keepsakes (Pinterest finds)
    sticker("snoopy_sleigh.jpg", "snoopy_sleigh.png", 236, max_w=300)
    sticker("snoopy_cocoa.png", "snoopy_cocoa.png", 236, max_w=240)
    sticker("snoopy_gingerbread.jpg", "snoopy_gingerbread.png", 236, max_w=220)
    sticker("snoopy_scarf.jpg", "snoopy_scarf.png", 236, max_w=220)
    sticker("cocoa_mug.jpg", "cocoa_mug.png", 236, max_w=140)
    cutout("snoopy_puffer.png", "snoopy_puffer.png", max_w=200)
    cutout("plaid_star.png", "plaid_star.png", max_w=120)
    cutout("snowman.png", "snowman.png", max_w=130)
    sticker("snoopy_reading.jpg", "snoopy.png", 232)
    # painted Spotify code card: no background to remove — shrink it, black & white
    card = Image.open(SRC / "spotify_code.webp").convert("L")
    card.resize((240, 300), Image.LANCZOS).save(OUT / "spotify_code.png", optimize=True)
    print(f"  {'spotify_code.png':22s} (240, 300)")
    SNOW = (236, 232, 222)
    ink("billie_letter.jpg", "billie_letter.png", color=SNOW, max_w=300)
    ink("you_with_me.jpg", "you_with_me.png", color=SNOW, max_w=220)
    ink("signature.jpg", "signature.png", color=(212, 175, 90), max_w=260)
    ink("sticker_63.jpg", "sticker_63.png", white=200, color=SNOW, max_w=220)
    ink("blohsh.jpg", "blohsh.png", color=SNOW, max_w=120)
    photo("newt_1.jpg", "newt_1.png")
    photo("george_russell.jpg", "george_russell.png", max_w=320, tone=0.62)
    photo("ellie.jpg", "ellie.png", max_w=320, tone=0.62, keep=0.3, erase=[(505, 250, 736, 736)])
    ink("journal_3.jpg", "journal_3.png", white=215, color=SNOW, max_w=220)
    eyes()
    print("done.")
