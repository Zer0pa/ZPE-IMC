from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Sequence

import numpy as np

from ..core.constants import DEFAULT_VERSION, Mode

# Enhanced family marker (bits 11..10 == 0b01)
IMAGE_FAMILY_MASK = 0x0C00
IMAGE_FAMILY_VALUE = 0x0400
DATA_FLAG = 0x0200

CMD_TL = 0
CMD_TR = 1
CMD_BL = 2
CMD_BR = 3
CMD_PAINT = 4
CMD_SET_COLOR = 5
CMD_BACKTRACK = 6
CMD_META = 7

META_BEGIN = 0
META_END = 1

# Metadata data kinds (inside META_BEGIN .. META_END)
M_WIDTH_HI = 0
M_WIDTH_LO = 1
M_HEIGHT_HI = 2
M_HEIGHT_LO = 3
M_ROOT_HI = 4
M_ROOT_LO = 5
M_BIT_DEPTH = 6
M_THRESH_X10 = 7

# Color kinds (after SET_COLOR)
C_R = 0
C_G = 1
C_B = 2

MAX_RUN = 63


@dataclass(frozen=True)
class EnhancedMeta:
    width: int
    height: int
    root: int
    bit_depth: int
    threshold_x10: int


@lru_cache(maxsize=1)
def _native_quadtree_encoder():
    try:
        from ..core.imc_native import encode_quadtree_kernel
    except Exception:
        return None
    return encode_quadtree_kernel


@lru_cache(maxsize=1)
def _native_quadtree_decoder():
    try:
        from ..core.imc_native import decode_quadtree_kernel
    except Exception:
        return None
    return decode_quadtree_kernel


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | (payload & 0xFFFF)


def _cmd_word(cmd: int, arg: int = 1) -> int:
    arg = max(0, min(int(arg), MAX_RUN))
    payload = IMAGE_FAMILY_VALUE | ((int(cmd) & 0x7) << 6) | (arg & 0x3F)
    return _ext_word(payload)


def _data_word(kind: int, value: int) -> int:
    payload = IMAGE_FAMILY_VALUE | DATA_FLAG | ((int(kind) & 0x7) << 6) | (int(value) & 0x3F)
    return _ext_word(payload)


def _is_family(payload: int) -> bool:
    return (payload & IMAGE_FAMILY_MASK) == IMAGE_FAMILY_VALUE


def _next_pow2(n: int) -> int:
    out = 1
    while out < n:
        out <<= 1
    return out


def _quantize(image: np.ndarray, bit_depth: int) -> np.ndarray:
    arr = image.astype(np.uint8)
    maxq = (1 << bit_depth) - 1
    if maxq <= 0:
        return np.zeros_like(arr, dtype=np.uint8)
    levels = np.rint((arr.astype(np.float64) / 255.0) * maxq).astype(np.intp, copy=False)
    return _dequant_lut(bit_depth)[levels]


def _quant_level(value_u8: int, bit_depth: int) -> int:
    maxq = (1 << bit_depth) - 1
    return int(round((int(value_u8) / 255.0) * maxq))


@lru_cache(maxsize=6)
def _dequant_lut(bit_depth: int) -> np.ndarray:
    maxq = (1 << bit_depth) - 1
    if maxq <= 0:
        lut = np.zeros((1,), dtype=np.uint8)
    else:
        levels = np.arange(maxq + 1, dtype=np.float64)
        lut = np.rint((levels / maxq) * 255.0).astype(np.uint8)
    lut.setflags(write=False)
    return lut


def _dequant_level(level: int, bit_depth: int) -> int:
    lut = _dequant_lut(bit_depth)
    index = max(0, min(int(level), len(lut) - 1))
    return int(lut[index])


def _pack_u12(value: int) -> tuple[int, int]:
    v = max(0, min(int(value), 0xFFF))
    return ((v >> 6) & 0x3F, v & 0x3F)


def _unpack_u12(hi: int, lo: int) -> int:
    return ((int(hi) & 0x3F) << 6) | (int(lo) & 0x3F)


