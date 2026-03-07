from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from ..core.constants import DEFAULT_VERSION, Mode
from ..diagram.pack import DIAGRAM_TYPE_BIT

# Direction-command reinterpretation for image quadtree
CMD_TL = 0
CMD_TR = 1
CMD_BL = 2
CMD_BR = 3
CMD_PAINT = 4
CMD_SET_COLOR = 5
CMD_BACKTRACK = 6
CMD_NOP = 7

# Payload subtypes
SUBTYPE_CMD = 0
SUBTYPE_DATA = 1

# DATA kinds for SUBTYPE_DATA
DATA_R = 0
DATA_G = 1
DATA_B = 2

MAX_RUN = 0x3FF


@dataclass(frozen=True)
class QuadMeta:
    height: int
    width: int
    root_size: int
    bit_depth: int


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | payload


def _cmd_word(cmd: int, count: int = 1) -> int:
    count = max(1, min(int(count), MAX_RUN))
    payload = DIAGRAM_TYPE_BIT | (SUBTYPE_CMD << 13) | ((cmd & 0x7) << 10) | (count & 0x3FF)
    return _ext_word(payload)


def _data_word(kind: int, value: int) -> int:
    payload = DIAGRAM_TYPE_BIT | (SUBTYPE_DATA << 13) | ((kind & 0x7) << 10) | (int(value) & 0x3FF)
    return _ext_word(payload)


def _next_pow2(n: int) -> int:
    n = max(1, int(n))
    out = 1
    while out < n:
        out <<= 1
    return out


def quantize_rgb(image: np.ndarray, bit_depth: int = 3) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected image shape (H, W, 3)")
    if not (1 <= bit_depth <= 8):
        raise ValueError("bit_depth must be in [1, 8]")
    shift = 8 - bit_depth
    arr = image.astype(np.uint8)
    if shift == 0:
        return arr.copy()
    return ((arr >> shift) << shift).astype(np.uint8)


def _pad_pow2_square(image: np.ndarray) -> tuple[np.ndarray, QuadMeta]:
    h, w, _ = image.shape
    root = _next_pow2(max(h, w))
    out = np.zeros((root, root, 3), dtype=np.uint8)
    out[:h, :w, :] = image
    return out, QuadMeta(height=h, width=w, root_size=root, bit_depth=3)


def quadtree_encode(image: np.ndarray, threshold: float = 5.0, bit_depth: int = 3) -> List[int]:
    """
    Encode image into extension words using quadtree recursion.

    Notes:
    - Returns words only; decode requires output shape at call site.
    - PSNR comparisons must be against quantized reference.
    """
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected image shape (H, W, 3)")

    q = quantize_rgb(image, bit_depth=bit_depth)
    padded, meta = _pad_pow2_square(q)

    words: List[int] = []
    current_color = (-1, -1, -1)

    def emit_set_color(rgb: tuple[int, int, int]) -> None:
        nonlocal current_color
        if rgb == current_color:
            return
        words.append(_cmd_word(CMD_SET_COLOR, 1))
        words.append(_data_word(DATA_R, rgb[0]))
        words.append(_data_word(DATA_G, rgb[1]))
        words.append(_data_word(DATA_B, rgb[2]))
        current_color = rgb

    def emit_paint() -> None:
        words.append(_cmd_word(CMD_PAINT, 1))

    def variance_of_region(region: np.ndarray) -> float:
        # Mean channel variance across RGB
        return float(np.var(region.reshape(-1, 3), axis=0).mean())

    def encode_node(x: int, y: int, size: int) -> None:
        region = padded[y : y + size, x : x + size, :]
        var = variance_of_region(region)

        if size == 1 or var <= threshold:
            mean_rgb = tuple(int(np.round(region[:, :, i].mean())) for i in range(3))
            mean_rgb_q = tuple(int(((c >> (8 - bit_depth)) << (8 - bit_depth)) if bit_depth < 8 else c) for c in mean_rgb)
            emit_set_color(mean_rgb_q)
            emit_paint()
            return

        half = size // 2
        children = [
            (CMD_TL, x, y),
            (CMD_TR, x + half, y),
            (CMD_BL, x, y + half),
            (CMD_BR, x + half, y + half),
        ]

        for cmd, cx, cy in children:
            words.append(_cmd_word(cmd, 1))
            encode_node(cx, cy, half)
            words.append(_cmd_word(CMD_BACKTRACK, 1))

    encode_node(0, 0, meta.root_size)
    return words


