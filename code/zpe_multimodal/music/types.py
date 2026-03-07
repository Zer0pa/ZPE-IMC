from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, List, Optional, Sequence, Tuple

from ..diagram.quantize import DrawDir, MoveTo, StrokeCommand


@dataclass(frozen=True)
class MusicMetadata:
    time_signature: Optional[Tuple[int, int]] = None
    key_signature: Optional[int] = None  # number of sharps (negative for flats)
    tempo: Optional[float] = None  # BPM
    tempo_changes: Optional[List[Tuple[float, float]]] = None  # (onset_quarter, bpm)
    dynamic_changes: Optional[List[Tuple[float, str]]] = None  # (onset_quarter, dynamic text)
    dynamic_base: Optional[int] = None  # encoded dynamic for extension packing
    part_names: Optional[Dict[str, str]] = None
    pitch_origin: int = 0
    time_step_quarter: float = 0.25

    def with_pitch_origin(self, origin: int) -> "MusicMetadata":
        return replace(self, pitch_origin=origin)

    def with_time_step(self, step: float) -> "MusicMetadata":
        return replace(self, time_step_quarter=step)

    def with_time_signature(self, ts: Tuple[int, int]) -> "MusicMetadata":
        return replace(self, time_signature=ts)

    def with_key_signature(self, key: int) -> "MusicMetadata":
        return replace(self, key_signature=key)

    def with_tempo(self, tempo: float) -> "MusicMetadata":
        return replace(self, tempo=tempo)


@dataclass(frozen=True)
class NoteEvent:
    onset_quarter: float
    duration_quarter: float
    pitch: Optional[int]  # MIDI note number, None for rest
    part: Optional[str] = None
    voice: Optional[str] = None
    is_rest: bool = False
    tie_type: Optional[str] = None
    articulations: Optional[List[str]] = None


@dataclass(frozen=True)
class GridNote:
    start_tick: int
    duration_ticks: int
    pitch: Optional[int]
    part: Optional[str] = None
    voice: Optional[str] = None
    is_rest: bool = False
    articulations: Optional[List[str]] = None


@dataclass
class MusicGrid:
    notes: List[GridNote]
    metadata: MusicMetadata


@dataclass
class MusicStroke:
    commands: List[StrokeCommand]
    part: Optional[str] = None
    voice: Optional[str] = None
    pitch: Optional[int] = None
    is_rest: bool = False
    articulations: Optional[List[str]] = None
    time_anchor_tick: Optional[int] = None
    track_id: Optional[int] = None
