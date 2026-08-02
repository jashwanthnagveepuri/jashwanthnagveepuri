#!/usr/bin/env python3
"""Render data/contributions.json as contrib-heatmap.svg.

53 weeks x 7 days grid of rounded rects, GitHub-green palette, with a
diagonal line-after-line slide-down reveal (CSS keyframes, plays once,
freezes via animation-fill-mode: forwards; no loop). Less->More legend
and a stats footer. Total width 860px.
"""
import json
from datetime import date, timedelta
from pathlib import Path

SRC = Path("data/contributions.json")
OUT = Path("contrib-heatmap.svg")

WIDTH = 860
CELL = 10
GAP = 3
STEP = CELL + GAP
COLS = 53
ROWS = 7
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
LEGEND_SWATCHES = [0, 1, 2, 3, 5]  # 5 swatches, Less -> More
TEXT = "#8b949e"
FONT = "ui-monospace, 'DejaVu Sans Mono', Menlo, Consolas, monospace"

GRID_W = COLS * STEP - GAP
GRID_H = ROWS * STEP - GAP
LEFT = (WIDTH - GRID_W) // 2
TOP = 20
FOOTER_Y = TOP + GRID_H + 26
HEIGHT = FOOTER_Y + 16

DELAY = 0.018   # seconds per diagonal step
DUR = 0.45      # seconds per cell animation


def main() -> None:
    data = json.loads(SRC.read_text())
    days = data["days"]
    stats = data["stats"]
    if not days:
        raise SystemExit("no days in contributions.json")

    first = date.fromisoformat(days[0]["date"])
    # grid columns start on Sunday (GitHub convention)
    start = first - timedelta(days=(first.weekday() + 1) % 7)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="contribution heatmap">',
        "<style>",
        ".cell{opacity:0;transform:translateY(-8px);"
        "animation:drop " + f"{DUR}s" + " ease-out forwards;}",
        "@keyframes drop{to{opacity:1;transform:translateY(0);}}",
        "</style>",
    ]

    for d in days:
        cur = date.fromisoformat(d["date"])
        delta = (cur - start).days
        col, row = delta // 7, delta % 7
        if not (0 <= col < COLS):
            continue
        x = LEFT + col * STEP
        y = TOP + row * STEP
        fill = PALETTE[min(d["level"], len(PALETTE) - 1)]
        delay = (col + row) * DELAY  # diagonal, line after line
        parts.append(
            f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{fill}" style="animation-delay:{delay:.3f}s">'
            f'<title>{d["count"]} contributions on {d["date"]}</title></rect>'
        )

    # Less -> More legend (5 swatches)
    lx = LEFT
    ly = FOOTER_Y - CELL + 2
    parts.append(
        f'<text x="{lx}" y="{FOOTER_Y}" font-family="{FONT}" font-size="10" '
        f'fill="{TEXT}">Less</text>'
    )
    sx = lx + 30
    for i, lvl in enumerate(LEGEND_SWATCHES):
        parts.append(
            f'<rect x="{sx + i * (CELL + GAP)}" y="{ly}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{PALETTE[lvl]}"/>'
        )
    parts.append(
        f'<text x="{sx + 5 * (CELL + GAP) + 4}" y="{FOOTER_Y}" font-family="{FONT}" '
        f'font-size="10" fill="{TEXT}">More</text>'
    )

    # stats footer line (right aligned)
    footer = (f"{stats['total_last_year']} contributions in the last year · "
              f"longest streak {stats['longest_streak']} days")
    parts.append(
        f'<text x="{WIDTH - LEFT}" y="{FOOTER_Y}" text-anchor="end" '
        f'font-family="{FONT}" font-size="11" fill="{TEXT}">{footer}</text>'
    )

    parts.append("</svg>")
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(days)} cells")


if __name__ == "__main__":
    main()
