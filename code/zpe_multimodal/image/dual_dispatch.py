from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .quadtree_enhanced_codec import (
    C_B,
    C_G,
    C_R,
    CMD_BACKTRACK as E_CMD_BACKTRACK,
    CMD_BL as E_CMD_BL,
    CMD_BR as E_CMD_BR,
    CMD_META,
    CMD_PAINT as E_CMD_PAINT,
    CMD_SET_COLOR as E_CMD_SET_COLOR,
    CMD_TL as E_CMD_TL,
    CMD_TR as E_CMD_TR,
    DATA_FLAG,
    IMAGE_FAMILY_VALUE as ENHANCED_FAMILY,
    M_BIT_DEPTH,
    M_HEIGHT_HI,
    M_HEIGHT_LO,
    M_ROOT_HI,
    M_ROOT_LO,
    M_THRESH_X10,
    M_WIDTH_HI,
    M_WIDTH_LO,
    META_BEGIN,
    META_END,
    _native_quadtree_decoder,
    decode_enhanced,
    decode_enhanced_payloads,
    encode_enhanced,
)
from .quadtree_legacy_codec import IMAGE_FAMILY_VALUE as LEGACY_FAMILY, decode_legacy, encode_legacy
from .quadtree_legacy_codec import (
    CMD_BACKTRACK as L_CMD_BACKTRACK,
    CMD_BL as L_CMD_BL,
    CMD_BR as L_CMD_BR,
    CMD_NOP as L_CMD_NOP,
    CMD_PAINT as L_CMD_PAINT,
    CMD_SET_COLOR as L_CMD_SET_COLOR,
    CMD_TL as L_CMD_TL,
    CMD_TR as L_CMD_TR,
    COLOR_FLAG,
)

FAMILY_MASK = 0x0C00
EXTENSION_MODE = 0x2
DEFAULT_VERSION = 0x0


@dataclass(frozen=True)
class DecodeResult:
    mode: str
    image: Any
    meta: Any


def _iter_image_payloads(words: Sequence[int]) -> list[int]:
    payloads: list[int] = []
    for word in words:
        payload = _image_payload(word)
        if payload is not None:
            payloads.append(payload)
    return payloads


def _image_payload(word: object) -> int | None:
    try:
        value = int(word)
    except (TypeError, ValueError):
        return None
    mode = (value >> 18) & 0x3
    version = (value >> 16) & 0x3
    if mode != EXTENSION_MODE or version != DEFAULT_VERSION:
        return None
    return value & 0xFFFF


def _detect_family_words(words: Sequence[int]) -> str:
    family: int | None = None
    for word in words:
        payload = _image_payload(word)
        if payload is None:
            continue
        current = payload & FAMILY_MASK
        if current not in (LEGACY_FAMILY, ENHANCED_FAMILY):
            if family is None:
                raise ValueError("no recognizable image family marker found")
            raise ValueError("mixed image family markers found")
        if family is None:
            family = current
            continue
        if current != family:
            raise ValueError("mixed image family markers found")
    if family is None:
        raise ValueError("no recognizable image family marker found")
    return "legacy" if family == LEGACY_FAMILY else "enhanced"


def _validate_legacy_stream(payloads: Sequence[int]) -> tuple[bool, str]:
    if not payloads:
        return False, "legacy stream has no extension payloads"

    depth = 1
    pending_color = False
    saw_set_color = False
    saw_paint = False
    for payload in payloads:
        family = payload & FAMILY_MASK
        if family != LEGACY_FAMILY:
            return False, "legacy stream has mixed/invalid family payload"

        if payload & COLOR_FLAG:
            if not pending_color:
                return False, "legacy stream has unexpected color payload"
            pending_color = False
            continue

        if pending_color:
            return False, "legacy stream missing color payload after SET_COLOR"

        cmd = (payload >> 6) & 0x7
        run = max(1, payload & 0x3F)
        if cmd in (L_CMD_TL, L_CMD_TR, L_CMD_BL, L_CMD_BR):
            depth += run
            continue
        if cmd == L_CMD_BACKTRACK:
            for _ in range(run):
                if depth <= 1:
                    return False, "legacy stream backtrack underflow"
                depth -= 1
            continue
        if cmd == L_CMD_SET_COLOR:
            if run != 1:
                return False, "legacy SET_COLOR run != 1"
            pending_color = True
            saw_set_color = True
            continue
        if cmd == L_CMD_PAINT:
            saw_paint = True
            continue
        if cmd == L_CMD_NOP:
            continue

        return False, "legacy stream has unknown command"

    if pending_color:
        return False, "legacy stream ended with incomplete color payload"
    if depth != 1:
        return False, "legacy stream ended with unbalanced traversal depth"
    if not saw_set_color or not saw_paint:
        return False, "legacy stream missing required SET_COLOR/PAINT sequence"
    return True, ""


