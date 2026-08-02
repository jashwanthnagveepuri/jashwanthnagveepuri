#!/usr/bin/env python3
"""Render assets/source-prepped.png as an animated ASCII-art SVG.

Writes avi-ascii.svg (370px wide, dark terminal style). Each row wipes in
left->right via an animated SMIL clip-path, staggered top->bottom, with a
small block cursor riding the wipe edge. Plays once, then freezes (no loop).

STATIC=1 env var: emit the final frozen frame with no animation.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

SRC = Path("assets/source-prepped.png")
OUT = Path("avi-ascii.svg")

RAMP = " .`:-=+*cs#%@"          # bright -> sparse (space), dark -> dense
COLS = 100                     # character columns
CHAR_ASPECT = 1.9              # char height / char width in monospace
WIDTH = 370                    # svg width in px (pairs with 490px info card)
ROW_H = 7                      # px per row
FONT_SIZE = 7
FG = "#c9d1d9"                 # single light-gray fill
BG = "#0d1117"                 # dark background
CURSOR = "#39d353"             # block cursor color
FONT = "ui-monospace, 'DejaVu Sans Mono', Menlo, Consolas, monospace"

WIPE_DUR = 1.2                 # seconds per row wipe
STAGGER = 0.04                 # seconds between row starts


def char_grid() -> list[str]:
    img = Image.open(SRC).convert("L")
    w, h = img.size
    rows = int(round(COLS * (h / w) / CHAR_ASPECT))
    small = img.resize((COLS, rows), Image.LANCZOS)
    arr = np.asarray(small, dtype=np.float64) / 255.0
    n = len(RAMP) - 1
    lines = []
    for row in arr:
        lines.append("".join(RAMP[min(n, int((1.0 - v) * n))] for v in row))
    return lines


def build_svg(static: bool) -> str:
    lines = char_grid()
    rows = len(lines)
    height = rows * ROW_H
    last_end = (rows - 1) * STAGGER + WIPE_DUR

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="ASCII art avatar">',
        f'<rect width="{WIDTH}" height="{height}" fill="{BG}"/>',
    ]

    if not static:
        parts.append("<defs>")
        for i in range(rows):
            begin = i * STAGGER
            parts.append(
                f'<clipPath id="wipe{i}">'
                f'<rect x="0" y="{i * ROW_H}" width="0" height="{ROW_H}">'
                f'<animate attributeName="width" from="0" to="{WIDTH}" '
                f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze"/>'
                f"</rect></clipPath>"
            )
        parts.append("</defs>")

    for i, line in enumerate(lines):
        y = i * ROW_H + ROW_H - 1
        clip = "" if static else f' clip-path="url(#wipe{i})"'
        parts.append(
            f'<text x="0" y="{y}" font-family="{FONT}" font-size="{FONT_SIZE}" '
            f'fill="{FG}" textLength="{WIDTH}" lengthAdjust="spacingAndGlyphs"'
            f"{clip}>{escape(line)}</text>"
        )

    if not static:
        for i in range(rows):
            begin = i * STAGGER
            end = begin + WIPE_DUR
            parts.append(
                f'<rect x="0" y="{i * ROW_H}" width="{ROW_H}" height="{ROW_H}" fill="{CURSOR}">'
                f'<animate attributeName="x" from="0" to="{WIDTH}" '
                f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze"/>'
                f'<animate attributeName="opacity" from="1" to="0" '
                f'begin="{end:.3f}s" dur="0.15s" fill="freeze"/>'
                f"</rect>"
            )
        parts.append(
            f"<!-- total duration ~{last_end + 0.15:.2f}s, plays once, freezes -->"
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    if not SRC.exists():
        raise SystemExit(f"{SRC} not found - run scripts/prep_photo.py first")
    svg = build_svg(static)
    OUT.write_text(svg, encoding="utf-8")
    print(f"{OUT} ({'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