def encode_enhanced(image: np.ndarray, threshold: float = 5.0, bit_depth: int = 3) -> tuple[List[int], EnhancedMeta]:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("expected image shape (H, W, 3)")
    if not (1 <= bit_depth <= 6):
        raise ValueError("bit_depth supported range is [1,6]")

    native_encode = _native_quadtree_encoder()
    if native_encode is not None:
        words, meta_payload = native_encode(image, threshold=threshold, bit_depth=bit_depth)
        return words, EnhancedMeta(
            width=int(meta_payload["width"]),
            height=int(meta_payload["height"]),
            root=int(meta_payload["root"]),
            bit_depth=int(meta_payload["bit_depth"]),
            threshold_x10=int(meta_payload["threshold_x10"]),
        )

    h, w, _ = image.shape
    root = _next_pow2(max(h, w))

    q = _quantize(image, bit_depth)
    padded = np.zeros((root, root, 3), dtype=np.uint8)
    padded[:h, :w, :] = q

    t10 = int(round(float(threshold) * 10.0))
    meta = EnhancedMeta(width=w, height=h, root=root, bit_depth=bit_depth, threshold_x10=t10)

    words: List[int] = []

    # Header
    words.append(_cmd_word(CMD_META, META_BEGIN))
    w_hi, w_lo = _pack_u12(w)
    h_hi, h_lo = _pack_u12(h)
    r_hi, r_lo = _pack_u12(root)

    words.extend([
        _data_word(M_WIDTH_HI, w_hi),
        _data_word(M_WIDTH_LO, w_lo),
        _data_word(M_HEIGHT_HI, h_hi),
        _data_word(M_HEIGHT_LO, h_lo),
        _data_word(M_ROOT_HI, r_hi),
        _data_word(M_ROOT_LO, r_lo),
        _data_word(M_BIT_DEPTH, bit_depth),
        _data_word(M_THRESH_X10, t10),
    ])
    words.append(_cmd_word(CMD_META, META_END))

    current = (-1, -1, -1)

    def region_stats(region: np.ndarray) -> tuple[float, tuple[int, int, int]]:
        flat = region.reshape(-1, 3)
        count = float(flat.shape[0])
        mean_rgb = flat.sum(axis=0, dtype=np.float64) / count
        sumsq_rgb = np.square(flat, dtype=np.float64).sum(axis=0, dtype=np.float64)
        variance_rgb = (sumsq_rgb / count) - np.square(mean_rgb)
        rounded = np.rint(mean_rgb).astype(np.int32, copy=False)
        return float(variance_rgb.mean()), (int(rounded[0]), int(rounded[1]), int(rounded[2]))

    def emit_color(rgb: tuple[int, int, int]) -> None:
        nonlocal current
        levels = tuple(_quant_level(c, bit_depth) for c in rgb)
        if levels == current:
            return
        words.append(_cmd_word(CMD_SET_COLOR, 1))
        words.append(_data_word(C_R, levels[0]))
        words.append(_data_word(C_G, levels[1]))
        words.append(_data_word(C_B, levels[2]))
        current = levels

    def emit_paint() -> None:
        words.append(_cmd_word(CMD_PAINT, 1))

    def rec(x: int, y: int, size: int) -> None:
        region = padded[y : y + size, x : x + size, :]
        variance_value, mean_rgb = region_stats(region)
        if size == 1 or variance_value <= threshold:
            emit_color(mean_rgb)
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
            rec(nx, ny, half)
            words.append(_cmd_word(CMD_BACKTRACK, 1))

    rec(0, 0, root)
    return words, meta


