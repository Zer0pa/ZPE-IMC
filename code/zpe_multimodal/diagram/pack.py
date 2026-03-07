from __future__ import annotations

from dataclasses import replace
from typing import Iterable, List

from ..core.constants import DEFAULT_VERSION, Mode
from .quantize import DrawDir, MoveTo, StrokePath, decode_style, encode_style

# Visual family bit shared by diagram+image.
VISUAL_TYPE_BIT = 0x8000
# Backward-compatible alias used by existing IMC imports/tests.
DIAGRAM_TYPE_BIT = VISUAL_TYPE_BIT
# Reserved profile bit (kept for compatibility/documentation).
VISUAL_PROFILE_BIT = 0x0800

SUBTYPE_MOVE_X = 0
SUBTYPE_MOVE_Y = 1
SUBTYPE_DRAW_RUN = 2  # dir bits in [9..7], run length in [6..0]
SUBTYPE_BOUNDARY = 3  # bit0=start, bit1=style follows (end boundary only)

SUBTYPE_SHIFT = 10
SUBTYPE_MASK = 0x3
DATA_MASK = 0x03FF
MAX_COORD = DATA_MASK
MAX_RUN = 0x7F

BOUNDARY_START_BIT = 0x0001
BOUNDARY_STYLE_FOLLOWS_BIT = 0x0002


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | (payload & 0xFFFF)


def _boundary_word(*, start: bool, style_follows: bool = False) -> int:
    payload = VISUAL_TYPE_BIT | (SUBTYPE_BOUNDARY << SUBTYPE_SHIFT)
    if start:
        payload |= BOUNDARY_START_BIT
    if style_follows:
        payload |= BOUNDARY_STYLE_FOLLOWS_BIT
    return _ext_word(payload)


def is_visual_word(word: int) -> bool:
    if not isinstance(word, int):
        return False
    return ((word >> 18) & 0x3) == Mode.EXTENSION.value and bool((word & 0xFFFF) & VISUAL_TYPE_BIT)


def is_diagram_header(word: int) -> bool:
    if not is_visual_word(word):
        return False
    payload = word & 0xFFFF
    subtype = (payload >> SUBTYPE_SHIFT) & SUBTYPE_MASK
    is_start = bool(payload & BOUNDARY_START_BIT)
    profile_is_image = bool(payload & VISUAL_PROFILE_BIT)
    return subtype == SUBTYPE_BOUNDARY and is_start and not profile_is_image


def _emit_run(words: List[int], direction: int, run_len: int) -> None:
    remaining = run_len
    while remaining > 0:
        chunk = min(remaining, MAX_RUN)
        words.append(
            _ext_word(
                VISUAL_TYPE_BIT
                | (SUBTYPE_DRAW_RUN << SUBTYPE_SHIFT)
                | ((direction & 0x7) << 7)
                | (chunk & MAX_RUN)
            )
        )
        remaining -= chunk


def pack_diagram_paths(
    paths: Iterable[StrokePath],
    canvas_size: int = 256,
    *,
    encode_styles: bool = False,
) -> List[int]:
    """
    Pack diagram paths into extension words.

    Collision-safe layout: subtype fields are in low bits and never set music/voice/BPE
    type bits. Optional style suffix encodes exactly 3 words on end boundary.
    """
    if canvas_size <= 0 or canvas_size > (MAX_COORD + 1):
        raise ValueError(f"canvas_size out of range: {canvas_size}")

    words: List[int] = []
    for path in paths:
        words.append(_boundary_word(start=True, style_follows=False))

        i = 0
        commands = path.commands
        while i < len(commands):
            cmd = commands[i]

            if isinstance(cmd, MoveTo):
                if not (0 <= cmd.x < canvas_size and 0 <= cmd.y < canvas_size):
                    raise ValueError(f"MoveTo out of canvas: {(cmd.x, cmd.y)}")
                words.append(_ext_word(VISUAL_TYPE_BIT | (SUBTYPE_MOVE_X << SUBTYPE_SHIFT) | (cmd.x & DATA_MASK)))
                words.append(_ext_word(VISUAL_TYPE_BIT | (SUBTYPE_MOVE_Y << SUBTYPE_SHIFT) | (cmd.y & DATA_MASK)))
                i += 1
                continue

            if isinstance(cmd, DrawDir):
                if not (0 <= cmd.direction <= 7):
                    raise ValueError(f"invalid direction index: {cmd.direction}")
                direction = cmd.direction
                run_len = 1
                j = i + 1
                while j < len(commands):
                    nxt = commands[j]
                    if isinstance(nxt, DrawDir) and nxt.direction == direction:
                        run_len += 1
                        j += 1
                    else:
                        break
                _emit_run(words, direction, run_len)
                i = j
                continue

            raise TypeError(f"unknown command {cmd!r}")

        style_payload = encode_style(path) if encode_styles else None
        words.append(_boundary_word(start=False, style_follows=style_payload is not None))

        if style_payload is not None:
            width_code, color_idx, dash_idx = style_payload
            words.append(_ext_word(VISUAL_TYPE_BIT | (SUBTYPE_MOVE_X << SUBTYPE_SHIFT) | (width_code & DATA_MASK)))
            words.append(_ext_word(VISUAL_TYPE_BIT | (SUBTYPE_MOVE_Y << SUBTYPE_SHIFT) | (color_idx & DATA_MASK)))
            words.append(
                _ext_word(
                    VISUAL_TYPE_BIT
                    | (SUBTYPE_DRAW_RUN << SUBTYPE_SHIFT)
                    | ((dash_idx & 0x7) << 7)
                    | 1
                )
            )

    return words


