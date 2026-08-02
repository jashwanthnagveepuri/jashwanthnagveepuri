#!/usr/bin/env python3
"""Generate info-card.svg - a neofetch-style terminal panel (490px wide).

Dark background, window title bar "jashwanthnagveepuri@github", then
colored key/value rows. Each row fades + slides in on a short stagger
(SMIL), plays once and freezes. STATIC=1 emits the frozen final frame.
"""
import os
from xml.sax.saxutils import escape

OUT = "info-card.svg"

WIDTH = 490
BG = "#0d1117"
BORDER = "#30363d"
TITLE_FG = "#8b949e"
KEY_FG = "#58a6ff"
VAL_FG = "#c9d1d9"
FONT = "ui-monospace, 'DejaVu Sans Mono', Menlo, Consolas, monospace"

TITLE = "jashwanthnagveepuri@github"
ROWS = [
    ("Role:", "Software Engineer · 5 YOE"),
    ("Now:", "Backend & Platform Engineering"),
    ("Prev:", "Claims processing systems @ insurance enterprise"),
    ("Stack:", "Java · Spring Boot · Python · AWS · Docker"),
    ("OSS:", "mcp-opsmate — MCP server for cloud ops"),
    ("Focus:", "GenAI tooling · RAG pipelines · CI/CD optimization"),
]

TITLE_BAR_H = 34
ROW_STEP = 27
FIRST_ROW_Y = TITLE_BAR_H + 34
PAD_BOTTOM = 20

FADE_DUR = 0.30
STAGGER = 0.18
FIRST_BEGIN = 0.15


def build_svg(static: bool) -> str:
    height = FIRST_ROW_Y + (len(ROWS) - 1) * ROW_STEP + PAD_BOTTOM
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="info card">',
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>',
        # window chrome dots
        '<circle cx="20" cy="17" r="5" fill="#ff5f57"/>',
        '<circle cx="38" cy="17" r="5" fill="#febc2e"/>',
        '<circle cx="56" cy="17" r="5" fill="#28c840"/>',
        f'<text x="{WIDTH // 2}" y="21" text-anchor="middle" font-family="{FONT}" '
        f'font-size="13" fill="{TITLE_FG}">{escape(TITLE)}</text>',
        f'<line x1="0" y1="{TITLE_BAR_H}" x2="{WIDTH}" y2="{TITLE_BAR_H}" stroke="{BORDER}"/>',
    ]

    for i, (key, val) in enumerate(ROWS):
        y = FIRST_ROW_Y + i * ROW_STEP
        begin = FIRST_BEGIN + i * STAGGER
        row = (
            f'<text x="20" y="{y}" font-family="{FONT}" font-size="14">'
            f'<tspan fill="{KEY_FG}">{escape(key)}</tspan>'
            f'<tspan fill="{VAL_FG}">  {escape(val)}</tspan></text>'
        )
        if static:
            parts.append(row)
        else:
            parts.append(
                f'<g opacity="0">{row}'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-10 0" to="0 0" begin="{begin:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>'
                f"</g>"
            )

    if not static:
        total = FIRST_BEGIN + (len(ROWS) - 1) * STAGGER + FADE_DUR
        parts.append(f"<!-- total duration ~{total:.2f}s, plays once, freezes -->")

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    svg = build_svg(static)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"{OUT} ({'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