def _validate_enhanced_stream(payloads: Sequence[int]) -> tuple[bool, str]:
    if not payloads:
        return False, "enhanced stream has no extension payloads"

    required_meta = {
        M_WIDTH_HI,
        M_WIDTH_LO,
        M_HEIGHT_HI,
        M_HEIGHT_LO,
        M_ROOT_HI,
        M_ROOT_LO,
        M_BIT_DEPTH,
        M_THRESH_X10,
    }
    seen_meta: set[int] = set()

    meta_open = False
    meta_begin_count = 0
    meta_end_count = 0

    depth = 1
    pending_channels: set[int] | None = None
    saw_set_color = False
    saw_paint = False
    for payload in payloads:
        family = payload & FAMILY_MASK
        if family != ENHANCED_FAMILY:
            return False, "enhanced stream has mixed/invalid family payload"

        if payload & DATA_FLAG:
            kind = (payload >> 6) & 0x7
            if meta_open:
                if kind in required_meta:
                    seen_meta.add(kind)
                continue
            if pending_channels is None:
                return False, "enhanced stream has unexpected data payload"
            if kind not in (C_R, C_G, C_B):
                return False, "enhanced stream has non-color data outside metadata block"
            if kind in pending_channels:
                return False, "enhanced stream has duplicate color channel payload"
            pending_channels.add(kind)
            if len(pending_channels) == 3:
                pending_channels = None
            continue

        cmd = (payload >> 6) & 0x7
        arg = payload & 0x3F
        run = max(1, arg)
        if cmd == CMD_META:
            if arg == META_BEGIN:
                if meta_open:
                    return False, "enhanced stream has nested META_BEGIN"
                meta_open = True
                meta_begin_count += 1
                continue
            if arg == META_END:
                if not meta_open:
                    return False, "enhanced stream has META_END without META_BEGIN"
                meta_open = False
                meta_end_count += 1
                continue
            return False, "enhanced stream has invalid META command arg"

        if meta_open:
            return False, "enhanced command encountered while metadata block is open"

        if cmd in (E_CMD_TL, E_CMD_TR, E_CMD_BL, E_CMD_BR):
            depth += run
            continue
        if cmd == E_CMD_BACKTRACK:
            for _ in range(run):
                if depth <= 1:
                    return False, "enhanced stream backtrack underflow"
                depth -= 1
            continue
        if cmd == E_CMD_SET_COLOR:
            if pending_channels is not None:
                return False, "enhanced stream has incomplete prior color triplet"
            pending_channels = set()
            saw_set_color = True
            continue
        if cmd == E_CMD_PAINT:
            saw_paint = True
            continue

        return False, "enhanced stream has unknown command"

    if meta_open:
        return False, "enhanced stream ended with open metadata block"
    if pending_channels is not None:
        return False, "enhanced stream ended with incomplete color triplet"
    if meta_begin_count != 1 or meta_end_count != 1:
        return False, "enhanced stream metadata framing count invalid"
    if not required_meta.issubset(seen_meta):
        return False, "enhanced stream missing required metadata fields"
    if depth != 1:
        return False, "enhanced stream ended with unbalanced traversal depth"
    if not saw_set_color or not saw_paint:
        return False, "enhanced stream missing required SET_COLOR/PAINT sequence"
    return True, ""


def detect_family(words: Sequence[int]) -> str:
    return _detect_family_words(words)


def _detect_family_payloads(payloads: Sequence[int]) -> str:
    if not payloads:
        raise ValueError("no recognizable image family marker found")

    family_0 = payloads[0] & FAMILY_MASK
    if family_0 not in (LEGACY_FAMILY, ENHANCED_FAMILY):
        raise ValueError("no recognizable image family marker found")
    for payload in payloads[1:]:
        if (payload & FAMILY_MASK) != family_0:
            raise ValueError("mixed image family markers found")
    return "legacy" if family_0 == LEGACY_FAMILY else "enhanced"


def _decode_enhanced_words(words: Sequence[int], payloads: Sequence[int] | None = None) -> DecodeResult:
    if _native_quadtree_decoder() is not None:
        image, meta = decode_enhanced(words)
        return DecodeResult(mode="enhanced", image=image, meta=meta)

    if payloads is None:
        payloads = _iter_image_payloads(words)
    ok, reason = _validate_enhanced_stream(payloads)
    if not ok:
        raise ValueError(f"invalid enhanced stream: {reason}")
    image, meta = decode_enhanced_payloads(payloads)
    return DecodeResult(mode="enhanced", image=image, meta=meta)


def decode_image_words(words: Sequence[int], *, legacy_shape: tuple[int, int] | None = None) -> DecodeResult:
    mode = _detect_family_words(words)
    if mode == "legacy":
        payloads = _iter_image_payloads(words)
        ok, reason = _validate_legacy_stream(payloads)
        if not ok:
            raise ValueError(f"invalid legacy stream: {reason}")
        if legacy_shape is None:
            raise ValueError("legacy decode requires legacy_shape=(h,w)")
        img = decode_legacy(words, shape=legacy_shape)
        return DecodeResult(mode="legacy", image=img, meta={"shape": legacy_shape})

    return _decode_enhanced_words(words)


def encode_image_legacy(image, threshold: float = 5.0):
    return encode_legacy(image, threshold=threshold)


def encode_image_enhanced(image, threshold: float = 5.0, bit_depth: int = 3):
    return encode_enhanced(image, threshold=threshold, bit_depth=bit_depth)
