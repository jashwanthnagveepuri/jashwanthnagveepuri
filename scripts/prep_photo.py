#!/usr/bin/env python3
"""Prep the source photo for ASCII conversion.

Pipeline: open with PIL -> grayscale -> autocontrast (cutoff=1) ->
CLAHE via OpenCV (clipLimit=2.0, tileGridSize=(8,8)) -> composite onto
pure white -> save assets/source-prepped.png.

Idempotent and deterministic.

Usage: python scripts/prep_photo.py assets/source-photo.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

DEFAULT_SRC = "assets/source-photo.jpg"
OUT_PATH = Path("assets/source-prepped.png")


def prep(src_path: str) -> Path:
    img = Image.open(src_path).convert("L")
    img = ImageOps.autocontrast(img, cutoff=1)

    arr = np.asarray(img)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # Composite onto pure white.
    fg = Image.fromarray(arr, mode="L").convert("RGBA")
    white = Image.new("RGBA", fg.size, (255, 255, 255, 255))
    comp = Image.alpha_composite(white, fg).convert("RGB")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    comp.save(OUT_PATH)
    return OUT_PATH


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = prep(src)
    print(out)


if __name__ == "__main__":
    main()
