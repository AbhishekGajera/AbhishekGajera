"""Render data/contributions.json as an animated contribution heatmap SVG.

Cells slide in along diagonals once on load, then freeze.

    python scripts/render_heatmap_svg.py            # writes contrib-heatmap.svg
    STATIC=1 python scripts/render_heatmap_svg.py   # frozen frame, for previews
"""

import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
BAR_H = 26
LEFT = 30  # weekday labels
TOP = 20  # month labels
FOOT = 44

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
ACCENT = "#39d353"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

DIAG_DELAY = 0.035
CELL_DUR = 0.45
START = 0.2


def layout(days: list[dict]) -> list[tuple[int, int, dict]]:
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7  # Sunday-first rows, like GitHub
    cells = []
    for i, d in enumerate(days):
        slot = i + offset
        cells.append((slot // 7, slot % 7, d))
    return cells


def build(data: dict, static: bool) -> str:
    cells = layout(data["days"])
    weeks = cells[-1][0] + 1
    grid_w = weeks * STEP - GAP
    width = PAD + LEFT + grid_w + PAD
    grid_x = PAD + LEFT
    grid_y = BAR_H + PAD + TOP
    height = grid_y + 7 * STEP - GAP + FOOT + PAD / 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height:.0f}" width="{width}" '
        f'height="{height:.0f}" role="img" aria-label="{data["total"]:,} GitHub contributions in the last year">',
        "<style>",
        f"text{{font-family:{FONT}}}",
    ]
    if not static:
        out.append(
            "@keyframes drop{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:none}}"
            f".c{{opacity:0;transform-box:fill-box;animation:drop {CELL_DUR}s cubic-bezier(.2,.8,.3,1) both}}"
            "@keyframes fade{from{opacity:0}to{opacity:1}}"
            f".f{{opacity:0;animation:fade .6s ease-out both}}"
        )
        for k in range(weeks + 7):
            out.append(f".d{k}{{animation-delay:{START + k * DIAG_DELAY:.3f}s}}")
    out.append("</style>")

    out += [
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1:.0f}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M8.5 0.5h{width - 17}a8 8 0 0 1 8 8V{BAR_H}H0.5V8.5a8 8 0 0 1 8-8z" fill="{BAR}"/>',
        f'<line x1="0.5" y1="{BAR_H}" x2="{width - 0.5}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{color}"/>')
    out.append(
        f'<text x="{width / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" fill="{MUTED}" '
        f'font-size="11">contributions.sh — last 12 months</text>'
    )

    # Label each month where it starts; skip months shown for under 3 weeks.
    first_of_col: dict[int, str] = {}
    for col, _row, d in cells:
        first_of_col.setdefault(col, d["date"])
    months = [first_of_col[col][:7] for col in range(weeks)]
    for col in range(weeks):
        if (col == 0 or months[col] != months[col - 1]) and months[col : col + 3].count(months[col]) == 3:
            label = date.fromisoformat(first_of_col[col]).strftime("%b")
            out.append(f'<text x="{grid_x + col * STEP}" y="{grid_y - 8}" fill="{MUTED}" font-size="10">{label}</text>')
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text x="{PAD}" y="{grid_y + row * STEP + CELL - 2}" fill="{MUTED}" font-size="10">{label}</text>'
        )

    for col, row, d in cells:
        cls = "" if static else f' class="c d{col + row}"'
        tip = f'{d["count"]} contribution{"" if d["count"] == 1 else "s"} on {d["date"]}'
        out.append(
            f'<rect x="{grid_x + col * STEP}" y="{grid_y + row * STEP}" width="{CELL}" height="{CELL}" '
            f'rx="2.5" fill="{PALETTE[min(d["level"], 4)]}"{cls}><title>{tip}</title></rect>'
        )

    # Footer: stats on the left, Less -> More legend on the right.
    fy = grid_y + 7 * STEP - GAP + 28
    fade = "" if static else f' class="f" style="animation-delay:{START + (weeks + 6) * DIAG_DELAY:.2f}s"'
    best = date.fromisoformat(data["best_day"]["date"]).strftime("%b %-d")
    out.append(f"<g{fade}>")
    out.append(
        f'<text x="{grid_x}" y="{fy}" font-size="12" fill="{FG}">'
        f'<tspan fill="{ACCENT}" font-weight="700">{data["total"]:,}</tspan> contributions in the last year'
        f'<tspan fill="{MUTED}">  ·  </tspan>longest streak <tspan fill="{ACCENT}">{data["longest_streak"]}d</tspan>'
        f'<tspan fill="{MUTED}">  ·  </tspan>best day <tspan fill="{ACCENT}">{data["best_day"]["count"]}</tspan>'
        f'<tspan fill="{MUTED}"> ({best})</tspan></text>'
    )
    lx = grid_x + grid_w - (len(PALETTE) * (CELL + 3)) - 32
    out.append(f'<text x="{lx - 34}" y="{fy}" font-size="10" fill="{MUTED}">Less</text>')
    for i, color in enumerate(PALETTE):
        out.append(f'<rect x="{lx + i * (CELL + 3)}" y="{fy - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
    out.append(
        f'<text x="{lx + len(PALETTE) * (CELL + 3) + 4}" y="{fy}" font-size="10" fill="{MUTED}">More</text>'
    )
    out.append("</g>")

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    data = json.loads(SRC.read_text())
    OUT.write_text(build(data, static=os.environ.get("STATIC") == "1") + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
