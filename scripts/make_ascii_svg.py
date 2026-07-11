#!/usr/bin/env python3
"""make_ascii_svg.py — source-prepped.png -> avi-ascii.svg

A clean, MONOCHROME ASCII portrait that "types" itself in like a terminal:
each row wipes in left-to-right, staggered top-to-bottom. The background of the
source is transparent, so the subject floats on blank space.

GitHub strips <script> from READMEs but DOES run SMIL/CSS inside an <img>-loaded
SVG, so all the motion lives here as SMIL <animate> and never 404s.

Also writes avi-ascii.preview.png (final frame) so you can eyeball it on any OS.

    python scripts/make_ascii_svg.py           # animated avi-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py  # SVG shows the final frame

Tune the LOOK with CONTRAST / GAMMA / WHITE_FLOOR; tune the TYPING with
ROW_DUR / STAGGER.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- input / output --------------------------------------------------------
SRC     = "source-prepped.png"
OUT_SVG = "avi-ascii.svg"
OUT_PNG = "avi-ascii.preview.png"

# --- look ------------------------------------------------------------------
COLS        = 92          # character columns (detail vs. size)
CONTRAST    = 1.34        # >1 = punchier
GAMMA       = 0.80        # <1 = brighter midtones / lighter face
WHITE_FLOOR = 0.14        # black-point lift; higher = cleaner, less shadow mush
COLOR       = "#d2d6db"   # ONE light-gray. never per-character rainbow.
BG          = "#0d1117"   # preview bg only (GitHub dark); SVG stays transparent

# --- crop (frame the subject) ----------------------------------------------
BBOX_ALPHA = 45           # alpha above this counts as "subject" for the bbox
KEEP_TOP   = 0.56         # keep this fraction of subject height from the top
                          #   (head + shoulders). set None to keep the whole body.
PAD_FRAC   = 0.05         # breathing room around the crop

# dark -> light. index 0 (space) only ever used for the removed background.
RAMP = " .,:;irsXA253hMHGS#9B&@"

# --- type animation --------------------------------------------------------
ROW_DUR = 0.45           # seconds for one row to wipe in
STAGGER = 0.055          # seconds between consecutive rows starting

# --- geometry --------------------------------------------------------------
FS = 14                  # font-size (px) in the SVG's own coordinate space
CW = FS * 0.60           # monospace advance width
LH = FS * 1.00           # line height
PAD = FS                 # padding around the art
STATIC = os.environ.get("STATIC") == "1"


def load_grid():
    """Return list[str] rows of the ASCII portrait."""
    im = Image.open(SRC).convert("RGBA")

    # frame the subject: tight bbox on the alpha matte, then keep the top slice
    a = np.asarray(im)[..., 3]
    ys, xs = np.where(a > BBOX_ALPHA)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        if KEEP_TOP:
            y1 = y0 + int((y1 - y0) * KEEP_TOP)
        px = int((x1 - x0) * PAD_FRAC)
        py = int((y1 - y0) * PAD_FRAC)
        im = im.crop((max(0, x0 - px), max(0, y0 - py),
                      min(im.size[0], x1 + px + 1), min(im.size[1], y1 + py + 1)))

    W, H = im.size
    rows = max(1, round(COLS * (H / W) * (CW / LH)))
    small = im.resize((COLS, rows), Image.LANCZOS)
    arr = np.asarray(small).astype(np.float32)
    rgb, alpha = arr[..., :3], arr[..., 3]

    # perceptual luminance 0..1
    lum = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]) / 255.0
    lum = np.power(np.clip(lum, 0, 1), GAMMA)
    lum = (lum - 0.5) * CONTRAST + 0.5
    lum = (lum - WHITE_FLOOR) / (1.0 - WHITE_FLOOR)
    lum = np.clip(lum, 0, 1)

    n = len(RAMP)
    lines = []
    for y in range(small.size[1]):
        chars = []
        for x in range(COLS):
            if alpha[y, x] < 110:                 # background -> blank
                chars.append(" ")
            else:                                  # subject -> never blank
                idx = 1 + int(round(lum[y, x] * (n - 2)))
                chars.append(RAMP[min(idx, n - 1)])
        # keep trailing spaces off the right edge but preserve internal ones
        lines.append("".join(chars).rstrip() or " ")
    return lines


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_svg(rows):
    width  = round(PAD * 2 + COLS * CW)
    height = round(PAD * 2 + len(rows) * LH)
    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'font-family="\'SF Mono\',\'Cascadia Code\',Menlo,Consolas,monospace">'
    )
    out.append(
        '<style>'
        f':root{{--ink:{COLOR}}}'
        '@media (prefers-color-scheme:light){:root{--ink:#2f343a}}'
        f'text{{font-size:{FS}px;fill:var(--ink);white-space:pre}}'
        '</style>'
    )
    for i, row in enumerate(rows):
        y = round(PAD + (i + 1) * LH - LH * 0.18, 2)
        roww = round(len(row) * CW + 2, 2)
        if STATIC:
            out.append(
                f'<text x="{PAD}" y="{y}" xml:space="preserve">{esc(row)}</text>'
            )
        else:
            begin = round(i * STAGGER, 3)
            out.append(
                f'<clipPath id="c{i}"><rect x="{PAD}" y="{round(PAD + i * LH,2)}" '
                f'width="0" height="{round(LH+2,2)}">'
                f'<animate attributeName="width" from="0" to="{roww}" '
                f'dur="{ROW_DUR}s" begin="{begin}s" fill="freeze" '
                f'calcMode="linear"/></rect></clipPath>'
                f'<text x="{PAD}" y="{y}" xml:space="preserve" '
                f'clip-path="url(#c{i})">{esc(row)}</text>'
            )
    out.append("</svg>")
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write("".join(out))
    return width, height


def write_preview(rows):
    """Render the final frame to a PNG so it can be inspected on any OS."""
    scale = 2
    fw, fh = CW * scale, LH * scale
    W = round((PAD * 2 + COLS * CW) * scale)
    H = round((PAD * 2 + len(rows) * LH) * scale)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    font = None
    for path in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"):
        try:
            font = ImageFont.truetype(path, round(FS * scale))
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
    for i, row in enumerate(rows):
        y = PAD * scale + i * fh
        for x, ch in enumerate(row):
            if ch != " ":
                d.text((PAD * scale + x * fw, y), ch, fill=COLOR, font=font)
    img.save(OUT_PNG)


def main():
    rows = load_grid()
    w, h = write_svg(rows)
    write_preview(rows)
    print(f"{OUT_SVG}  {w}x{h}  ({len(rows)} rows x {COLS} cols)"
          f"  {'STATIC' if STATIC else 'animated'}")
    print(f"{OUT_PNG}  preview written")


if __name__ == "__main__":
    main()