def decode_enhanced_payloads(payloads: Sequence[int]) -> tuple[np.ndarray, EnhancedMeta]:
    meta_open = False
    meta_vals = {
        M_WIDTH_HI: 0,
        M_WIDTH_LO: 0,
        M_HEIGHT_HI: 0,
        M_HEIGHT_LO: 0,
        M_ROOT_HI: 0,
        M_ROOT_LO: 0,
        M_BIT_DEPTH: 3,
        M_THRESH_X10: 50,
    }

    commands: list[tuple[int, int]] = []
    color_data: list[tuple[int, int]] = []

    for payload in payloads:
        if not _is_family(int(payload)):
            continue
        payload = int(payload)

        if payload & DATA_FLAG:
            kind = (payload >> 6) & 0x7
            val = payload & 0x3F
            if meta_open:
                meta_vals[kind] = val
            else:
                color_data.append((kind, val))
            continue

        cmd = (payload >> 6) & 0x7
        arg = payload & 0x3F

        if cmd == CMD_META and arg == META_BEGIN:
            meta_open = True
            continue
        if cmd == CMD_META and arg == META_END:
            meta_open = False
            continue

        commands.append((cmd, max(1, arg)))

    width = _unpack_u12(meta_vals[M_WIDTH_HI], meta_vals[M_WIDTH_LO])
    height = _unpack_u12(meta_vals[M_HEIGHT_HI], meta_vals[M_HEIGHT_LO])
    root = _unpack_u12(meta_vals[M_ROOT_HI], meta_vals[M_ROOT_LO])
    bit_depth = max(1, min(int(meta_vals[M_BIT_DEPTH]), 6))
    thresh_x10 = int(meta_vals[M_THRESH_X10])

    meta = EnhancedMeta(width=width, height=height, root=root, bit_depth=bit_depth, threshold_x10=thresh_x10)

    if root <= 0:
        raise ValueError("invalid root in metadata")

    dequant_lut = _dequant_lut(bit_depth)
    canvas = np.zeros((root, root, 3), dtype=np.uint8)
    stack: list[tuple[int, int, int]] = [(0, 0, root)]

    cur = (0, 0, 0)
    color_idx = 0

    for cmd, run in commands:
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
                channels = {C_R: 0, C_G: 0, C_B: 0}
                seen = set()
                while color_idx < len(color_data) and len(seen) < 3:
                    k, v = color_data[color_idx]
                    color_idx += 1
                    if k in (C_R, C_G, C_B):
                        channels[k] = int(v)
                        seen.add(k)
                cur = (
                    int(dequant_lut[channels[C_R]]),
                    int(dequant_lut[channels[C_G]]),
                    int(dequant_lut[channels[C_B]]),
                )
            elif cmd == CMD_PAINT:
                x, y, size = stack[-1]
                canvas[y : y + size, x : x + size, :] = np.array(cur, dtype=np.uint8)

    return canvas[:height, :width, :], meta


def decode_enhanced(words: Sequence[int]) -> tuple[np.ndarray, EnhancedMeta]:
    native_decode = _native_quadtree_decoder()
    if native_decode is not None:
        image, meta_payload = native_decode(words)
        return image, EnhancedMeta(
            width=int(meta_payload["width"]),
            height=int(meta_payload["height"]),
            root=int(meta_payload["root"]),
            bit_depth=int(meta_payload["bit_depth"]),
            threshold_x10=int(meta_payload["threshold_x10"]),
        )

    payloads: list[int] = []
    for wv in words:
        value = int(wv)
        mode = (value >> 18) & 0x3
        version = (value >> 16) & 0x3
        payload = value & 0xFFFF
        if mode == Mode.EXTENSION.value and version == DEFAULT_VERSION and _is_family(payload):
            payloads.append(payload)
    return decode_enhanced_payloads(payloads)


def psnr(reference: np.ndarray, candidate: np.ndarray) -> float:
    x = reference.astype(np.float64)
    y = candidate.astype(np.float64)
    mse = float(np.mean((x - y) ** 2))
    if mse == 0.0:
        return 99.0
    return float(10.0 * np.log10((255.0 ** 2) / mse))


def quantized_reference(image: np.ndarray, bit_depth: int) -> np.ndarray:
    # Match decoder reconstruction levels exactly so PSNR is evaluated
    # against the actual quantized-dequantized reference.
    return _quantize(image, bit_depth)
