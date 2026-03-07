from __future__ import annotations

from dataclasses import dataclass, replace
from typing import List, Optional, Sequence, Tuple

from ..diagram.quantize import DrawDir, MoveTo, StrokeCommand


@dataclass(frozen=True)
class PhonemeSymbol:
    symbol: str  # ARPAbet symbol (uppercase)
    stress: bool = False
    pitch_trend: Optional[str] = None  # "UP", "DOWN", "LEVEL" or None


@dataclass(frozen=True)
class PhonemeSpan:
    symbol: PhonemeSymbol
    start_tick: int
    duration_ticks: int


@dataclass(frozen=True)
class VoiceMetadata:
    language: str = "en-us"
    time_step_sec: float = 0.02
    pitch_levels: int = 3  # quantized pitch lanes

    def with_time_step(self, step: float) -> "VoiceMetadata":
        return replace(self, time_step_sec=step)


@dataclass
class VoiceTimeline:
    spans: List[PhonemeSpan]
    metadata: VoiceMetadata


@dataclass
class VoiceStroke:
    commands: List[StrokeCommand]
    symbol: str
    stress: bool = False
    pitch_trend: Optional[str] = None
    metadata: VoiceMetadata | None = None
    time_anchor_tick: int | None = None
    formant_f1_band: int | None = None
    formant_f2_band: int | None = None
    speaking_rate_bucket: int | None = None
    emotion_valence: int | None = None
