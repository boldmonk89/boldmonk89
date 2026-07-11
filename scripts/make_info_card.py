#!/usr/bin/env python3
"""make_info_card.py — a neofetch-style info panel -> info-card.svg

Sits next to the ASCII portrait in the README. Monochrome terminal look:
`user@host`, a rule, then your experience / stack / highlights (NOT GitHub
stats — the contribution graph already covers those). Rows cascade in.

Also writes info-card.preview.png so you can eyeball it on any OS.

    python scripts/make_info_card.py

EDIT the two marked blocks below (HOST/USER and ROWS) to make it yours.
"""
from PIL import Image, ImageDraw, ImageFont

# ===========================================================================
# EDIT ME ===================================================================
USER = "tejas"
HOST = "boldmonk89"

ROWS = [
    ("Role",      "Defence Aspirant  x  Developer"),
    ("Focus",     "Full-stack web & products"),
    ("Frontend",  "Next.js / React / TypeScript"),
    ("Styling",   "Tailwind CSS / Framer Motion"),
    ("Backend",   "Supabase / PostgreSQL / Python"),
    ("Building",  "ZestCampus - campus food app"),
    ("Ethos",     "Ship fast, stay disciplined"),
    ("Portfolio", "tejassportfolio.vercel.app"),
    ("LinkedIn",  "in/tejascodes2006"),
    ("Instagram", "@traghavvv"),
]
# END EDIT ==================================================================
# ===========================================================================

OUT_SVG = "info-card.svg"
OUT_PNG = "info-card.preview.png"

# --- look ------------------------------------------------------------------
FS        = 21           # font-size (px)
CW        = FS * 0.60    # monospace advance
ROW_H     = 40           # vertical step per info row
PAD       = 34           # inner padding
KEY_COL   = "#e6edf3"    # bright gray for keys / title user
VAL_COL   = "#9aa4b2"    # muted gray for values
DIM_COL   = "#6b7482"    # rule + @host
BORDER    = "#30363d"    # panel border
BG        = "#0d1117"    # preview bg (GitHub dark); SVG panel fill is transparent
FONT      = "'SF Mono','Cascadia Code',Menlo,Consolas,monospace"

STAGGER   = 0.09         # seconds between rows appearing
ROW_DUR   = 0.5


def layout():
    keyw = max(len(k) for k, _ in ROWS)
    title = f"{USER}@{HOST}"
    rule = "-" * len(title)
    longest = max([len(title), len(rule)] +
                  [keyw + 2 + len(v) for _, v in ROWS])
    width = round(PAD * 2 + longest * CW)
    # title + rule + rows + swatch strip
    top = PAD + FS
    rows_top = top + ROW_H * 1.6
    height = round(rows_top + len(ROWS) * ROW_H + ROW_H * 0.9 + PAD)
    return keyw, title, rule, width, height, top, rows_top


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def write_svg():
    keyw, title, rule, W, H, top, rows_top = layout()
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" font-family="{FONT}">',
        '<style>'
        f':root{{--key:{KEY_COL};--val:{VAL_COL};--dim:{DIM_COL};--brd:{BORDER}}}'
        '@media (prefers-color-scheme:light){:root{'
        '--key:#1f2328;--val:#59636e;--dim:#818b98;--brd:#d0d7de}}'
        f'text{{font-size:{FS}px;white-space:pre;dominant-baseline:middle}}'
        '.k{fill:var(--key);font-weight:bold}.v{fill:var(--val)}.d{fill:var(--dim)}'
        '.brd{fill:none;stroke:var(--brd);stroke-width:1.5}'
        '</style>',
        # panel
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" class="brd"/>',
    ]
    x = PAD
    # title: user (bright) @host (dim)
    o.append(
        f'<text x="{x}" y="{top}" opacity="0">'
        f'<tspan class="k">{USER}</tspan>'
        f'<tspan class="d">@{HOST}</tspan>'
        f'<animate attributeName="opacity" from="0" to="1" begin="0.15s" '
        f'dur="{ROW_DUR}s" fill="freeze"/></text>'
    )
    o.append(
        f'<text x="{x}" y="{round(top+ROW_H*0.7)}" class="d" opacity="0">'
        f'{rule}<animate attributeName="opacity" from="0" to="1" begin="0.28s" '
        f'dur="{ROW_DUR}s" fill="freeze"/></text>'
    )
    for i, (k, v) in enumerate(ROWS):
        y = round(rows_top + i * ROW_H)
        begin = round(0.4 + i * STAGGER, 3)
        pad_k = k.ljust(keyw)
        o.append(
            f'<text x="{x}" y="{y}" opacity="0">'
            f'<tspan class="k" xml:space="preserve">{esc(pad_k)}</tspan>'
            f'<tspan class="d"> : </tspan>'
            f'<tspan class="v">{esc(v)}</tspan>'
            f'<animate attributeName="opacity" from="0" to="1" begin="{begin}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></text>'
        )
    # neofetch-style swatch strip (monochrome grays)
    sy = round(rows_top + len(ROWS) * ROW_H + ROW_H * 0.15)
    sw = 26
    grays = ["#2d333b", "#484f58", "#636c76", "#8b949e", "#b1bac4",
             "#c9d1d9", "#e6edf3", "#f0f3f6"]
    sbegin = round(0.4 + len(ROWS) * STAGGER + 0.1, 3)
    for j, g in enumerate(grays):
        o.append(
            f'<rect x="{x + j*(sw+6)}" y="{sy}" width="{sw}" height="14" rx="3" '
            f'fill="{g}" opacity="0"><animate attributeName="opacity" from="0" '
            f'to="1" begin="{round(sbegin + j*0.05,3)}s" dur="0.4s" '
            f'fill="freeze"/></rect>'
        )
    o.append("</svg>")
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write("".join(o))
    return W, H


