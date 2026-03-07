from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np


Direction = Tuple[int, int]


@dataclass
class StrokeStep:
    dx: int
    dy: int
    pen: bool  # True when pen is down drawing


def _quantize_polyline(polyline: Sequence[Tuple[float, float]], grid_size: int) -> List[Tuple[int, int]]:
    coords: List[Tuple[int, int]] = []
    for x, y in polyline:
        gx = max(0, min(grid_size - 1, int(round(x))))
        gy = max(0, min(grid_size - 1, int(round(y))))
        coords.append((gx, gy))
    deduped: List[Tuple[int, int]] = []
    for pt in coords:
        if not deduped or pt != deduped[-1]:
            deduped.append(pt)
    return deduped


def polylines_to_strokes(polylines: Iterable[Sequence[Tuple[float, float]]], *, grid_size: int = 64) -> List[StrokeStep]:
    """
    Map polylines to 8-direction stroke steps with pen-up markers between polylines.

    This preserves ordering per input list; no attempt is made to optimize tour length.
    """
    strokes: List[StrokeStep] = []
    for idx, polyline in enumerate(polylines):
        quantized = _quantize_polyline(polyline, grid_size)
        if len(quantized) < 2:
            continue
        if strokes:
            strokes.append(StrokeStep(0, 0, pen=False))  # pen-up separator
        prev_x, prev_y = quantized[0]
        strokes.append(StrokeStep(prev_x, prev_y, pen=False))  # move to start
        for x, y in quantized[1:]:
            dx = x - prev_x
            dy = y - prev_y
            strokes.append(StrokeStep(dx, dy, pen=True))
            prev_x, prev_y = x, y
    return strokes


def strokes_to_bitmap(strokes: Sequence[StrokeStep], *, canvas_size: int = 256, grid_size: int = 64) -> np.ndarray:
    """
    Render strokes to a binary raster for visualization/IoU metrics.
    """
    canvas = np.zeros((canvas_size, canvas_size), dtype=np.uint8)
    if not strokes:
        return canvas

    scale = (canvas_size - 1) / max(grid_size - 1, 1)

    def to_px(x: int, y: int) -> Tuple[int, int]:
        return int(round(x * scale)), int(round(y * scale))

    x = y = None
    for step in strokes:
        if step.pen is False and (step.dx != 0 or step.dy != 0):
            # absolute move to starting point
            x, y = step.dx, step.dy
            continue
        if x is None or y is None:
            continue
        if step.pen:
            nx, ny = x + step.dx, y + step.dy
            _draw_line(canvas, to_px(x, y), to_px(nx, ny))
            x, y = nx, ny
        else:
            # pen-up separator: keep current position
            continue
    return canvas


def _draw_line(canvas: np.ndarray, start: Tuple[int, int], end: Tuple[int, int]) -> None:
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= y0 < canvas.shape[0] and 0 <= x0 < canvas.shape[1]:
            canvas[y0, x0] = 1
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
