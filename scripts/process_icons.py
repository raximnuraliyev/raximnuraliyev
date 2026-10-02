#!/usr/bin/env python3
"""
One-off local step: turn the source images in assets/icons/ into
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


# ── Frame: black etching -> silver ink on transparent ──────────────
def frame():
    rgb = load("frame.jpg")
    alpha = ink_to_alpha(lum(rgb), 228, 70) ** 0.85
    alpha[640:668, 585:660] = 0     # watermark, right
    alpha[675:700, 10:65] = 0       # watermark, left
    h = alpha.shape[0]
    cut = 670                       # split between the top and bottom ornament groups
    col = solid(rgb.shape, SILVER)
    save(col[:cut], alpha[:cut], "frame_top.png", crop=False)
    save(col[cut:], alpha[cut:], "frame_bottom.png", crop=False)


# ── Castle: keep as a dark engraved silhouette ─────────────────────
def castle():
    rgb = load("castle.jpg")
    alpha = ink_to_alpha(lum(rgb), 245, 25) ** 0.9
    save(solid(rgb.shape, (11, 11, 12)), alpha, "castle.png", max_w=560)


# ── Bats: strip the fake checkerboard, recolor as smoky grey ───────
def bats():
    rgb = load("bats.jpg")
    # the "transparent" checkerboard is baked in: 18px cells of 255 / 236
    ys, xs = np.mgrid[: rgb.shape[0], : rgb.shape[1]]
    white_cell = (((xs - 574) // 18 + (ys - 307) // 18) % 2) == 1
    paper = np.where(white_cell, 255.0, 236.0)
    alpha = np.clip((paper - lum(rgb) - 6) / (paper - 20), 0, 1)
    alpha = nd.median_filter(alpha, 3)
    alpha[alpha < 0.18] = 0
    # feather the hard image edges so the flock dissolves into the canvas
    h, w = alpha.shape
    ys, xs = np.mgrid[:h, :w]
    alpha *= np.clip(np.minimum.reduce([xs, ys, w - 1 - xs, h - 1 - ys]) / 60, 0, 1)
    save(solid(rgb.shape, (150, 146, 140)), alpha, "bats.png", max_w=420)


# ── Lettering: black stencil -> bone white, pumpkin tinted orange ──
def lettering():
    rgb = load("happy_halloween.jpg")
    alpha = ink_to_alpha(lum(rgb), 235, 60)
    col = solid(rgb.shape, BONE)
    ys, xs = np.mgrid[: rgb.shape[0], : rgb.shape[1]]
    pumpkin = ((xs - 372) / 50) ** 2 + ((ys - 245) / 50) ** 2 < 1
    col[pumpkin] = (232, 116, 42)
    save(col, alpha, "happy_halloween.png", max_w=560)


# ── Graveyard: black silhouette (sits on a fog glow in the SVG) ────
def graveyard():
    rgb = load("graveyard.jpg")
    alpha = ink_to_alpha(lum(rgb), 235, 40)
    save(solid(rgb.shape, (11, 11, 12)), alpha, "graveyard.png", max_w=560)


# ── Stickers: flood the paper away, keep the art ───────────────────
def sticker(src, name, tol, max_w=260):
    rgb = load(src)
    bg = flood_background(rgb, tol)
    bg = nd.binary_opening(bg, iterations=1)
    alpha = drop_specks(soften(~bg, 0.8))
    save(rgb, alpha, name, max_w=max_w)


# ── Garland: paper is cut into pockets by the string, so key it out
#    everywhere; relight the black string/bats/spiders so they read ──
def garland():
    rgb = load("pumpkin_garland.jpg")
    L = lum(rgb)
    sat = rgb.max(2) - rgb.min(2)
    alpha = drop_specks(np.clip((242 - L) / 40, 0, 1) * (1 - (sat < 20) * (L > 225)), 0.002)
    orange = nd.binary_dilation((sat > 80) & (rgb[..., 0] > 150), iterations=5)
    ink = (sat < 50) & ~orange
    col = rgb.copy()
    col[ink] = np.array([168, 162, 152], np.float32)
    save(col, alpha, "pumpkin_garland.png", max_w=600)


# ── Ink drawings: black on paper -> silver ink on transparent ─────
def ink(src, name, white=225, black=60, color=SILVER, max_w=360):
    rgb = load(src)
    alpha = ink_to_alpha(lum(rgb), white, black)
    e = 8                                   # scanned page edges
    alpha[:e], alpha[-e:], alpha[:, :e], alpha[:, -e:] = 0, 0, 0, 0
    alpha = drop_specks(alpha, 0.004)
    save(solid(rgb.shape, color), alpha, name, max_w=max_w)


# ── Photos: AI cut-out of the person, toned to monochrome ─────────
def photo(src, name, max_w=420):
    try:
        from rembg import remove, new_session
    except ImportError:
        print(f"  {name:22s} skipped (pip install rembg)")
        return
    global _rembg
    if "_rembg" not in globals():
        _rembg = new_session("u2net")
    cut = np.asarray(remove(Image.open(SRC / src).convert("RGB"), session=_rembg)).astype(np.float32)
    grey = lum(cut[..., :3])[..., None]
    alpha = drop_specks(cut[..., 3] / 255)
    save(np.broadcast_to(grey, cut.shape[:2] + (3,)).copy(), alpha, name, max_w=max_w, grey=True)


# ── Portrait on black: the black *is* the background, key it out ───
def glow_portrait(src, name, max_w=360):
    rgb = load(src)
    L = lum(rgb)
    alpha = drop_specks(np.clip((L - 35) / 90, 0, 1), 0.01)
    save(solid(rgb.shape, BONE) * (L[..., None] / 255) ** 0.4, alpha, name, max_w=max_w)


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
    frame()
    castle()
    bats()
    lettering()
    graveyard()
    sticker("ghost.jpg", "ghost.png", 238)
    sticker("snoopy_reading.jpg", "snoopy.png", 232)
    sticker("spotify_code.jpg", "spotify_code.png", 236, max_w=320)
    garland()
    ink("billie_letter.jpg", "billie_letter.png", max_w=300)
    ink("you_with_me.jpg", "you_with_me.png", max_w=220)
    ink("signature.jpg", "signature.png", max_w=260)
    ink("sticker_63.jpg", "sticker_63.png", white=200, max_w=220)
    ink("winged.jpg", "winged.png", max_w=260)
    ink("snake.jpg", "snake.png", white=215, max_w=260)
    ink("blohsh.jpg", "blohsh.png", max_w=120)
    ink("centipede.jpg", "centipede.png", max_w=140)
    ink("spiderweb.jpg", "spiderweb.png", white=222, max_w=300)
    photo("newt_1.jpg", "newt_1.png")
    photo("newt_2.jpg", "newt_2.png")
    photo("billie_portrait.jpg", "billie_portrait.png")
    glow_portrait("billie_glow.jpg", "billie_glow.png")
    eyes()
    print("done.")
