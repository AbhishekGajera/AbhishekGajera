"""Prep a portrait photo for ASCII conversion.

Removes the background, crops to head and shoulders, boosts local contrast
with CLAHE and composites onto pure white. Also saves the subject mask so the
ASCII step can blank the background exactly. Run once per photo:

    python scripts/prep_photo.py assets/source-photo.jpg
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "source-prepped.png"
MASK_OUT = ROOT / "assets" / "source-mask.png"

# Fraction of the subject's height kept, measured from the top of the head.
BUST_FRACTION = 0.34


def main(src: str) -> None:
    photo = Image.open(src).convert("RGB")
    cutout = remove(photo)  # RGBA, background alpha = 0
    alpha = np.array(cutout)[:, :, 3]

    ys, xs = np.where(alpha > 32)
    top, bottom = ys.min(), ys.max()
    crop_bottom = top + int((bottom - top) * BUST_FRACTION)
    rows = alpha[top:crop_bottom] > 32
    cols = np.where(rows.any(axis=0))[0]
    left, right = cols.min(), cols.max()
    pad = int((right - left) * 0.04)
    box = (max(left - pad, 0), max(top - pad, 0), min(right + pad, photo.width), crop_bottom)
    cutout = cutout.crop(box)

    rgba = np.array(cutout)
    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    a = rgba[:, :, 3].astype(np.float32) / 255.0
    composite = gray.astype(np.float32) * a + 255.0 * (1.0 - a)
    Image.fromarray(composite.clip(0, 255).astype(np.uint8), "L").save(OUT)
    Image.fromarray(rgba[:, :, 3], "L").save(MASK_OUT)
    print(f"wrote {OUT.relative_to(ROOT)} ({cutout.width}x{cutout.height})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: prep_photo.py <photo>")
    main(sys.argv[1])
