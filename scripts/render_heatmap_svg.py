#!/usr/bin/env python3
"""render_heatmap_svg.py — data/contributions.json -> contrib-heatmap.svg

A GitHub-style grid of boxes that reveal cell-by-cell in a left-to-right sweep
(SMIL, so it animates inside a README <img>), in MONOCHROME grays instead of
green. Month + weekday labels, a Less->More legend, and real streak stats.

    python scripts/render_heatmap_svg.py

Also writes contrib-heatmap.preview.png.
"""
import json
import os
from datetime import date
from PIL import Image, ImageDraw, ImageFont

SRC = os.path.join("data", "contributions.json")
OUT_SVG = "contrib-heatmap.svg"
OUT_PNG = "contrib-heatmap.preview.png"

# --- look ------------------------------------------------------------------
CELL = 13
GAP = 3
STEP = CELL + GAP
LEFT = 38                 # room for weekday labels
TOP = 26                  # room for month labels
BG = "#0d1117"            # preview bg (GitHub dark); SVG stays transparent
LABEL = "#7d8894"
TEXT = "#c9d1d9"
FONT = "'SF Mono','Cascadia Code',Menlo,Consolas,monospace"
# grayscale ramp for levels 0..4 (empty -> most active)
LEVELS = ["#21262d", "#4d5763", "#7d8894", "#aeb7c2", "#e6edf3"]        # dark theme
LEVELS_LIGHT = ["#ebedf0", "#c6cdd5", "#99a2ad", "#636c76", "#24292f"]  # light theme
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def gh_wday(iso):
    y, m, d = map(int, iso.split("-"))
    return (date(y, m, d).weekday() + 1) % 7   # Sun=0 .. Sat=6


def grid(days):
    """Return cells [(col,row,level,date)], ncols, and col->first-date map."""
    off = gh_wday(days[0]["date"])
    cells, col_date = [], {}
    for i, day in enumerate(days):
        idx = i + off
        col, row = idx // 7, idx % 7
        cells.append((col, row, day["level"], day["date"]))
        col_date.setdefault(col, day["date"])
    ncols = cells[-1][0] + 1
    return cells, ncols, col_date


def month_labels(col_date, ncols):
    out, last = [], None
    for c in range(ncols):
        iso = col_date.get(c)
        if not iso:
            continue
        y, m, d = map(int, iso.split("-"))
        if m != last and d <= 7:
            out.append((c, MONTHS[m - 1]))
            last = m
    return out


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    days = data["days"]
    cells, ncols, col_date = grid(days)
    months = month_labels(col_date, ncols)

    gridW = ncols * STEP
    W = LEFT + gridW + 8
    H = TOP + 7 * STEP + 52

    total = data["total"]
    cur = data["current_streak"]
    lng = data["longest_streak"]

    # ---- SVG ----
    lv = "".join(f'.l{i}{{fill:var(--l{i})}}' for i in range(5))
    dark = ";".join(f'--l{i}:{LEVELS[i]}' for i in range(5))
    light = ";".join(f'--l{i}:{c}' for i, c in enumerate(LEVELS_LIGHT))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'width="{W}" height="{H}" font-family="{FONT}">',
         '<style>'
         f':root{{--lbl:{LABEL};--txt:{TEXT};{dark}}}'
         '@media (prefers-color-scheme:light){:root{'
         f'--lbl:#59636e;--txt:#1f2328;{light}}}'
         'text{font-size:11px;fill:var(--lbl)}'
         '.s{font-size:12px;fill:var(--txt)}'
         f'{lv}</style>']

    # month labels
    for c, name in months:
        o.append(f'<text x="{LEFT + c*STEP}" y="{TOP-8}">{name}</text>')
    # weekday labels
    for row, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        o.append(f'<text x="0" y="{TOP + row*STEP + CELL-2}">{name}</text>')

    # cells (sweeping reveal)
    for col, row, level, iso in cells:
        x = LEFT + col * STEP
        y = TOP + row * STEP
        begin = round(col * 0.020 + row * 0.010, 3)
        o.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'class="l{level}" opacity="0">'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" '
            f'dur="0.35s" fill="freeze"/></rect>'
        )

    base = TOP + 7 * STEP + 22
    # stats (left)
    o.append(f'<text x="{LEFT}" y="{base}" class="s">'
             f'{total:,} contributions in the last year</text>')
    o.append(f'<text x="{LEFT}" y="{base+20}">'
             f'Current streak {cur} days   •   Longest {lng} days</text>')
    # legend (right)
    lx = W - 8 - (5 * STEP) - 78
    o.append(f'<text x="{lx}" y="{base}">Less</text>')
    for i, col in enumerate(LEVELS):
        o.append(f'<rect x="{lx + 34 + i*STEP}" y="{base-11}" width="{CELL}" '
                 f'height="{CELL}" rx="2.5" class="l{i}"/>')
    o.append(f'<text x="{lx + 34 + 5*STEP + 4}" y="{base}">More</text>')
    o.append("</svg>")
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write("".join(o))

    write_preview(cells, ncols, months, W, H, total, cur, lng)
    print(f"{OUT_SVG}  {W}x{H}  ({ncols} weeks, {len(cells)} days)")
    print(f"{OUT_PNG}  preview written")


def write_preview(cells, ncols, months, W, H, total, cur, lng):
    s = 2
    img = Image.new("RGB", (W*s, H*s), BG)
    d = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 11*s)
        fb = ImageFont.truetype(r"C:\Windows\Fonts\consola.ttf", 12*s)
    except OSError:
        f = fb = ImageFont.load_default()
    for c, name in months:
        d.text(((LEFT + c*STEP)*s, (TOP-20)*s), name, font=f, fill=LABEL)
    for row, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        d.text((0, (TOP + row*STEP)*s), name, font=f, fill=LABEL)
    for col, row, level, iso in cells:
        x = (LEFT + col*STEP)*s
        y = (TOP + row*STEP)*s
        d.rounded_rectangle([x, y, x+CELL*s, y+CELL*s], radius=2.5*s,
                            fill=LEVELS[level])
    base = TOP + 7*STEP + 22
    d.text((LEFT*s, (base-12)*s), f"{total:,} contributions in the last year",
           font=fb, fill=TEXT)
    d.text((LEFT*s, (base+8)*s),
           f"Current streak {cur} days   -   Longest {lng} days", font=f, fill=LABEL)
    lx = W - 8 - (5*STEP) - 78
    d.text((lx*s, (base-12)*s), "Less", font=f, fill=LABEL)
    for i, col in enumerate(LEVELS):
        x = (lx + 34 + i*STEP)*s
        d.rounded_rectangle([x, (base-11)*s, x+CELL*s, (base-11+CELL)*s],
                            radius=2.5*s, fill=col)
    d.text(((lx + 34 + 5*STEP + 4)*s, (base-12)*s), "More", font=f, fill=LABEL)
    img.save(OUT_PNG)


if __name__ == "__main__":
    main()
