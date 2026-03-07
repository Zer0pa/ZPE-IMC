from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from ..core.constants import DEFAULT_VERSION, Mode

# Legacy command mapping from Four Pillars
CMD_TL = 0
CMD_TR = 1
CMD_BL = 2
CMD_BR = 3
CMD_PAINT = 4
CMD_SET_COLOR = 5
CMD_BACKTRACK = 6
CMD_NOP = 7

# Legacy family marker inside payload (bits 11..10 == 0b10)
IMAGE_FAMILY_MASK = 0x0C00
IMAGE_FAMILY_VALUE = 0x0800

# Bit 9 determines color vs command payload
COLOR_FLAG = 0x0200

MAX_RUN = 63  # 6-bit run for command payloads


@dataclass(frozen=True)
class LegacyMeta:
    height: int
    width: int
    root: int


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | (payload & 0xFFFF)


def _is_legacy_payload(payload: int) -> bool:
    return (payload & IMAGE_FAMILY_MASK) == IMAGE_FAMILY_VALUE


def _quant_rgb333(image: np.ndarray) -> np.ndarray:
    arr = image.astype(np.uint8)
    return (arr >> 5).astype(np.uint8)


def _dequant3(v: int) -> int:
    v &= 0x7
    return ((v << 5) | (v << 2) | (v >> 1)) & 0xFF


def _next_pow2(n: int) -> int:
    out = 1
    while out < n:
        out <<= 1
    return out


def _pad_pow2(image: np.ndarray) -> tuple[np.ndarray, LegacyMeta]:
    h, w, _ = image.shape
    root = _next_pow2(max(h, w))
    out = np.zeros((root, root, 3), dtype=np.uint8)
    out[:h, :w, :] = image
    return out, LegacyMeta(height=h, width=w, root=root)


def _color_word(rgb333: tuple[int, int, int]) -> int:
    r, g, b = [int(c) & 0x7 for c in rgb333]
    payload = IMAGE_FAMILY_VALUE | COLOR_FLAG | (r << 6) | (g << 3) | b
    return _ext_word(payload)


def _cmd_word(cmd: int, run: int = 1) -> int:
    cmd = int(cmd) & 0x7
    run = max(1, min(int(run), MAX_RUN))
    payload = IMAGE_FAMILY_VALUE | ((cmd & 0x7) << 6) | (run & 0x3F)
    return _ext_word(payload)


def encode_legacy(image: np.ndarray, threshold: float = 5.0) -> tuple[List[int], LegacyMeta]:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected image shape (H, W, 3)")

    q333 = _quant_rgb333(image)
    padded, meta = _pad_pow2(q333)
    # Threshold=5.0 is defined in the legacy docs on an 8-bit-like scale.
    # Keep stored colors in rgb333, but evaluate split variance on dequantized bytes.
    padded_u8 = np.zeros_like(padded, dtype=np.uint8)
    padded_u8[:, :, 0] = np.vectorize(_dequant3)(padded[:, :, 0])
    padded_u8[:, :, 1] = np.vectorize(_dequant3)(padded[:, :, 1])
    padded_u8[:, :, 2] = np.vectorize(_dequant3)(padded[:, :, 2])

    words: List[int] = []
    current_color = (-1, -1, -1)

    def region_var_u8(region_u8: np.ndarray) -> float:
        return float(np.var(region_u8.reshape(-1, 3), axis=0).mean())

    def emit_set_color(rgb333: tuple[int, int, int]) -> None:
        nonlocal current_color
        if rgb333 == current_color:
            return
        words.append(_cmd_word(CMD_SET_COLOR, 1))
        words.append(_color_word(rgb333))
        current_color = rgb333

    def emit_paint() -> None:
        words.append(_cmd_word(CMD_PAINT, 1))

    def encode_node(x: int, y: int, size: int) -> None:
        region = padded[y : y + size, x : x + size, :]
        region_u8 = padded_u8[y : y + size, x : x + size, :]
        v = region_var_u8(region_u8)
        if size == 1 or v <= threshold:
            mean_rgb = tuple(int(np.round(region[:, :, i].mean())) & 0x7 for i in range(3))
            emit_set_color(mean_rgb)
            emit_paint()
            return

        half = size // 2
        for cmd, nx, ny in (
            (CMD_TL, x, y),
            (CMD_TR, x + half, y),
            (CMD_BL, x, y + half),
            (CMD_BR, x + half, y + half),
        ):
            words.append(_cmd_word(cmd, 1))
            encode_node(nx, ny, half)
            words.append(_cmd_word(CMD_BACKTRACK, 1))

    encode_node(0, 0, meta.root)
    return words, meta


def decode_legacy(words: Sequence[int], *, shape: tuple[int, int]) -> np.ndarray:
    h, w = shape
    root = _next_pow2(max(h, w))
    canvas = np.zeros((root, root, 3), dtype=np.uint8)

    stack: List[tuple[int, int, int]] = [(0, 0, root)]
    current_color = (0, 0, 0)

    i = 0
    while i < len(words):
        wv = int(words[i])
        mode = (wv >> 18) & 0x3
        version = (wv >> 16) & 0x3
        payload = wv & 0xFFFF

        if mode != Mode.EXTENSION.value or version != DEFAULT_VERSION or not _is_legacy_payload(payload):
            i += 1
            continue

        if payload & COLOR_FLAG:
            # color payload
            r3 = (payload >> 6) & 0x7
            g3 = (payload >> 3) & 0x7
            b3 = payload & 0x7
            current_color = (_dequant3(r3), _dequant3(g3), _dequant3(b3))
            i += 1
            continue

        cmd = (payload >> 6) & 0x7
        run = payload & 0x3F
        run = max(1, run)

        for _ in range(run):
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
                # color is read from following payload word
                pass
            elif cmd == CMD_PAINT:
                x, y, size = stack[-1]
                canvas[y : y + size, x : x + size, :] = np.array(current_color, dtype=np.uint8)
            elif cmd == CMD_NOP:
                pass

        i += 1

    return canvas[:h, :w, :]


def psnr(a: np.ndarray, b: np.ndarray) -> float:
    x = a.astype(np.float64)
    y = b.astype(np.float64)
    mse = float(np.mean((x - y) ** 2))
    if mse == 0.0:
        return 99.0
    return float(10.0 * np.log10((255.0 ** 2) / mse))


def quantized_reference_legacy(image: np.ndarray) -> np.ndarray:
    q333 = _quant_rgb333(image)
    out = np.zeros_like(q333, dtype=np.uint8)
    out[:, :, 0] = np.vectorize(_dequant3)(q333[:, :, 0])
    out[:, :, 1] = np.vectorize(_dequant3)(q333[:, :, 1])
    out[:, :, 2] = np.vectorize(_dequant3)(q333[:, :, 2])
    return out
