"""Convert the prepped portrait into a self-typing monochrome ASCII SVG.

Each row is revealed by a left-to-right clip wipe with a block cursor riding
the edge, staggered top to bottom. It plays once and freezes.

    python scripts/make_ascii_svg.py            # writes ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previews
"""

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source-prepped.png"
MASK = ROOT / "assets" / "source-mask.png"
OUT = ROOT / "ascii.svg"

COLS = 120
# Monospace glyphs are roughly twice as tall as they are wide.
CHAR_ASPECT = 0.5
# Light text on a dark panel: bright pixels get the dense glyphs.
RAMP = " .'`:-=+*cs#%@"

FONT_SIZE = 6.4
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE * 1.08
PAD = 18
BAR_H = 26

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
CURSOR = "#39d353"

ROW_DELAY = 0.045  # seconds between rows starting
ROW_DUR = 0.28  # seconds for one row to wipe across
START = 0.3


def to_grid() -> list[str]:
    img = Image.open(SRC).convert("L")
    mask = Image.open(MASK).convert("L")
    rows = round(COLS * img.height / img.width * CHAR_ASPECT)
    img = img.resize((COLS, rows), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 80, 2))
    mask = mask.resize((COLS, rows), Image.LANCZOS)

    lum = np.asarray(img, dtype=np.float32)
    alpha = np.asarray(mask, dtype=np.float32) / 255.0
    # Equalize over subject pixels only so the face spans the whole ramp.
    subject = lum[alpha >= 0.35]
    ranks = np.searchsorted(np.sort(subject), lum) / max(len(subject), 1)
    lum = np.clip(ranks, 0, 1) ** 1.15
    # Keep the darkest subject areas (hair, beard) faintly visible.
    level = np.clip(0.12 + lum * 0.88, 0, 1) * alpha
    idx = np.rint(level * (len(RAMP) - 1)).astype(int)
    idx[alpha < 0.35] = 0

    lines = ["".join(RAMP[i] for i in row) for row in idx]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def esc(text: str) -> str:
    # Non-breaking spaces: renderers collapse ordinary leading spaces.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text.replace(" ", "\u00a0")


def build(lines: list[str], static: bool) -> str:
    text_w = COLS * CHAR_W
    width = text_w + PAD * 2
    height = BAR_H + PAD + len(lines) * LINE_H + PAD
    font = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" role="img" aria-label="ASCII portrait of Abhishek Gajera">',
        f'<rect x="0.5" y="0.5" width="{width - 1:.0f}" height="{height - 1:.0f}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M8.5 0.5h{width - 17:.0f}a8 8 0 0 1 8 8V{BAR_H}H0.5V8.5a8 8 0 0 1 8-8z" fill="{BAR}"/>',
        f'<line x1="0.5" y1="{BAR_H}" x2="{width - 0.5:.0f}" y2="{BAR_H}" stroke="{BORDER}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{color}"/>')
    out.append(
        f'<text x="{width / 2:.0f}" y="{BAR_H / 2 + 4}" text-anchor="middle" fill="{MUTED}" '
        f'font-family="{font}" font-size="11">~/portrait.txt</text>'
    )

    out.append("<defs>")
    for i in range(len(lines)):
        y = BAR_H + PAD + i * LINE_H
        begin = START + i * ROW_DELAY
        anim = (
            ""
            if static
            else f'<animate attributeName="width" from="0" to="{text_w + 2:.1f}" begin="{begin:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
        )
        w = f"{text_w + 2:.1f}" if static else "0"
        out.append(
            f'<clipPath id="r{i}"><rect x="{PAD - 1}" y="{y:.2f}" width="{w}" height="{LINE_H + 0.5:.2f}">{anim}</rect></clipPath>'
        )
    out.append("</defs>")

    out.append(
        f'<g fill="{FG}" font-family="{font}" font-size="{FONT_SIZE}">'
    )
    for i, line in enumerate(lines):
        y = BAR_H + PAD + i * LINE_H + FONT_SIZE * 0.82
        out.append(
            f'<text x="{PAD}" y="{y:.2f}" textLength="{text_w:.1f}" lengthAdjust="spacing" '
            f'clip-path="url(#r{i})">{esc(line)}</text>'
        )
    out.append("</g>")

    if not static:
        # Each row gets a cursor block that rides its wipe edge, then hides.
        for i in range(len(lines)):
            y = BAR_H + PAD + i * LINE_H
            begin = START + i * ROW_DELAY
            end = begin + ROW_DUR
            out.append(
                f'<rect y="{y:.2f}" width="{CHAR_W:.1f}" height="{LINE_H:.1f}" fill="{CURSOR}" opacity="0">'
                f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
                f'<animate attributeName="x" from="{PAD}" to="{PAD + text_w:.1f}" begin="{begin:.3f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0" begin="{end:.3f}s"/></rect>'
            )
        # A prompt cursor blinks under the portrait once it has printed.
        done = START + (len(lines) - 1) * ROW_DELAY + ROW_DUR
        y = BAR_H + PAD + len(lines) * LINE_H - LINE_H
        out.append(
            f'<rect x="{PAD + text_w + 3:.1f}" y="{y:.2f}" width="{CHAR_W:.1f}" height="{LINE_H:.1f}" '
            f'fill="{CURSOR}" opacity="0"><animate attributeName="opacity" values="0.9;0.9;0;0" '
            f'keyTimes="0;0.5;0.5;1" dur="1.1s" begin="{done:.3f}s" repeatCount="indefinite"/></rect>'
        )

    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    lines = to_grid()
    OUT.write_text(build(lines, static=os.environ.get("STATIC") == "1"))
    print(f"wrote {OUT.relative_to(ROOT)} ({COLS}x{len(lines)} chars)")


if __name__ == "__main__":
    main()
