from __future__ import annotations

from .flags import voice_enabled, voice_placeholders_enabled
from .phoneme_map import phoneme_category
from .text_to_phonemes import (
    PHONEME_SOURCE_MODES,
    phoneme_symbols_from_tokens,
    phoneme_tokens_with_mode,
    text_to_phonemes,
)
from .timeline import timeline_duration_ticks, timeline_from_aligned_phonemes, timeline_from_phonemes
from .strokes import timeline_to_strokes, strokes_to_timeline
from .audio import audio_to_strokes, audio_to_strokes_with_metadata, load_alignment
from .pack import VOICE_TYPE_BIT, pack_voice_strokes, unpack_voice_words
from .types import PhonemeSpan, PhonemeSymbol, VoiceMetadata, VoiceStroke, VoiceTimeline

__all__ = [
    "voice_enabled",
    "voice_placeholders_enabled",
    "phoneme_category",
    "PHONEME_SOURCE_MODES",
    "text_to_phonemes",
    "phoneme_tokens_with_mode",
    "phoneme_symbols_from_tokens",
    "audio_to_strokes",
    "audio_to_strokes_with_metadata",
    "load_alignment",
    "timeline_from_phonemes",
    "timeline_from_aligned_phonemes",
    "timeline_duration_ticks",
    "timeline_to_strokes",
    "strokes_to_timeline",
    "pack_voice_strokes",
    "unpack_voice_words",
    "VOICE_TYPE_BIT",
    "PhonemeSpan",
    "PhonemeSymbol",
    "VoiceMetadata",
    "VoiceStroke",
    "VoiceTimeline",
]
