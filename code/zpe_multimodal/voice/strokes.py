from __future__ import annotations

from typing import Iterable, List, Sequence

from ..diagram.quantize import DIRS, DrawDir, MoveTo
from .phoneme_map import phoneme_category
from .types import PhonemeSpan, VoiceStroke, VoiceTimeline, VoiceMetadata, PhonemeSymbol


def _phoneme_pattern(sym: str, stress: bool) -> List[int]:
    cat = phoneme_category(sym)
    if cat == "vowel":
        pattern = [0]  # R
        if stress:
            pattern = [2, 6] + pattern  # U then D bump for stress
        return pattern
    if cat == "stop":
        return [0, 6]  # R then D
    if cat == "affricate":
        return [0, 1]  # R then UR
    if cat == "fricative":
        return [0, 1]  # simple oscillation placeholder
    if cat == "nasal":
        return [0, 7]  # R then DR
    if cat == "liquid" or cat == "glide":
        return [0, 4]  # R then L
    if cat == "silence":
        return []
    return [0]


def _lane_for_pitch(trend: str | None) -> int:
    if trend == "UP":
        return -1
    if trend == "DOWN":
        return 1
    return 0


def timeline_to_strokes(timeline: VoiceTimeline) -> List[VoiceStroke]:
    strokes: List[VoiceStroke] = []
    for span in timeline.spans:
        cmds = [MoveTo(span.start_tick, _lane_for_pitch(span.symbol.pitch_trend))]
        pattern = _phoneme_pattern(span.symbol.symbol, span.symbol.stress)
        dur = max(1, span.duration_ticks)
        # expand duration by repeating R unless silence
        cat = phoneme_category(span.symbol.symbol)
        if cat != "silence":
            for _ in range(dur):
                cmds.append(DrawDir(0))
        # overlay pattern (conceptual; we append directional hints)
        for dir_idx in pattern:
            cmds.append(DrawDir(dir_idx))
        strokes.append(
            VoiceStroke(
                commands=cmds,
                symbol=span.symbol.symbol,
                stress=span.symbol.stress,
                pitch_trend=span.symbol.pitch_trend,
            )
        )
    return strokes


def strokes_to_timeline(strokes: Sequence[VoiceStroke], time_step_sec: float = 0.02) -> VoiceTimeline:
    spans: List[PhonemeSpan] = []
    for vs in strokes:
        start = None
        duration = 0
        for cmd in vs.commands:
            if isinstance(cmd, MoveTo):
                start = cmd.x
            elif isinstance(cmd, DrawDir):
                dx, _ = DIRS[cmd.direction]
                if dx > 0:
                    duration += dx
        if start is None:
            continue
        symbol = PhonemeSymbol(symbol=vs.symbol, stress=vs.stress, pitch_trend=vs.pitch_trend)
        spans.append(
            PhonemeSpan(
                symbol=symbol,
                start_tick=int(start),
                duration_ticks=max(1, duration),
            )
        )
    meta = VoiceMetadata(time_step_sec=time_step_sec)
    return VoiceTimeline(spans=spans, metadata=meta)
