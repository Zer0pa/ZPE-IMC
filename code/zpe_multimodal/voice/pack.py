from __future__ import annotations

from typing import Iterable, List

from ..core.constants import DEFAULT_VERSION, Mode
from .flags import voice_enabled
from .types import VoiceStroke, VoiceMetadata
from ..diagram.quantize import MoveTo, DrawDir

# Voice uses extension bit 13 (distinct from diagrams bit 15, music bit 14).
VOICE_TYPE_BIT = 0x2000

# Voice keeps subtype in bits [11..10] so bit 13 remains an isolated type bit.
SUBTYPE_SHIFT = 10
SUBTYPE_MASK = 0x3
SUBTYPE_BOUNDARY = 0
SUBTYPE_MOVE_T = 1
SUBTYPE_MOVE_P = 2
SUBTYPE_DRAW_RUN = 3
SUBTYPE_META = 4  # logical marker used by metadata helpers

CANVAS_LIMIT = 0x3FF  # 10 bits for x/y payloads

# Boundary/meta subtype payload schema (subtype 0):
# - bit 9: metadata flag
# - bits [8..7]: metadata kind
# - bits [6..0]: metadata value
META_FLAG = 1 << 9
META_KIND_SHIFT = 7
META_KIND_MASK = 0x3
META_VALUE_MASK = 0x7F

META_KIND_LANG = 0
META_KIND_TIME_STEP = 1
META_KIND_PITCH_LEVELS = 2

LANG_TO_CODE = {"en": 1}
CODE_TO_LANG = {1: "en"}

# Control words are encoded as SUBTYPE_MOVE_T when no immediate MoveP follows.
# 10-bit payload schema:
# - bits [9..7]: control tag
# - bits [6..0]: control value
CTRL_TAG_SHIFT = 7
CTRL_TAG_MASK = 0x7
CTRL_VALUE_MASK = 0x7F

CTRL_TAG_TIME_ANCHOR = 0
CTRL_TAG_FORMANT_F1 = 1
CTRL_TAG_FORMANT_F2 = 2
CTRL_TAG_SPEAK_RATE = 3
CTRL_TAG_EMOTION = 4


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | payload


def _subtype(payload: int) -> int:
    return (payload >> SUBTYPE_SHIFT) & SUBTYPE_MASK


def _with_subtype(subtype: int, data: int) -> int:
    return VOICE_TYPE_BIT | ((subtype & SUBTYPE_MASK) << SUBTYPE_SHIFT) | data


def _control_data(tag: int, value: int) -> int:
    return ((tag & CTRL_TAG_MASK) << CTRL_TAG_SHIFT) | (value & CTRL_VALUE_MASK)


def _emit_control(words: List[int], tag: int, value: int) -> None:
    words.append(_ext_word(_with_subtype(SUBTYPE_MOVE_T, _control_data(tag, value))))


def _clamp_int(value: int | None, min_val: int, max_val: int) -> int | None:
    if value is None:
        return None
    return max(min_val, min(max_val, int(value)))


def pack_voice_strokes(strokes: Iterable[VoiceStroke], metadata: VoiceMetadata | None = None) -> List[int]:
    if not voice_enabled():
        raise RuntimeError("voice packing requires STROKEGRAM_ENABLE_VOICE=1")

    words: List[int] = []
    words.extend(_encode_metadata(metadata))

    for stroke in strokes:
        anchor = _clamp_int(stroke.time_anchor_tick, 0, CTRL_VALUE_MASK)
        if anchor is not None:
            _emit_control(words, CTRL_TAG_TIME_ANCHOR, anchor)

        f1 = _clamp_int(stroke.formant_f1_band, 0, 15)
        f2 = _clamp_int(stroke.formant_f2_band, 0, 15)
        rate = _clamp_int(stroke.speaking_rate_bucket, 0, 15)
        emotion = _clamp_int(stroke.emotion_valence, 0, 7)
        if f1 is not None:
            _emit_control(words, CTRL_TAG_FORMANT_F1, f1)
        if f2 is not None:
            _emit_control(words, CTRL_TAG_FORMANT_F2, f2)
        if rate is not None:
            _emit_control(words, CTRL_TAG_SPEAK_RATE, rate)
        if emotion is not None:
            _emit_control(words, CTRL_TAG_EMOTION, emotion)

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
                words.append(_ext_word(_with_subtype(SUBTYPE_DRAW_RUN, ((dir_idx & 0x7) << 7) | (run & 0x7F))))
            else:
                raise TypeError(f"unknown command {cmd!r}")
        words.append(_ext_word(_with_subtype(SUBTYPE_BOUNDARY, 0)))  # END
    return words


