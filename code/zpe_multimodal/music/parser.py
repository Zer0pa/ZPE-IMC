from __future__ import annotations

import os
from typing import Iterable, List, Tuple

from .types import MusicMetadata, NoteEvent

try:
    import music21 as _MUSIC21  # type: ignore
except ImportError:  # pragma: no cover - exercised when missing dependency
    _MUSIC21 = None


def _require_music21():
    if _MUSIC21 is None:  # pragma: no cover - exercised when missing dependency
        raise ImportError(
            "music21 is required for Tier-3A music support. Install via `pip install music21`."
        )
    return _MUSIC21


def _load_score(source: str):
    music21 = _require_music21()
    # Path on disk takes priority; otherwise treat as inline XML.
    if os.path.exists(source):
        return music21.converter.parse(source)
    if source.lstrip().startswith("<"):
        return music21.converter.parseData(source, format="musicxml")
    return music21.converter.parse(source)


def _extract_metadata(score) -> MusicMetadata:
    music21 = _require_music21()
    time_signature = None
    key_signature = None
    tempo = None
    tempo_changes = []
    dynamic_changes = []

    ts = score.recurse().getElementsByClass(music21.meter.TimeSignature)
    first_ts = next(iter(ts), None)
    if first_ts:
        time_signature = (int(first_ts.numerator), int(first_ts.denominator))

    ks = score.recurse().getElementsByClass(music21.key.KeySignature)
    first_ks = next(iter(ks), None)
    if first_ks is not None:
        key_signature = int(first_ks.sharps)

    tempos = score.recurse().getElementsByClass(music21.tempo.MetronomeMark)
    first_tempo = next(iter(tempos), None)
    if first_tempo and first_tempo.number is not None:
        tempo = float(first_tempo.number)
    for tmark in tempos:
        if tmark.number is None:
            continue
        tempo_changes.append((float(tmark.offset), float(tmark.number)))

    dyns = score.recurse().getElementsByClass(music21.dynamics.Dynamic)
    for d in dyns:
        if getattr(d, "value", None):
            dynamic_changes.append((float(d.offset), str(d.value)))

    part_names = {}
    for idx, part in enumerate(score.parts):
        part_id = getattr(part, "id", None) or f"P{idx + 1}"
        name = getattr(part, "partName", None) or part_id
        part_names[part_id] = str(name)

    return MusicMetadata(
        time_signature=time_signature,
        key_signature=key_signature,
        tempo=tempo,
        tempo_changes=tempo_changes or None,
        dynamic_changes=dynamic_changes or None,
        part_names=part_names or None,
    )


def _events_from_part(part, part_id: str) -> Iterable[NoteEvent]:
    music21 = _require_music21()
    for element in part.flatten().notesAndRests:
        onset = float(element.offset)
        duration = float(element.duration.quarterLength)
        voice = getattr(element, "voice", None)
        voice_id = str(voice) if voice is not None else None
        articulations = None
        if getattr(element, "articulations", None):
            articulations = [type(a).__name__ for a in element.articulations]

        if element.isRest:
            yield NoteEvent(
                onset_quarter=onset,
                duration_quarter=duration,
                pitch=None,
                part=part_id,
                voice=voice_id,
                is_rest=True,
                tie_type=None,
                articulations=articulations,
            )
        elif element.isChord:
            # Flatten each pitch in the chord into its own event.
            for pitch in element.pitches:
                yield NoteEvent(
                    onset_quarter=onset,
                    duration_quarter=duration,
                    pitch=int(pitch.midi),
                    part=part_id,
                    voice=voice_id,
                    is_rest=False,
                    tie_type=getattr(element.tie, "type", None),
                    articulations=articulations,
                )
        elif element.isNote:
            tie_type = getattr(element.tie, "type", None)
            yield NoteEvent(
                onset_quarter=onset,
                duration_quarter=duration,
                pitch=int(element.pitch.midi),
                part=part_id,
                voice=voice_id,
                is_rest=False,
                tie_type=tie_type,
                articulations=articulations,
            )


def musicxml_to_events(source: str) -> Tuple[MusicMetadata, List[NoteEvent]]:
    """Parse MusicXML (path or inline XML) into note/rest events + metadata."""
    score = _load_score(source)
    metadata = _extract_metadata(score)
    events: List[NoteEvent] = []
    for idx, part in enumerate(score.parts):
        part_id = getattr(part, "id", None) or f"P{idx + 1}"
        events.extend(_events_from_part(part, part_id))
    events = _merge_ties(events)
    return metadata, events


def _merge_ties(events: List[NoteEvent]) -> List[NoteEvent]:
    """Merge tie chains into single events to stabilize quantization."""
    merged: List[NoteEvent] = []
    active = {}
    # Sort by part/voice/pitch/onset to keep chains adjacent.
    events_sorted = sorted(
        events,
        key=lambda e: (e.part or "", e.voice or "", e.pitch if e.pitch is not None else -1, e.onset_quarter),
    )
    for ev in events_sorted:
        if ev.is_rest or ev.pitch is None:
            merged.append(ev)
            continue
        key = (ev.part or "", ev.voice or "", ev.pitch)
        tie_type = (ev.tie_type or "").lower() if ev.tie_type else None
        if tie_type in ("start", "continue"):
            if key in active:
                onset, dur, arts = active[key]
                active[key] = (onset, dur + ev.duration_quarter, _merge_artics(arts, ev.articulations))
            else:
                active[key] = (ev.onset_quarter, ev.duration_quarter, ev.articulations)
            continue
        if tie_type in ("stop", "end"):
            if key in active:
                onset, dur, arts = active.pop(key)
                merged.append(
                    NoteEvent(
                        onset_quarter=onset,
                        duration_quarter=dur + ev.duration_quarter,
                        pitch=ev.pitch,
                        part=ev.part,
                        voice=ev.voice,
                        is_rest=False,
                        tie_type=None,
                        articulations=_merge_artics(arts, ev.articulations),
                    )
                )
                continue
        # No tie: flush any active chain then add this event.
        if key in active:
            onset, dur, arts = active.pop(key)
            merged.append(
                NoteEvent(
                    onset_quarter=onset,
                    duration_quarter=dur,
                    pitch=ev.pitch,
                    part=ev.part,
                    voice=ev.voice,
                    is_rest=False,
                    tie_type=None,
                    articulations=arts,
                )
            )
        merged.append(ev)

    for (part, voice, pitch), (onset, dur, arts) in active.items():
        merged.append(
            NoteEvent(
                onset_quarter=onset,
                duration_quarter=dur,
                pitch=pitch,
                part=part or None,
                voice=voice or None,
                is_rest=False,
                tie_type=None,
                articulations=arts,
            )
        )
    return merged


def _merge_artics(a, b):
    if not a:
        return b
    if not b:
        return a
    merged = list(dict.fromkeys(list(a) + list(b)))
    return merged
