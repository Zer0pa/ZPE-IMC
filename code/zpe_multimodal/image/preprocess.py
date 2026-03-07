from __future__ import annotations

import warnings
from pathlib import Path
from typing import Tuple

import numpy as np


def _lazy_import_pil():
    try:
        from PIL import Image  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ImportError(
            "Pillow is required for image research loading. "
            "Install via `pip install pillow`."
        ) from exc
    return Image


def load_and_binarize(
    image_path: str | Path,
    *,
    canvas_size: int = 256,
    threshold: float | None = None,
) -> np.ndarray:
    """
    Load an image, convert to grayscale, resize, and binarize to {0,1}.

    Parameters
    ----------
    image_path : str | Path
        Input image path (PNG/SVG rasterized/bitmap).
    canvas_size : int
        Square canvas size to resize to (pixels).
    threshold : float | None
        Manual threshold in [0, 255]. If None, use Otsu if available, else 128.

    Returns
    -------
    np.ndarray
        Binary image of shape (canvas_size, canvas_size) with values {0,1}.
    """
    image_path = Path(image_path)
    Image = _lazy_import_pil()
    img = Image.open(image_path).convert("L")
    if canvas_size:
        img = img.resize((canvas_size, canvas_size))
    arr = np.array(img, dtype=np.uint8)

    if threshold is None:
        try:
            from skimage.filters import threshold_otsu  # type: ignore

            threshold = float(threshold_otsu(arr))
        except Exception:
            threshold = 128.0
            warnings.warn(
                "Falling back to fixed threshold=128; install scikit-image for Otsu.",
                RuntimeWarning,
            )

    binary = (arr < threshold).astype(np.uint8)
    return binary