def unpack_voice_words(words: Iterable[int]) -> List[VoiceStroke]:
    if not voice_enabled():
        raise RuntimeError("voice unpack requires STROKEGRAM_ENABLE_VOICE=1")

    paths: List[VoiceStroke] = []
    meta = VoiceMetadata()
    current_cmds: List = []
    cx = cy = 0

    pending_anchor: int | None = None
    pending_f1: int | None = None
    pending_f2: int | None = None
    pending_rate: int | None = None
    pending_emotion: int | None = None

    current_anchor: int | None = None
    current_f1: int | None = None
    current_f2: int | None = None
    current_rate: int | None = None
    current_emotion: int | None = None

    def _flush_current() -> None:
        nonlocal current_cmds
        if current_cmds:
            paths.append(
                VoiceStroke(
                    commands=current_cmds,
                    symbol="",
                    stress=False,
                    time_anchor_tick=current_anchor,
                    formant_f1_band=current_f1,
                    formant_f2_band=current_f2,
                    speaking_rate_bucket=current_rate,
                    emotion_valence=current_emotion,
                )
            )
            current_cmds = []

    packed = list(words)
    idx = 0
    while idx < len(packed):
        w = packed[idx]
        mode = (w >> 18) & 0x3
        version = (w >> 16) & 0x3
        payload = w & 0xFFFF

        if mode != Mode.EXTENSION.value or not (payload & VOICE_TYPE_BIT):
            raise ValueError(f"non-voice word encountered: {w:#x}")
        if version != DEFAULT_VERSION:
            raise ValueError(f"unsupported extension version {version}")

        subtype = _subtype(payload)

        if subtype == SUBTYPE_BOUNDARY:
            if payload & META_FLAG:
                meta = _decode_meta(payload, meta)
                idx += 1
                continue

            start = payload & 0x1
            if start == 1:
                _flush_current()
                current_anchor = pending_anchor
                current_f1 = pending_f1
                current_f2 = pending_f2
                current_rate = pending_rate
                current_emotion = pending_emotion

                pending_anchor = None
                pending_f1 = None
                pending_f2 = None
                pending_rate = None
                pending_emotion = None
            else:
                _flush_current()
                current_anchor = None
                current_f1 = None
                current_f2 = None
                current_rate = None
                current_emotion = None
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
                    and (next_payload & VOICE_TYPE_BIT)
                    and _subtype(next_payload) == SUBTYPE_MOVE_P
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
            elif tag == CTRL_TAG_FORMANT_F1:
                pending_f1 = value & 0xF
            elif tag == CTRL_TAG_FORMANT_F2:
                pending_f2 = value & 0xF
            elif tag == CTRL_TAG_SPEAK_RATE:
                pending_rate = value & 0xF
            elif tag == CTRL_TAG_EMOTION:
                pending_emotion = value & 0x7
            else:
                raise ValueError(f"unknown voice control tag {tag}")
            idx += 1
            continue

        if subtype == SUBTYPE_MOVE_P:
            raise ValueError("MoveP without preceding MoveT")

        if subtype == SUBTYPE_DRAW_RUN:
            dir_idx = (payload >> 7) & 0x7
            run_len = payload & 0x7F
            if run_len == 0:
                raise ValueError("run_len must be >=1")
            if not current_cmds:
                current_cmds.append(MoveTo(cx, cy))
            for _ in range(run_len):
                current_cmds.append(DrawDir(dir_idx))
            idx += 1
            continue

        raise ValueError(f"unknown voice subtype {subtype}")

    _flush_current()

    for p in paths:
        setattr(p, "metadata", meta)
    return paths


def _encode_metadata(meta: VoiceMetadata | None) -> List[int]:
    if meta is None:
        meta = VoiceMetadata()

    words: List[int] = []

    lang = (meta.language or "en").lower()[:2]
    lang_code = LANG_TO_CODE.get(lang, LANG_TO_CODE["en"])
    words.append(
        _ext_word(
            _with_subtype(
                SUBTYPE_BOUNDARY,
                META_FLAG | ((META_KIND_LANG & META_KIND_MASK) << META_KIND_SHIFT) | (lang_code & META_VALUE_MASK),
            )
        )
    )

    ts_ms = int(round(float(meta.time_step_sec) * 1000.0))
    ts_ms = max(0, min(META_VALUE_MASK, ts_ms))
    words.append(
        _ext_word(
            _with_subtype(
                SUBTYPE_BOUNDARY,
                META_FLAG | ((META_KIND_TIME_STEP & META_KIND_MASK) << META_KIND_SHIFT) | ts_ms,
            )
        )
    )

    pl = int(meta.pitch_levels)
    pl = max(0, min(META_VALUE_MASK, pl))
    words.append(
        _ext_word(
            _with_subtype(
                SUBTYPE_BOUNDARY,
                META_FLAG | ((META_KIND_PITCH_LEVELS & META_KIND_MASK) << META_KIND_SHIFT) | pl,
            )
        )
    )

    return words


def _decode_meta(payload: int, meta: VoiceMetadata) -> VoiceMetadata:
    kind = (payload >> META_KIND_SHIFT) & META_KIND_MASK
    val = payload & META_VALUE_MASK

    if kind == META_KIND_LANG:
        language = CODE_TO_LANG.get(val, "en")
        return VoiceMetadata(language=language, time_step_sec=meta.time_step_sec, pitch_levels=meta.pitch_levels)

    if kind == META_KIND_TIME_STEP:
        return VoiceMetadata(language=meta.language, time_step_sec=float(val) / 1000.0, pitch_levels=meta.pitch_levels)

    if kind == META_KIND_PITCH_LEVELS:
        return VoiceMetadata(language=meta.language, time_step_sec=meta.time_step_sec, pitch_levels=val)

    return meta
