#!/usr/bin/env python3
"""prep_photo.py — one-time local image prep for the ASCII portrait.

Removes the background with rembg and boosts *local* contrast with CLAHE so the
face reads as real highlights/shadows instead of a dark blob. Output is an RGBA
PNG with a transparent background, ready for make_ascii_svg.py.

Usage:
    python scripts/prep_photo.py <input photo> <output.png>
"""
import sys
import numpy as np
import cv2
from PIL import Image, ImageOps

# --- tune here -------------------------------------------------------------
CLIP_LIMIT = 2.6      # CLAHE local-contrast strength (higher = punchier face)
TILE       = 8        # CLAHE tile grid (smaller = more local)
MAX_SIDE   = 1000     # downscale huge photos before rembg for speed
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 3:
        print("usage: prep_photo.py <input> <output.png>")
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]

    # 1. read + fix EXIF rotation (phone photos)
    img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    if max(img.size) > MAX_SIDE:
        s = MAX_SIDE / max(img.size)
        img = img.resize((round(img.size[0] * s), round(img.size[1] * s)), Image.LANCZOS)

    # 2. remove background -> RGBA with a real alpha matte
    from rembg import remove          # imported lazily; heavy onnx model
    cut = remove(img).convert("RGBA")

    # 3. CLAHE on the L channel of LAB, keep the alpha matte untouched
    arr   = np.array(cut)
    rgb   = arr[..., :3]
    alpha = arr[..., 3]
    lab   = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=(TILE, TILE))
    l2 = clahe.apply(l)
    rgb2 = cv2.cvtColor(cv2.merge((l2, a, b)), cv2.COLOR_LAB2RGB)
    out  = np.dstack([rgb2, alpha]).astype(np.uint8)

    Image.fromarray(out, "RGBA").save(dst)
    op = int((alpha > 20).mean() * 100)
    print(f"saved {dst}  {out.shape[1]}x{out.shape[0]}  (~{op}% subject)")


if __name__ == "__main__":
    main()
