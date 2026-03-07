from __future__ import annotations

from typing import Iterable, List, Optional

from .types import PhonemeSpan, PhonemeSymbol, VoiceMetadata, VoiceTimeline


def timeline_from_phonemes(
    phonemes: Iterable[PhonemeSymbol],
    time_step_sec: float = 0.02,
    default_ticks: int = 1,
) -> VoiceTimeline:
    spans: List[PhonemeSpan] = []
    t = 0
    for ph in phonemes:
        # Heuristic pitch: stressed syllables get UP, others LEVEL
        trend = "UP" if ph.stress else None
        sym = PhonemeSymbol(symbol=ph.symbol, stress=ph.stress, pitch_trend=trend)
        spans.append(PhonemeSpan(symbol=sym, start_tick=t, duration_ticks=default_ticks))
        t += default_ticks
    meta = VoiceMetadata(time_step_sec=time_step_sec)
    return VoiceTimeline(spans=spans, metadata=meta)


def timeline_from_aligned_phonemes(
    phonemes: Iterable[PhonemeSymbol],
    alignment: List[dict],
    time_step_sec: float = 0.02,
    default_ticks: int = 1,
) -> VoiceTimeline:
    spans: List[PhonemeSpan] = []
    items = list(phonemes)
    count = min(len(items), len(alignment))
    if count == 0:
        return timeline_from_phonemes(items, time_step_sec=time_step_sec, default_ticks=default_ticks)

    for idx in range(count):
        phoneme = items[idx]
        segment = alignment[idx]
        start_sec = max(0.0, float(segment.get("start", 0.0)))
        end_sec = max(start_sec, float(segment.get("end", start_sec)))
        start_tick = max(0, int(round(start_sec / max(1e-6, time_step_sec))))
        end_tick = max(start_tick + 1, int(round(end_sec / max(1e-6, time_step_sec))))
        spans.append(
            PhonemeSpan(
                symbol=PhonemeSymbol(
                    symbol=phoneme.symbol,
                    stress=phoneme.stress,
                    pitch_trend=phoneme.pitch_trend,
                ),
                start_tick=start_tick,
                duration_ticks=max(default_ticks, end_tick - start_tick),
            )
        )
    meta = VoiceMetadata(time_step_sec=time_step_sec)
    return VoiceTimeline(spans=spans, metadata=meta)


def timeline_duration_ticks(tl: VoiceTimeline) -> int:
    end = 0
    for sp in tl.spans:
        end = max(end, sp.start_tick + sp.duration_ticks)
    return end


def apply_pitch_trends(tl: VoiceTimeline, trends: List[str]) -> VoiceTimeline:
    """Assign coarse pitch trends to spans; cycles if fewer trends than spans."""
    if not trends:
        return tl
    spans: List[PhonemeSpan] = []
    for idx, sp in enumerate(tl.spans):
        trend = trends[idx % len(trends)]
        sym = PhonemeSymbol(symbol=sp.symbol.symbol, stress=sp.symbol.stress, pitch_trend=trend)
        spans.append(PhonemeSpan(symbol=sym, start_tick=sp.start_tick, duration_ticks=sp.duration_ticks))
    return VoiceTimeline(spans=spans, metadata=tl.metadata)
