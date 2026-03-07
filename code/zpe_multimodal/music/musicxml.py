from __future__ import annotations

import os
import tempfile
from collections import defaultdict
from typing import Iterable, List, Sequence

from .flags import require_music_enabled
from .grid import events_to_grid, grid_to_events
from .parser import _require_music21, musicxml_to_events
from .strokes import grid_to_strokes, strokes_to_grid
from .types import MusicGrid, MusicMetadata, MusicStroke, NoteEvent


def musicxml_to_grid(source: str, time_step_quarter: float = 0.25) -> MusicGrid:
    require_music_enabled()
    metadata, events = musicxml_to_events(source)
    return events_to_grid(events, metadata, time_step_quarter=time_step_quarter)


def musicxml_to_strokes(source: str, time_step_quarter: float = 0.25) -> List[MusicStroke]:
    grid = musicxml_to_grid(source, time_step_quarter=time_step_quarter)
    strokes = grid_to_strokes(grid)
    # attach metadata for packing if desired
    for s in strokes:
        setattr(s, "metadata", grid.metadata)
    return strokes


def _group_events_by_part(events: Iterable[NoteEvent], default_part: str = "P1"):
    grouped = defaultdict(list)
    for ev in events:
        part_id = ev.part or default_part
        grouped[part_id].append(ev)
    return grouped


def grid_to_musicxml(grid: MusicGrid) -> str:
    """Emit MusicXML from a grid using music21. Returns XML as a string."""
    require_music_enabled()
    music21 = _require_music21()
    events = grid_to_events(grid)
    grouped = _group_events_by_part(events)

    score = music21.stream.Score()
    part_names = grid.metadata.part_names or {}
    time_sig = grid.metadata.time_signature
    key_sig = grid.metadata.key_signature
    tempo = grid.metadata.tempo

    part_keys = sorted(grouped.keys())
    part_ids = {key: f"P{idx+1}" for idx, key in enumerate(part_keys)}
    part_names_resolved = {key: (part_names.get(key) if part_names else key) for key in part_keys}

    for idx, part_key in enumerate(part_keys):
        part_stream = music21.stream.Part(id=part_ids[part_key])
        if part_names_resolved:
            part_stream.partName = part_names_resolved.get(part_key, part_key)
        if time_sig:
            part_stream.insert(0, music21.meter.TimeSignature(f"{time_sig[0]}/{time_sig[1]}"))
        if key_sig is not None:
            part_stream.insert(0, music21.key.KeySignature(int(key_sig)))
        if tempo and idx == 0:
            part_stream.insert(0, music21.tempo.MetronomeMark(number=tempo))
        if grid.metadata.tempo_changes and idx == 0:
            for onset_q, bpm in grid.metadata.tempo_changes:
                part_stream.insert(onset_q, music21.tempo.MetronomeMark(number=bpm))
        if grid.metadata.dynamic_changes and idx == 0:
            for onset_q, dyn in grid.metadata.dynamic_changes:
                try:
                    part_stream.insert(onset_q, music21.dynamics.Dynamic(dyn))
                except Exception:
                    continue

        part_events = sorted(grouped[part_key], key=lambda e: (e.onset_quarter, e.pitch or -1))
        idx = 0
        while idx < len(part_events):
            onset = part_events[idx].onset_quarter
            same_onset: List = []
            while idx < len(part_events) and part_events[idx].onset_quarter == onset:
                same_onset.append(part_events[idx])
                idx += 1

            notes_here = [ev for ev in same_onset if not ev.is_rest and ev.pitch is not None]
            rests_here = [ev for ev in same_onset if ev.is_rest or ev.pitch is None]

            if notes_here:
                pitches = [ev.pitch for ev in notes_here if ev.pitch is not None]
                duration_q = max(ev.duration_quarter for ev in notes_here)
                if len(pitches) == 1:
                    note_obj = music21.note.Note(pitches[0])
                else:
                    note_obj = music21.chord.Chord(pitches)
                note_obj.duration = music21.duration.Duration(duration_q)
                voice_val = notes_here[0].voice
                if voice_val:
                    note_obj.voice = voice_val
                _apply_articulations(note_obj, notes_here[0].articulations, music21)
                part_stream.insert(onset, note_obj)

            for ev in rests_here:
                rest_obj = music21.note.Rest()
                if ev.voice:
                    rest_obj.voice = ev.voice
                rest_obj.duration = music21.duration.Duration(ev.duration_quarter)
                _apply_articulations(rest_obj, ev.articulations, music21)
                part_stream.insert(ev.onset_quarter, rest_obj)

        score.insert(0, part_stream)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".musicxml") as tmp:
        tmp_name = tmp.name
        path = score.write("musicxml", fp=tmp.name)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
        if path != tmp_name:
            try:
                os.remove(tmp_name)
            except OSError:
                pass


def strokes_to_musicxml(
    strokes: Sequence[MusicStroke],
    metadata: MusicMetadata | None = None,
    time_step_quarter: float = 0.25,
    pitch_origin: int = 0,
) -> str:
    require_music_enabled()
    grid = strokes_to_grid(
        strokes,
        time_step_quarter=time_step_quarter,
        pitch_origin=pitch_origin if metadata is None else metadata.pitch_origin,
        metadata=metadata,
    )
    return grid_to_musicxml(grid)


def _apply_articulations(note_obj, articulations, music21):
    if not articulations:
        return
    name_to_cls = {
        "Staccato": music21.articulations.Staccato,
        "Accent": music21.articulations.Accent,
        "Tenuto": music21.articulations.Tenuto,
        "Marcato": music21.articulations.Marcato,
    }
    for name in articulations:
        cls = name_to_cls.get(name)
        if cls:
            note_obj.articulations.append(cls())
