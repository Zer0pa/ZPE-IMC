from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any, Sequence

from .prosody import trends_from_alignment, assign_pitch_trends
from .timeline import apply_pitch_trends, timeline_from_aligned_phonemes, timeline_from_phonemes
from .text_to_phonemes import (
    PHONEME_SOURCE_MODES,
    phoneme_symbols_from_tokens,
    phoneme_tokens_with_mode,
)
from .strokes import timeline_to_strokes


_SILENCE_LABELS = {"", "SIL", "SP", "SPN", "<EPS>", "SILENCE", "NSN"}


def _normalize_phone_label(label: str) -> str:
    token = re.sub(r"[^A-Za-z0-2]", "", str(label).upper())
    if token in _SILENCE_LABELS:
        return ""
    return token


def _coerce_segment(seg: Any) -> dict | None:
    if isinstance(seg, (list, tuple)) and len(seg) >= 3:
        start, end, label = seg[0], seg[1], seg[2]
    elif isinstance(seg, dict):
        start = seg.get("start", seg.get("begin", seg.get("xmin", seg.get("minTime", 0.0))))
        end = seg.get("end", seg.get("stop", seg.get("xmax", seg.get("maxTime", start))))
        label = seg.get("phone", seg.get("label", seg.get("text", seg.get("mark", seg.get("value", "")))))
    else:
        return None

    try:
        start_f = float(start)
        end_f = float(end)
    except Exception:
        return None
    if end_f < start_f:
        start_f, end_f = end_f, start_f
    if end_f <= start_f:
        end_f = start_f + 1e-3

    phone = _normalize_phone_label(label)
    if not phone:
        return None
    return {"phone": phone, "start": start_f, "end": end_f}


def _parse_tier_entries(tier_obj: Any) -> list[dict]:
    entries = []
    if isinstance(tier_obj, dict):
        entries = tier_obj.get("entries", tier_obj.get("intervals", tier_obj.get("items", [])))
    elif isinstance(tier_obj, list):
        entries = tier_obj

    out: list[dict] = []
    for entry in entries:
        segment = _coerce_segment(entry)
        if segment:
            out.append(segment)
    return out


def _normalize_alignment_payload(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        out = []
        for item in payload:
            segment = _coerce_segment(item)
            if segment:
                out.append(segment)
        return out

    if not isinstance(payload, dict):
        return []

    if "phones" in payload:
        return _parse_tier_entries(payload["phones"])
    if "alignment" in payload:
        return _parse_tier_entries(payload["alignment"])

    tiers = payload.get("tiers")
    if isinstance(tiers, dict):
        for key, value in tiers.items():
            if str(key).lower().startswith("phone"):
                return _parse_tier_entries(value)
        for fallback_key in ("phones", "phone"):
            if fallback_key in tiers:
                return _parse_tier_entries(tiers[fallback_key])
    return []


def load_alignment(path: str | Path) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return _normalize_alignment_payload(payload)


def load_audio_mono_with_backend(audio_path: str) -> tuple[object, int, str]:
    """Load mono audio, preferring soundfile and falling back to librosa loaders."""
    try:
        import soundfile as sf  # type: ignore

        y, sr = sf.read(audio_path, dtype="float32")
        if getattr(y, "ndim", 1) > 1:
            y = y.mean(axis=1)
        return y, int(sr), "soundfile"
    except Exception:
        try:
            import librosa  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("librosa is required for audio prosody extraction; install via pip") from exc
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        return y, int(sr), "librosa_fallback"


def audio_to_strokes(
    audio_path: str,
    transcript: str,
    alignment_path: str | None = None,
    time_step_sec: float = 0.02,
    source_mode_preference: Sequence[str] | None = None,
    return_debug: bool = False,
):
    try:
        import librosa  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("librosa is required for audio prosody extraction; install via pip") from exc

    alignment: list[dict] = []
    if alignment_path:
        alignment = load_alignment(alignment_path)

    if alignment:
        tokens = [seg["phone"] for seg in alignment if seg.get("phone")]
        phon_syms = phoneme_symbols_from_tokens(tokens)
        source_mode = "ground_truth_alignment"
    else:
        preferred = tuple(source_mode_preference or ("g2p_text", "phonemizer_optional_adapter", "deterministic_fallback"))
        tokens, source_mode = phoneme_tokens_with_mode(transcript, preferred_modes=preferred)
        phon_syms = phoneme_symbols_from_tokens(tokens)

    if not phon_syms:
        tokens, source_mode = phoneme_tokens_with_mode(transcript, preferred_modes=("deterministic_fallback",))
        phon_syms = phoneme_symbols_from_tokens(tokens)

    y, sr, backend = load_audio_mono_with_backend(audio_path)
    strict = os.environ.get("VOICE_STRICT_NO_AUDIOREAD", "0").lower() in ("1", "true", "yes", "on")
    if strict and backend != "soundfile":
        raise RuntimeError(f"strict voice decode backend requires soundfile, got {backend}")

    f0 = librosa.yin(y, fmin=50, fmax=400, sr=sr)

    if alignment and source_mode == "ground_truth_alignment":
        trends = trends_from_alignment(f0, sr, alignment)
        tl = timeline_from_aligned_phonemes(phon_syms, alignment, time_step_sec=time_step_sec)
    else:
        trends = assign_pitch_trends(f0, span_count=len(phon_syms))
        tl = timeline_from_phonemes(phon_syms, time_step_sec=time_step_sec)
    tl = apply_pitch_trends(tl, trends)
    strokes = timeline_to_strokes(tl)

    if return_debug:
        return {
            "strokes": strokes,
            "source_mode": source_mode if source_mode in PHONEME_SOURCE_MODES else "deterministic_fallback",
            "phoneme_count": len(phon_syms),
            "alignment_segment_count": len(alignment),
            "audio_backend": backend,
            "time_step_sec": float(time_step_sec),
        }
    return strokes


def audio_to_strokes_with_metadata(
    audio_path: str,
    transcript: str,
    alignment_path: str | None = None,
    time_step_sec: float = 0.02,
    source_mode_preference: Sequence[str] | None = None,
) -> dict[str, Any]:
    payload = audio_to_strokes(
        audio_path=audio_path,
        transcript=transcript,
        alignment_path=alignment_path,
        time_step_sec=time_step_sec,
        source_mode_preference=source_mode_preference,
        return_debug=True,
    )
    assert isinstance(payload, dict)
    return payload
