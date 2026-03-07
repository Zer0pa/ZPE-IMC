from __future__ import annotations

from dataclasses import replace
from typing import Iterable, List

from ..core.constants import DEFAULT_VERSION, Mode
from .flags import music_enabled
from .types import MusicMetadata, MusicStroke
from ..diagram.quantize import DrawDir, MoveTo

# Extension payload bit 14 flags music blocks (bit 15 used by diagrams).
MUSIC_TYPE_BIT = 0x4000
# Collision-safe subtype layout in low payload bits [11..10].
SUBTYPE_BOUNDARY = 0
SUBTYPE_MOVE_T = 1
SUBTYPE_MOVE_P = 2
SUBTYPE_DRAW_RUN = 3
SUBTYPE_SHIFT = 10
SUBTYPE_MASK = 0x3

CANVAS_LIMIT = 0x3FF  # 10 bits for positions/run payloads
MAX_RUN = 0x7F        # run shares payload with 3-bit direction

META_FLAG = 1 << 9
META_KIND_SHIFT = 7
META_KIND_MASK = 0x3
META_VALUE_MASK = 0x7F

META_KIND_TIMESIG = 0
META_KIND_KEY = 1
META_KIND_TEMPO = 2
META_KIND_DYNAMIC = 3

# Control words are represented as SUBTYPE_MOVE_T when no immediate MoveP follows.
CTRL_TAG_SHIFT = 7
CTRL_TAG_MASK = 0x7
CTRL_VALUE_MASK = 0x7F
CTRL_TAG_TIME_ANCHOR = 0


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | payload


def _with_subtype(subtype: int, data: int) -> int:
    return MUSIC_TYPE_BIT | ((subtype & SUBTYPE_MASK) << SUBTYPE_SHIFT) | data


def _control_data(tag: int, value: int) -> int:
    return ((tag & CTRL_TAG_MASK) << CTRL_TAG_SHIFT) | (value & CTRL_VALUE_MASK)


def _emit_control(words: List[int], tag: int, value: int) -> None:
    words.append(_ext_word(_with_subtype(SUBTYPE_MOVE_T, _control_data(tag, value))))


def _clamp_anchor(value: int | None) -> int | None:
    if value is None:
        return None
    return max(0, min(CTRL_VALUE_MASK, int(value)))


def pack_music_strokes(strokes: Iterable[MusicStroke], metadata=None) -> List[int]:
    if not music_enabled():
        raise RuntimeError("music packing requires STROKEGRAM_ENABLE_MUSIC=1")
    words: List[int] = []

    # Metadata header (time/key/tempo/dynamic) encoded once up front.
    words.extend(_encode_metadata(metadata))
    for stroke in strokes:
        anchor = _clamp_anchor(stroke.time_anchor_tick)
        if anchor is not None:
            _emit_control(words, CTRL_TAG_TIME_ANCHOR, anchor)

        words.append(_ext_word(_with_subtype(SUBTYPE_BOUNDARY, 1)))  # BEGIN
        for cmd in stroke.commands:
            if isinstance(cmd, MoveTo):
                x_val = int(cmd.x)
                y_val = int(cmd.y)
                if anchor is not None:
                    x_val -= anchor
                if not (0 <= x_val <= CANVAS_LIMIT and 0 <= y_val <= CANVAS_LIMIT):
                    raise ValueError(f"MoveTo out of range: {(cmd.x, cmd.y)}")
                words.append(_ext_word(_with_subtype(SUBTYPE_MOVE_T, x_val & CANVAS_LIMIT)))
                words.append(_ext_word(_with_subtype(SUBTYPE_MOVE_P, y_val & CANVAS_LIMIT)))
            elif isinstance(cmd, DrawDir):
                dir_idx = cmd.direction & 0x7
                run = 1
                words.append(
                    _ext_word(
                        _with_subtype(
                            SUBTYPE_DRAW_RUN,
                            ((dir_idx & 0x7) << 7) | (run & MAX_RUN),
                        )
                    )
                )
            else:
                raise TypeError(f"unknown command {cmd!r}")
        words.append(_ext_word(_with_subtype(SUBTYPE_BOUNDARY, 0)))  # END
    return words


