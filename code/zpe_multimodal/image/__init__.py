"""
Research-only utilities for converting raster images to stroke sequences.

This module is isolated from the core codec; it should not be imported by
`packetgram/codec.py` or any production path. Dependencies are optional and
should degrade gracefully (scikit-image/OpenCV preferred but not required).
"""

from .preprocess import load_and_binarize
from .vectorize import binary_to_polylines, skeletonize_binary
from .strokes import polylines_to_strokes, strokes_to_bitmap

__all__ = [
    "load_and_binarize",
    "binary_to_polylines",
    "skeletonize_binary",
    "polylines_to_strokes",
    "strokes_to_bitmap",
]