def _parse_words(words: Iterable[int]) -> List[tuple[str, int, int]]:
    out: List[tuple[str, int, int]] = []
    for w in words:
        if not isinstance(w, int):
            continue
        mode = (w >> 18) & 0x3
        version = (w >> 16) & 0x3
        payload = w & 0xFFFF

        if mode != Mode.EXTENSION.value:
            continue
        if version != DEFAULT_VERSION:
            continue
        if not (payload & DIAGRAM_TYPE_BIT):
            continue

        subtype = (payload >> 13) & 0x3
        if subtype == SUBTYPE_CMD:
            cmd = (payload >> 10) & 0x7
            count = payload & 0x3FF
            out.append(("cmd", cmd, max(1, count)))
        elif subtype == SUBTYPE_DATA:
            kind = (payload >> 10) & 0x7
            value = payload & 0x3FF
            out.append(("data", kind, value))

    return out


def quadtree_decode(
    words: Sequence[int],
    *,
    shape: tuple[int, int],
    bit_depth: int = 3,
) -> np.ndarray:
    """
    Decode quadtree extension words into a quantized RGB image.

    `shape` is required because dimensions are not embedded in this payload profile.
    """
    h, w = shape
    root = _next_pow2(max(h, w))
    canvas = np.zeros((root, root, 3), dtype=np.uint8)

    parsed = _parse_words(words)

    stack: List[tuple[int, int, int]] = [(0, 0, root)]
    current_color = (0, 0, 0)

    i = 0
    while i < len(parsed):
        kind, a, b = parsed[i]

        if kind != "cmd":
            i += 1
            continue

        cmd = a
        count = b

        for _ in range(count):
            if cmd in (CMD_TL, CMD_TR, CMD_BL, CMD_BR):
                x, y, size = stack[-1]
                half = max(1, size // 2)
                if cmd == CMD_TL:
                    stack.append((x, y, half))
                elif cmd == CMD_TR:
                    stack.append((x + half, y, half))
                elif cmd == CMD_BL:
                    stack.append((x, y + half, half))
                else:
                    stack.append((x + half, y + half, half))

            elif cmd == CMD_BACKTRACK:
                if len(stack) > 1:
                    stack.pop()

            elif cmd == CMD_SET_COLOR:
                channels = {}
                j = i + 1
                while j < len(parsed) and parsed[j][0] == "data" and len(channels) < 3:
                    _, data_kind, value = parsed[j]
                    if data_kind in (DATA_R, DATA_G, DATA_B):
                        channels[data_kind] = int(value & 0xFF)
                    j += 1
                if len(channels) == 3:
                    current_color = (channels[DATA_R], channels[DATA_G], channels[DATA_B])
                    i = j - 1

            elif cmd == CMD_PAINT:
                x, y, size = stack[-1]
                canvas[y : y + size, x : x + size, :] = current_color

            elif cmd == CMD_NOP:
                pass

        i += 1

    return canvas[:h, :w, :]


def psnr(reference: np.ndarray, candidate: np.ndarray) -> float:
    ref = reference.astype(np.float64)
    rec = candidate.astype(np.float64)
    mse = float(np.mean((ref - rec) ** 2))
    if mse == 0.0:
        return 99.0
    return float(10.0 * np.log10((255.0 ** 2) / mse))
