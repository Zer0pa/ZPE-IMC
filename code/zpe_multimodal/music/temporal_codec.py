from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from ..core.constants import DEFAULT_VERSION, Mode

MUSIC_TYPE_BIT = 0x4000

# 2-bit temporal event kind in payload bits [13:12]
KIND_NOTE = 0
KIND_DURATION = 1
KIND_TIME_ADVANCE = 2
KIND_PROGRAM = 3

KIND_SHIFT = 12
KIND_MASK = 0x3
DATA_MASK = 0x0FFF

TIME_QUANT_MS_DEFAULT = 50


@dataclass(frozen=True)
class TemporalNoteEvent:
    start_ms: int
    duration_ms: int
    pitch: int
    velocity: int
    channel: int = 0
    program: int = 0


def _ext_word(payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | (payload & 0xFFFF)


def _payload(kind: int, data: int) -> int:
    return MUSIC_TYPE_BIT | ((kind & KIND_MASK) << KIND_SHIFT) | (data & DATA_MASK)


def _pack_time_advance(frames: int) -> list[int]:
    words: list[int] = []
    remaining = int(frames)
    while remaining > 0:
        chunk = min(remaining, DATA_MASK)
        words.append(_ext_word(_payload(KIND_TIME_ADVANCE, chunk)))
        remaining -= chunk
    return words


def _pack_program(channel: int, program: int) -> int:
    # channel: 0..15 (4 bits), program: 0..127 (7 bits)
    data = ((channel & 0xF) << 7) | (program & 0x7F)
    return _ext_word(_payload(KIND_PROGRAM, data))


def _pack_note(channel: int, pitch: int) -> int:
    # channel: 0..15 (4 bits), pitch: 0..127 (7 bits)
    data = ((channel & 0xF) << 7) | (pitch & 0x7F)
    return _ext_word(_payload(KIND_NOTE, data))


def _pack_duration(duration_frames: int, velocity: int) -> list[int]:
    # duration chunk: 5 bits (1..31), velocity: 7 bits (0..127)
    words: list[int] = []
    remaining = int(duration_frames)
    vel = int(max(0, min(127, velocity)))
    while remaining > 0:
        chunk = min(remaining, 31)
        data = ((chunk & 0x1F) << 7) | (vel & 0x7F)
        words.append(_ext_word(_payload(KIND_DURATION, data)))
        remaining -= chunk
    return words


def encode_temporal_events(
    events: Iterable[TemporalNoteEvent],
    time_quant_ms: int = TIME_QUANT_MS_DEFAULT,
) -> list[int]:
    if time_quant_ms <= 0:
        raise ValueError("time_quant_ms must be > 0")

    sorted_events = sorted(
        events,
        key=lambda e: (int(e.start_ms), int(e.channel), int(e.pitch), int(e.program), int(e.velocity), int(e.duration_ms)),
    )

    words: list[int] = []
    current_ms = 0
    program_by_channel = {ch: None for ch in range(16)}

    for ev in sorted_events:
        start_ms = int(ev.start_ms)
        if start_ms < current_ms:
            raise ValueError("events must be sorted by start time")

        delta_ms = start_ms - current_ms
        delta_frames = int(round(delta_ms / time_quant_ms))
        if delta_frames > 0:
            words.extend(_pack_time_advance(delta_frames))
            current_ms += delta_frames * time_quant_ms

        ch = int(max(0, min(15, ev.channel)))
        prog = int(max(0, min(127, ev.program)))
        if program_by_channel[ch] != prog:
            words.append(_pack_program(ch, prog))
            program_by_channel[ch] = prog

        pitch = int(max(0, min(127, ev.pitch)))
        words.append(_pack_note(ch, pitch))

        duration_ms = int(max(0, ev.duration_ms))
        duration_frames = max(1, int(round(duration_ms / time_quant_ms)))
        words.extend(_pack_duration(duration_frames, int(ev.velocity)))

    return words


def decode_temporal_words(
    words: Iterable[int],
    time_quant_ms: int = TIME_QUANT_MS_DEFAULT,
) -> list[TemporalNoteEvent]:
    if time_quant_ms <= 0:
        raise ValueError("time_quant_ms must be > 0")

    current_ms = 0
    program_by_channel = {ch: 0 for ch in range(16)}

    out: list[TemporalNoteEvent] = []

    pending_pitch: int | None = None
    pending_channel: int | None = None
    pending_start_ms: int | None = None
    pending_velocity = 64
    pending_duration_frames = 0

    def flush_pending() -> None:
        nonlocal pending_pitch, pending_channel, pending_start_ms, pending_velocity, pending_duration_frames
        if pending_pitch is None or pending_channel is None or pending_start_ms is None:
            return
        duration_frames = max(1, pending_duration_frames)
        out.append(
            TemporalNoteEvent(
                start_ms=pending_start_ms,
                duration_ms=duration_frames * time_quant_ms,
                pitch=pending_pitch,
                velocity=int(max(0, min(127, pending_velocity))),
                channel=pending_channel,
                program=program_by_channel[pending_channel],
            )
        )
        pending_pitch = None
        pending_channel = None
        pending_start_ms = None
        pending_velocity = 64
        pending_duration_frames = 0

    for w in words:
        mode = (w >> 18) & 0x3
        version = (w >> 16) & 0x3
        payload = w & 0xFFFF
        if mode != Mode.EXTENSION.value or not (payload & MUSIC_TYPE_BIT):
            raise ValueError(f"non-music temporal word encountered: {w:#x}")
        if version != DEFAULT_VERSION:
            raise ValueError(f"unsupported extension version {version}")

        kind = (payload >> KIND_SHIFT) & KIND_MASK
        data = payload & DATA_MASK

        if kind == KIND_TIME_ADVANCE:
            flush_pending()
            current_ms += int(data) * time_quant_ms
            continue

        if kind == KIND_PROGRAM:
            flush_pending()
            channel = (data >> 7) & 0xF
            program = data & 0x7F
            program_by_channel[channel] = program
            continue

        if kind == KIND_NOTE:
            flush_pending()
            channel = (data >> 7) & 0xF
            pitch = data & 0x7F
            pending_channel = channel
            pending_pitch = pitch
            pending_start_ms = current_ms
            pending_velocity = 64
            pending_duration_frames = 0
            continue

        if kind == KIND_DURATION:
            if pending_pitch is None:
                raise ValueError("duration frame encountered without a preceding note frame")
            duration_chunk = (data >> 7) & 0x1F
            velocity = data & 0x7F
            pending_duration_frames += max(1, duration_chunk)
            pending_velocity = velocity
            continue

        raise ValueError(f"unknown temporal kind {kind}")

    flush_pending()
    return out