def _parse_style_suffix(words: List[int], index: int) -> tuple[dict[str, object] | None, int]:
    if index + 2 >= len(words):
        return None, index

    w0, w1, w2 = words[index], words[index + 1], words[index + 2]
    p0 = w0 & 0xFFFF
    p1 = w1 & 0xFFFF
    p2 = w2 & 0xFFFF

    s0 = (p0 >> SUBTYPE_SHIFT) & SUBTYPE_MASK
    s1 = (p1 >> SUBTYPE_SHIFT) & SUBTYPE_MASK
    s2 = (p2 >> SUBTYPE_SHIFT) & SUBTYPE_MASK
    if s0 != SUBTYPE_MOVE_X or s1 != SUBTYPE_MOVE_Y or s2 != SUBTYPE_DRAW_RUN:
        return None, index

    width_code = p0 & DATA_MASK
    color_idx = p1 & DATA_MASK
    dash_idx = (p2 >> 7) & 0x7
    style = decode_style(width_code, color_idx, dash_idx)
    return style, index + 3


def unpack_diagram_words(words: Iterable[int]) -> List[StrokePath]:
    """Inverse of `pack_diagram_paths` including optional style suffix decode."""
    in_words = [int(w) for w in words if isinstance(w, int)]

    paths: List[StrokePath] = []
    current: List[MoveTo | DrawDir] = []
    cx = cy = 0
    pending_x: int | None = None

    def flush_current() -> None:
        nonlocal current
        if current:
            paths.append(StrokePath(commands=current))
            current = []

    i = 0
    while i < len(in_words):
        w = in_words[i]
        mode = (w >> 18) & 0x3
        version = (w >> 16) & 0x3
        payload = w & 0xFFFF

        if mode != Mode.EXTENSION.value or version != DEFAULT_VERSION or not (payload & VISUAL_TYPE_BIT):
            i += 1
            continue

        subtype = (payload >> SUBTYPE_SHIFT) & SUBTYPE_MASK

        if subtype == SUBTYPE_BOUNDARY:
            start = bool(payload & BOUNDARY_START_BIT)
            style_follows = bool(payload & BOUNDARY_STYLE_FOLLOWS_BIT)

            flush_current()
            pending_x = None
            i += 1

            if (not start) and style_follows and paths:
                style, next_i = _parse_style_suffix(in_words, i)
                if style is not None:
                    paths[-1] = replace(
                        paths[-1],
                        stroke=style["stroke"],
                        stroke_width=style["stroke_width"],
                        dash=style["dash"],
                    )
                    i = next_i
            continue

        if subtype == SUBTYPE_MOVE_X:
            pending_x = payload & DATA_MASK
            i += 1
            continue

        if subtype == SUBTYPE_MOVE_Y:
            if pending_x is not None:
                cx = pending_x
                cy = payload & DATA_MASK
                flush_current()
                current = [MoveTo(cx, cy)]
                pending_x = None
            i += 1
            continue

        if subtype == SUBTYPE_DRAW_RUN:
            direction = (payload >> 7) & 0x7
            run_len = payload & MAX_RUN
            if run_len > 0:
                if not current:
                    current.append(MoveTo(cx, cy))
                for _ in range(run_len):
                    current.append(DrawDir(direction))
            i += 1
            continue

        i += 1

    flush_current()
    return paths
