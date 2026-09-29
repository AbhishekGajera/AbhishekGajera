"""Render the neofetch-style info card SVG. Edit CARD below to change it.

Lines fade and slide in one after another, then freeze.

    python scripts/make_info_card.py            # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py   # frozen frame, for previews
"""

import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

USER = "abhishek"
HOST = "github"
SINCE = 2021

CARD = [
    ("Role", "Full-stack JavaScript Developer"),
    ("Uptime", f"{date.today().year - SINCE}+ years shipping on GitHub"),
    ("Languages", "TypeScript · JavaScript · Dart"),
    ("Frontend", "React · Next.js · Electron · Flutter"),
    ("Backend", "Node.js · Express · REST APIs"),
    ("Data", "PostgreSQL · MongoDB · MySQL"),
    ("Cloud", "AWS · GitHub Actions · Codemagic"),
    ("Built", "e-commerce, inventory, real-time chat,"),
    ("", "AI workspaces, mobile apps"),
]

WIDTH = 490
BAR_H = 26
PAD = 22
LINE_H = 20
KEY_W = 92

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
KEY = "#39d353"
USER_C = "#58a6ff"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SWATCHES = ["#ff7b72", "#ffa657", "#d29922", "#3fb950", "#39c5cf", "#58a6ff", "#bc8cff", "#c9d1d9"]

LINE_DELAY = 0.14
START = 0.4


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build(static: bool) -> str:
    rows = 2 + len(CARD) + 2  # title, rule, card lines, gap, swatches
    height = BAR_H + PAD + rows * LINE_H + PAD - 4
    x = PAD

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" '
        f'height="{height}" role="img" aria-label="About Abhishek Gajera">',
        "<style>",
        f"text{{font-family:{FONT};font-size:12.5px}}",
    ]
    if not static:
        out.append(
            "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
            ".l{opacity:0;animation:in .45s cubic-bezier(.2,.8,.3,1) both}"
        )
    out.append("</style>")

    out += [
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M8.5 0.5h{WIDTH - 17}a8 8 0 0 1 8 8V{BAR_H}H0.5V8.5a8 8 0 0 1 8-8z" fill="{BAR}"/>',
        f'<line x1="0.5" y1="{BAR_H}" x2="{WIDTH - 0.5}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{color}"/>')
    out.append(
        f'<text x="{WIDTH / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" fill="{MUTED}" '
        f'style="font-size:11px">neofetch</text>'
    )

    line = 0

    def row(content: str, baseline: int = 12) -> None:
        nonlocal line
        y = BAR_H + PAD + line * LINE_H + baseline
        attr = "" if static else f' class="l" style="animation-delay:{START + line * LINE_DELAY:.2f}s"'
        out.append(f'<g{attr}>{content.format(y=y)}</g>')
        line += 1

    title = f"{USER}@{HOST}"
    row(
        f'<text x="{x}" y="{{y}}" font-weight="700"><tspan fill="{USER_C}">{USER}</tspan>'
        f'<tspan fill="{FG}">@</tspan><tspan fill="{USER_C}">{HOST}</tspan></text>'
    )
    row(f'<text x="{x}" y="{{y}}" fill="{MUTED}">{"-" * len(title)}</text>')
    for key, value in CARD:
        label = f'<tspan fill="{KEY}" font-weight="700">{esc(key)}</tspan>' if key else ""
        colon = f'<tspan fill="{MUTED}">:</tspan>' if key else ""
        row(
            f'<text x="{x}" y="{{y}}">{label}{colon}</text>'
            f'<text x="{x + KEY_W}" y="{{y}}" fill="{FG}">{esc(value)}</text>'
        )
    line += 1
    blocks = "".join(
        f'<rect x="{x + i * 24}" y="{{y}}" width="22" height="12" rx="2" fill="{c}"/>' for i, c in enumerate(SWATCHES)
    )
    row(blocks, baseline=1)

    # Blinking prompt cursor after the last line.
    if not static:
        done = START + line * LINE_DELAY + 0.3
        cy = BAR_H + PAD + (line - 1) * LINE_H + 1
        out.append(
            f'<rect x="{x + len(SWATCHES) * 24 + 8}" y="{cy}" width="8" height="13" fill="{KEY}" opacity="0">'
            f'<animate attributeName="opacity" values="0.9;0.9;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
            f'begin="{done:.2f}s" repeatCount="indefinite"/></rect>'
        )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    OUT.write_text(build(static=os.environ.get("STATIC") == "1") + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