def write_preview():
    keyw, title, rule, W, H, top, rows_top = layout()
    s = 2
    img = Image.new("RGB", (W * s, H * s), BG)
    d = ImageDraw.Draw(img)
    font = fontb = None
    for p in (r"C:\Windows\Fonts\consola.ttf",):
        try:
            font = ImageFont.truetype(p, FS * s)
        except OSError:
            pass
    for p in (r"C:\Windows\Fonts\consolab.ttf",):
        try:
            fontb = ImageFont.truetype(p, FS * s)
        except OSError:
            pass
    font = font or ImageFont.load_default()
    fontb = fontb or font

    d.rounded_rectangle([2, 2, W*s-2, H*s-2], radius=14*s, outline=BORDER, width=3)
    d.text((PAD*s, (top-FS)*s), USER, font=fontb, fill=KEY_COL)
    d.text(((PAD+len(USER)*CW)*s, (top-FS)*s), f"@{HOST}", font=font, fill=DIM_COL)
    d.text((PAD*s, round((top+ROW_H*0.7-FS)*s)), rule, font=font, fill=DIM_COL)
    for i, (k, v) in enumerate(ROWS):
        y = round((rows_top + i*ROW_H - FS*0.9) * s)
        d.text((PAD*s, y), k.ljust(keyw), font=fontb, fill=KEY_COL)
        d.text(((PAD+(keyw)*CW)*s, y), " : ", font=font, fill=DIM_COL)
        d.text(((PAD+(keyw+3)*CW)*s, y), v, font=font, fill=VAL_COL)
    sy = round((rows_top + len(ROWS)*ROW_H + ROW_H*0.15) * s)
    grays = ["#2d333b", "#484f58", "#636c76", "#8b949e", "#b1bac4",
             "#c9d1d9", "#e6edf3", "#f0f3f6"]
    for j, g in enumerate(grays):
        gx = (PAD + j*32) * s
        d.rounded_rectangle([gx, sy, gx+26*s, sy+14*s], radius=3*s, fill=g)
    img.save(OUT_PNG)


def main():
    W, H = write_svg()
    write_preview()
    print(f"{OUT_SVG}  {W}x{H}  ({len(ROWS)} rows)")
    print(f"{OUT_PNG}  preview written")


if __name__ == "__main__":
    main()