def unpack_music_words(words: Iterable[int]) -> tuple[MusicMetadata | None, List[MusicStroke]]:
    paths: List[MusicStroke] = []
    meta = MusicMetadata()
    current_cmds: List = []
    cx = cy = 0

    pending_anchor: int | None = None
    current_anchor: int | None = None

    def _flush_current() -> None:
        nonlocal current_cmds
        if current_cmds:
            paths.append(MusicStroke(commands=current_cmds, time_anchor_tick=current_anchor))
            current_cmds = []

    packed = list(words)
    idx = 0
    while idx < len(packed):
        w = packed[idx]
        mode = (w >> 18) & 0x3
        version = (w >> 16) & 0x3
        payload = w & 0xFFFF
        if mode != Mode.EXTENSION.value or not (payload & MUSIC_TYPE_BIT):
            raise ValueError(f"non-music word encountered: {w:#x}")
        if version != DEFAULT_VERSION:
            raise ValueError(f"unsupported extension version {version}")

        subtype = (payload >> SUBTYPE_SHIFT) & SUBTYPE_MASK

        if subtype == SUBTYPE_BOUNDARY:
            if payload & META_FLAG:
                meta = _decode_meta_word(payload, meta)
                idx += 1
                continue
            start = payload & 0x1
            if start == 1:
                _flush_current()
                current_anchor = pending_anchor
                pending_anchor = None
            else:
                _flush_current()
                current_anchor = None
            idx += 1
            continue

        if subtype == SUBTYPE_MOVE_T:
            move_t_data = payload & CANVAS_LIMIT

            if idx + 1 < len(packed):
                next_w = packed[idx + 1]
                next_mode = (next_w >> 18) & 0x3
                next_version = (next_w >> 16) & 0x3
                next_payload = next_w & 0xFFFF
                if (
                    next_mode == Mode.EXTENSION.value
                    and next_version == DEFAULT_VERSION
                    and (next_payload & MUSIC_TYPE_BIT)
                    and ((next_payload >> SUBTYPE_SHIFT) & SUBTYPE_MASK) == SUBTYPE_MOVE_P
                ):
                    cy = next_payload & CANVAS_LIMIT
                    cx = move_t_data + (current_anchor or 0)
                    _flush_current()
                    current_cmds = [MoveTo(cx, cy)]
                    idx += 2
                    continue

            tag = (move_t_data >> CTRL_TAG_SHIFT) & CTRL_TAG_MASK
            value = move_t_data & CTRL_VALUE_MASK
            if tag == CTRL_TAG_TIME_ANCHOR:
                pending_anchor = value
            else:
                raise ValueError(f"unknown music control tag {tag}")
            idx += 1
            continue

        if subtype == SUBTYPE_MOVE_P:
            raise ValueError("MoveP without preceding MoveT")

        if subtype == SUBTYPE_DRAW_RUN:
            dir_idx = (payload >> 7) & 0x7
            run_len = payload & MAX_RUN
            if run_len == 0:
                raise ValueError("run_len must be >=1")
            if not current_cmds:
                current_cmds.append(MoveTo(cx, cy))
            for _ in range(run_len):
                current_cmds.append(DrawDir(dir_idx))
            idx += 1
            continue

        raise ValueError(f"unknown music subtype {subtype}")

    _flush_current()
    return meta, paths


def _encode_metadata(meta: MusicMetadata | None) -> List[int]:
    meta_words: List[int] = []
    if meta is None:
        return meta_words
    meta_template = meta if isinstance(meta, MusicMetadata) else MusicMetadata()
    # Time signature (num, den) packed into 7 bits: 4+3
    if meta_template.time_signature is not None:
        num, den = meta_template.time_signature
        num_c = max(0, min(15, int(num)))
        den_c = max(0, min(7, int(den)))
        payload = (
            MUSIC_TYPE_BIT
            | (SUBTYPE_BOUNDARY << SUBTYPE_SHIFT)
            | META_FLAG
            | ((META_KIND_TIMESIG & META_KIND_MASK) << META_KIND_SHIFT)
            | (((num_c << 3) | (den_c & 0x7)) & META_VALUE_MASK)
        )
        meta_words.append(_ext_word(payload))
    # Key signature
    if meta_template.key_signature is not None:
        key_c = max(0, min(META_VALUE_MASK, meta_template.key_signature + 64))
        payload = (
            MUSIC_TYPE_BIT
            | (SUBTYPE_BOUNDARY << SUBTYPE_SHIFT)
            | META_FLAG
            | ((META_KIND_KEY & META_KIND_MASK) << META_KIND_SHIFT)
            | key_c
        )
        meta_words.append(_ext_word(payload))
    # Tempo (store bpm)
    if meta_template.tempo is not None:
        tempo_c = max(0, min(META_VALUE_MASK, int(round(meta_template.tempo))))
        payload = (
            MUSIC_TYPE_BIT
            | (SUBTYPE_BOUNDARY << SUBTYPE_SHIFT)
            | META_FLAG
            | ((META_KIND_TEMPO & META_KIND_MASK) << META_KIND_SHIFT)
            | tempo_c
        )
        meta_words.append(_ext_word(payload))
    # Dynamic (best-effort code)
    dyn_code = getattr(meta_template, "dynamic_base", None)
    if dyn_code:
        payload = (
            MUSIC_TYPE_BIT
            | (SUBTYPE_BOUNDARY << SUBTYPE_SHIFT)
            | META_FLAG
            | ((META_KIND_DYNAMIC & META_KIND_MASK) << META_KIND_SHIFT)
            | (dyn_code & META_VALUE_MASK)
        )
        meta_words.append(_ext_word(payload))
    return meta_words


def _decode_meta_word(payload: int, meta: MusicMetadata) -> MusicMetadata:
    kind = (payload >> META_KIND_SHIFT) & META_KIND_MASK
    value = payload & META_VALUE_MASK
    if kind == META_KIND_TIMESIG:
        num = (value >> 3) & 0xF
        den = value & 0x7
        if num and den:
            meta = meta.with_time_signature((num, den))
    elif kind == META_KIND_KEY:
        key = int(value) - 64
        meta = meta.with_key_signature(key)
    elif kind == META_KIND_TEMPO:
        tempo_bpm = value
        meta = meta.with_tempo(float(tempo_bpm))
    elif kind == META_KIND_DYNAMIC:
        code = value
        meta = replace(meta, dynamic_base=code)
    return meta
