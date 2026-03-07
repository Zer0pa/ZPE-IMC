from __future__ import annotations

import warnings
from typing import List, Sequence, Tuple

import numpy as np


Polyline = List[Tuple[float, float]]


def skeletonize_binary(binary: np.ndarray) -> np.ndarray:
    """
    Morphological thinning to a 1px skeleton. If scikit-image is missing,
    returns the input binary mask unchanged.
    """
    try:
        from skimage.morphology import skeletonize  # type: ignore
    except Exception:  # pragma: no cover - dependency guard
        warnings.warn(
            "scikit-image not available; returning binary mask without skeletonization",
            RuntimeWarning,
        )
        return binary
    return skeletonize(binary > 0).astype(np.uint8)


def binary_to_polylines(binary: np.ndarray, *, use_contours: bool = True) -> List[Polyline]:
    """
    Convert a binary mask to a list of polylines suitable for stroke conversion.

    Priority order:
    1) If scikit-image is available and use_contours=True, use find_contours.
    2) Fallback: connected-component bounding box rectangles as coarse polylines.
    """
    if use_contours:
        try:
            from skimage import measure  # type: ignore

            contours = measure.find_contours(binary, level=0.5)
            polylines: List[Polyline] = []
            for contour in contours:
                polyline = [(float(y), float(x)) for x, y in contour]
                if len(polyline) >= 2:
                    polylines.append(polyline)
            if polylines:
                return polylines
        except Exception:  # pragma: no cover - dependency guard
            warnings.warn(
                "scikit-image not available for contours; using coarse bounding boxes",
                RuntimeWarning,
            )

    # Fallback: find connected components and return box outlines as polylines
    return _bounding_box_polylines(binary)


def _bounding_box_polylines(binary: np.ndarray) -> List[Polyline]:
    visited = np.zeros_like(binary, dtype=bool)
    polylines: List[Polyline] = []
    h, w = binary.shape

    def neighbors(x: int, y: int):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < h and 0 <= ny < w:
                yield nx, ny

    for x in range(h):
        for y in range(w):
            if binary[x, y] == 0 or visited[x, y]:
                continue
            stack = [(x, y)]
            visited[x, y] = True
            xs: List[int] = []
            ys: List[int] = []
            while stack:
                cx, cy = stack.pop()
                xs.append(cx)
                ys.append(cy)
                for nx, ny in neighbors(cx, cy):
                    if binary[nx, ny] and not visited[nx, ny]:
                        visited[nx, ny] = True
                        stack.append((nx, ny))
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            polyline: Polyline = [
                (float(min_y), float(min_x)),
                (float(max_y), float(min_x)),
                (float(max_y), float(max_x)),
                (float(min_y), float(max_x)),
                (float(min_y), float(min_x)),
            ]
            polylines.append(polyline)
    return polylines
