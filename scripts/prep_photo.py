#!/usr/bin/env python3
"""Prep the source photo for ASCII conversion.

Pipeline: open with PIL -> rembg background removal (STEP 1, isolates the
subject; RGBA with transparent background) -> grayscale -> autocontrast
(cutoff=1) -> CLAHE via OpenCV (clipLimit=2.0, tileGridSize=(8,8)) ->
composite onto pure white (transparent background maps to white, i.e. the
space glyph) -> save assets/source-prepped.png.

If rembg is unavailable (import error or model download failure), log a
warning and proceed without background removal.

Idempotent and deterministic (given the same u2net model).

Usage: python scripts/prep_photo.py assets/source-photo.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

DEFAULT_SRC = "assets/source-photo.jpg"
OUT_PATH = Path("assets/source-prepped.png")


def remove_background(img: Image.Image) -> Image.Image:
    """STEP 1: isolate the subject with rembg (RGBA, transparent bg).

    Falls back to the original image if rembg cannot run (import error,
    model download failure, etc.).
    """
    try:
        from rembg import remove
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"warning: rembg unavailable ({exc}); proceeding without "
              f"background removal", file=sys.stderr)
        return img.convert("RGBA")
    try:
        return remove(img.convert("RGB"))
    except Exception as exc:  # e.g. u2net model download failure
        print(f"warning: rembg background removal failed ({exc}); "
              f"proceeding without background removal", file=sys.stderr)
        return img.convert("RGBA")


def prep(src_path: str) -> Path:
    img = Image.open(src_path)
    rgba = remove_background(img)

    # Grayscale the subject, keeping the alpha mask from rembg.
    gray = rgba.convert("L")
    gray = ImageOps.autocontrast(gray, cutoff=1)

    arr = np.asarray(gray)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    arr = clahe.apply(arr)

    # Composite onto pure white: transparent background becomes white,
    # which maps to the space glyph in the ASCII ramp.
    fg = Image.fromarray(arr, mode="L").convert("RGBA")
    fg.putalpha(rgba.getchannel("A"))
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
