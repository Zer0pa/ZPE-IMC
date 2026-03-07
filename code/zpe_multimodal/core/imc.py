from __future__ import annotations

from dataclasses import dataclass, field
import gzip
import json
from numbers import Integral
from pathlib import Path
from typing import Callable, Dict, Iterable, Iterator, List, Literal, Mapping, Sequence, Tuple
import xml.etree.ElementTree as ET

import numpy as np
from scipy.io import wavfile

from .codec import decode_with_bpe, encode, encode_bpe_bridge
from .constants import DEFAULT_VERSION, Mode, PAYLOAD_16_MASK, WORD_MASK
from .imc_native import (
    get_kernel_backend_info as _get_kernel_backend_info,
    materialize_chunk_store,
    materialize_text_words,
    scan_stream_kernel,
    validate_stream_kernel,
)
from ..diagram.pack import DIAGRAM_TYPE_BIT, pack_diagram_paths, unpack_diagram_words
from ..diagram.quantize import DrawDir, MoveTo, StrokePath, polylines_to_strokes, quantize_polylines
from ..diagram.svg_io import svg_to_polylines
from ..image.dual_dispatch import decode_image_words
from ..image.quadtree_enhanced_codec import (
    IMAGE_FAMILY_MASK,
    IMAGE_FAMILY_VALUE as IMAGE_FAMILY_ENHANCED,
    encode_enhanced,
)
from ..music.pack import MUSIC_TYPE_BIT, pack_music_strokes, unpack_music_words
from ..music.parser import musicxml_to_events
from ..music.strokes import grid_to_strokes
from ..music.grid import events_to_grid
from ..music.types import MusicMetadata, MusicStroke
from ..voice.pack import VOICE_TYPE_BIT, pack_voice_strokes, unpack_voice_words
from ..voice.types import VoiceMetadata, VoiceStroke
from ..mental.codec import decode_mental, encode_mental
from ..mental.ingest import IngestResult, ingest_clinical_entry
from ..mental.pack import MENTAL_TYPE_BIT
from ..mental.types import MentalStroke
from ..touch.codec import decode_touch, encode_touch
from ..touch.pack import (
    TOUCH_TYPE_BIT,
    pack_raii_complete,
    pack_timed_simultaneous_frame,
    pack_touch_zlayers,
    unpack_raii_complete,
    unpack_timed_simultaneous_frame,
    unpack_touch_zlayers,
)
from ..touch.phase5_extensions import (
    pack_anchored_touch,
    pack_raii_frequency_sequence,
    unpack_anchored_touch,
    unpack_raii_frequency_words,
)
from ..touch.types import BodyRegion, RAIIDescriptor, TouchStroke, ensure_body_region
from ..smell.codec import decode_smell_words, encode_smell_strokes
from ..smell.adaptation import AdaptationParams
from ..smell.pack import OP_HEADER_A, OP_HEADER_B, OP_META, OP_SHIFT, SMELL_TYPE_BIT
from ..smell.phase5_augment import (
    AugmentedOdorRecord,
    pack_augmented_records,
    pack_z_episode,
    unpack_augmented_words,
    unpack_z_episode,
)
from ..smell.types import OdorStroke, SmellZLevel
from ..taste.codec import (
    decode_taste_words,
    encode_taste_events,
    load_taste_events_from_fixture,
    load_taste_words_from_manifest,
)
from ..taste.pack import TASTE_TYPE_BIT
from ..taste.types import TasteEvent
from ..text.mapping_v1 import WORD_TO_CHAR

BPE_TYPE_BIT = 0x1000
# IMC image encoding path emits enhanced image family words (0x0400).
# Legacy family words (0x0800) collide with touch's top-bit and are decoded
# through image-specific APIs, not IMC mixed streams.
_IMAGE_FAMILY_VALUES = {IMAGE_FAMILY_ENHANCED}


@dataclass
class IMCResult:
    text: str
    diagram_blocks: List[List[StrokePath]]
    music_blocks: List[Tuple[MusicMetadata | None, List[MusicStroke]]]
    voice_blocks: List[List[VoiceStroke]]
    mental_blocks: List[Tuple[dict | None, List[MentalStroke]]]
    touch_blocks: List[Tuple[dict | None, List[TouchStroke]]]
    smell_blocks: List[Tuple[dict | None, List[OdorStroke]]]
    taste_blocks: List[Tuple[dict | None, List[TasteEvent]]]
    image_blocks: List[np.ndarray]
    bpe_tokens: List[int]
    word_count: int
    modality_counts: Dict[str, int]
    stream_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


def _is_enabled(env_name: str) -> bool:
    import os

    return os.environ.get(env_name, "").lower() in ("1", "true", "yes", "on")


def _require_enabled_flags() -> None:
    missing = [
        name
        for name in (
            "STROKEGRAM_ENABLE_DIAGRAM",
            "STROKEGRAM_ENABLE_MUSIC",
            "STROKEGRAM_ENABLE_VOICE",
        )
        if not _is_enabled(name)
    ]
    if missing:
        missing_str = ", ".join(missing)
        raise RuntimeError(f"IMC requires enabled modality flags. Missing: {missing_str}")


def _is_image_payload(payload: int) -> bool:
    return (payload & IMAGE_FAMILY_MASK) in _IMAGE_FAMILY_VALUES


def _word_fields(word: int) -> tuple[int, int, int]:
    mode = (word >> 18) & 0x3
    version = (word >> 16) & 0x3
    payload = word & PAYLOAD_16_MASK
    return mode, version, payload


def _is_taste_extension_word(word: int) -> bool:
    mode, _version, payload = _word_fields(word)
    return mode == Mode.EXTENSION.value and bool(payload & TASTE_TYPE_BIT)


def _taste_sequence_length_in_stream(stream: Sequence[int], start_idx: int) -> int:
    """Detect a canonical taste z-layer sequence at index and return word span."""
    if start_idx + 2 >= len(stream):
        return 0

    def _coerce(index: int) -> int | None:
        if index < 0 or index >= len(stream):
            return None
        word = stream[index]
        if not isinstance(word, int):
            return None
        if word < 0 or word > WORD_MASK:
            return None
        return int(word)

    w0 = _coerce(start_idx)
    w1 = _coerce(start_idx + 1)
    w2 = _coerce(start_idx + 2)
    if w0 is None or w1 is None or w2 is None:
        return 0

    m0, v0, p0 = _word_fields(w0)
    m1, v1, p1 = _word_fields(w1)
    m2, v2, p2 = _word_fields(w2)
    if (
        m0 != Mode.EXTENSION.value
        or v0 != 0
        or not (p0 & TASTE_TYPE_BIT)
        or m1 != Mode.EXTENSION.value
        or v1 != 1
        or not (p1 & TASTE_TYPE_BIT)
        or m2 != Mode.EXTENSION.value
        or v2 != 2
        or not (p2 & TASTE_TYPE_BIT)
    ):
        return 0

    j = start_idx + 3
    while j < len(stream):
        wj = _coerce(j)
        if wj is None:
            break
        mj, vj, pj = _word_fields(wj)
        if mj == Mode.EXTENSION.value and (pj & TASTE_TYPE_BIT) and vj in (2, 3):
            j += 1
            continue
        break
    return j - start_idx


def _classify_word(word: int) -> Literal[
    "text",
    "diagram",
    "music",
    "voice",
    "image",
    "bpe",
    "mental",
    "touch",
    "smell",
    "taste",
]:
    """Classify a 20-bit word into a modality label.

    Mental words intentionally span two modes:
    - Mode 3 (`Mode.RESERVED`) for mental control/header words.
    - Mode 2 (`Mode.EXTENSION`) for mental draw direction words.

    Collision guards run sensation checks before image dispatch, but only when
    payloads are not marked as image-family words.
    """
    mode, version, payload = _word_fields(word)
    if mode == Mode.RESERVED.value and (payload & MENTAL_TYPE_BIT):
        return "mental"
    if mode != Mode.EXTENSION.value:
        return "text"
    if payload & MUSIC_TYPE_BIT:
        return "music"
    if payload & VOICE_TYPE_BIT:
        return "voice"
    if payload & DIAGRAM_TYPE_BIT:
        return "diagram"
    if payload & BPE_TYPE_BIT:
        return "bpe"
    # Taste shares image's 0x0400 family bit and also collides with touch
    # control payload data. Canonical taste dispatch is handled by
    # `_taste_sequence_length_in_stream`, so standalone words are not claimed
    # here.
    # Sensation checks are before image dispatch, but gated to avoid
    # collisions with image family payloads.
    if (payload & TOUCH_TYPE_BIT) and not _is_image_payload(payload):
        return "touch"
    if (payload & SMELL_TYPE_BIT) and not _is_image_payload(payload):
        return "smell"
    if (payload & MENTAL_TYPE_BIT) and not _is_image_payload(payload):
        return "mental"
    if _is_image_payload(payload):
        return "image"
    # Includes emoji extension words (no high type bit) and any generic extension payload.
    return "text"


def _direction_for_delta(dx: int, dy: int) -> int:
    if dx > 0 and dy < 0:
        return 1
    if dx > 0 and dy > 0:
        return 7
    if dx > 0:
        return 0
    if dy < 0:
        return 2
    if dy > 0:
        return 6
    return 0


def _wav_to_voice_strokes(wav_path: str | Path) -> Tuple[List[VoiceStroke], VoiceMetadata]:
    """Convert WAV audio to a single contour using frame RMS energy levels.

    The Y-axis is an 8-level (0-7) normalized RMS energy contour. This is a
    deterministic fallback used when true F0 extraction tooling is unavailable.
    """
    sr, samples = wavfile.read(str(wav_path))
    if getattr(samples, "ndim", 1) > 1:
        samples = samples.mean(axis=1)
    arr = np.asarray(samples, dtype=np.float64)
    if arr.size == 0:
        return [], VoiceMetadata(language="en-us", time_step_sec=0.02, pitch_levels=8)

    peak = float(np.max(np.abs(arr)))
    if peak > 0:
        arr = arr / peak

    frame = max(128, arr.size // 64)
    energies: List[float] = []
    for i in range(0, arr.size, frame):
        chunk = arr[i : i + frame]
        if chunk.size == 0:
            continue
        energies.append(float(np.sqrt(np.mean(chunk**2))))

    if not energies:
        energies = [0.0]

    e_min = min(energies)
    e_max = max(energies)
    denom = (e_max - e_min) if (e_max - e_min) > 1e-12 else 1.0
    levels = [int(round(((e - e_min) / denom) * 7.0)) for e in energies]

    commands = [MoveTo(0, levels[0])]
    prev = levels[0]
    for lvl in levels[1:]:
        dy = -1 if lvl > prev else (1 if lvl < prev else 0)
        commands.append(DrawDir(_direction_for_delta(1, dy)))
        prev = lvl

    metadata = VoiceMetadata(language="en-us", time_step_sec=float(frame) / float(sr), pitch_levels=8)
    stroke = VoiceStroke(commands=commands, symbol="AA", stress=False, metadata=metadata)
    return [stroke], metadata


def _coerce_voice_payload(
    voice_input: str | Path | Iterable[VoiceStroke],
    metadata: VoiceMetadata | None,
) -> tuple[List[VoiceStroke], VoiceMetadata | None]:
    if isinstance(voice_input, (str, Path)):
        return _wav_to_voice_strokes(voice_input)

    strokes = list(voice_input)
    for stroke in strokes:
        if not isinstance(stroke, VoiceStroke):
            raise TypeError(f"expected VoiceStroke, got {type(stroke)!r}")

    resolved_metadata = metadata
    if resolved_metadata is None:
        for stroke in strokes:
            if stroke.metadata is not None:
                resolved_metadata = stroke.metadata
                break
    return strokes, resolved_metadata


def _coerce_mental_strokes(strokes: Iterable[MentalStroke] | Iterable[IngestResult] | Iterable[Mapping[str, object]]) -> List[MentalStroke]:
    if isinstance(strokes, Mapping):
        source_items: Iterable[object] = [strokes]
    else:
        source_items = strokes

    coerced: List[MentalStroke] = []
    for item in source_items:
        if isinstance(item, MentalStroke):
            coerced.append(item)
            continue
        if isinstance(item, IngestResult):
            coerced.append(item.stroke)
            continue
        if isinstance(item, Mapping):
            coerced.append(ingest_clinical_entry(item).stroke)
            continue
        raise TypeError(f"expected MentalStroke, IngestResult, or mapping, got {type(item)!r}")
    return coerced


def _coerce_touch_strokes(strokes: Iterable[TouchStroke] | TouchStroke) -> List[TouchStroke]:
    if isinstance(strokes, TouchStroke):
        return [strokes]
    coerced = list(strokes)
    for stroke in coerced:
        if not isinstance(stroke, TouchStroke):
            raise TypeError(f"expected TouchStroke, got {type(stroke)!r}")
    return coerced


def _coerce_raii_descriptor(value: object) -> RAIIDescriptor:
    if isinstance(value, RAIIDescriptor):
        return value
    if isinstance(value, Mapping):
        return RAIIDescriptor(
            frequency_band=int(value["frequency_band"]),
            amplitude=int(value["amplitude"]),
            envelope=int(value["envelope"]),
        )
    raise TypeError(f"expected RAIIDescriptor or mapping, got {type(value)!r}")


def _coerce_raii_complete_entries(raw: object) -> List[tuple[BodyRegion, RAIIDescriptor]]:
    if raw is None:
        return []

    entries: List[tuple[BodyRegion, RAIIDescriptor]] = []
    for item in raw:
        if isinstance(item, Mapping):
            region = ensure_body_region(int(item["region"]))
            descriptor_obj = item.get("descriptor")
            if descriptor_obj is None:
                descriptor = RAIIDescriptor(
                    frequency_band=int(item["frequency_band"]),
                    amplitude=int(item["amplitude"]),
                    envelope=int(item["envelope"]),
                )
            else:
                descriptor = _coerce_raii_descriptor(descriptor_obj)
            entries.append((region, descriptor))
            continue

        region_obj, descriptor_obj = item
        entries.append((ensure_body_region(int(region_obj)), _coerce_raii_descriptor(descriptor_obj)))
    return entries


def _coerce_raii_frequency_sequences(raw: object) -> List[tuple[BodyRegion, List[int]]]:
    if raw is None:
        return []

    if isinstance(raw, Mapping):
        items = raw.items()
    else:
        items = raw

    sequences: List[tuple[BodyRegion, List[int]]] = []
    for item in items:
        if isinstance(item, Mapping):
            region = ensure_body_region(int(item["region"]))
            bands = [int(band) for band in item["bands"]]
            sequences.append((region, bands))
            continue

        region_obj, bands_obj = item
        region = ensure_body_region(int(region_obj))
        bands = [int(band) for band in bands_obj]
        sequences.append((region, bands))
    return sequences


def _encode_touch_block(strokes: List[TouchStroke], metadata: Mapping[str, object] | None) -> List[int]:
    if not metadata:
        return encode_touch(strokes, metadata=None)

    if "frame_id" in metadata and "anchor_offset" in metadata:
        raise ValueError("touch block cannot encode frame_id and anchor_offset together")

    if "frame_id" in metadata:
        deltas = metadata.get("time_deltas_ms")
        if deltas is None:
            raise ValueError("timed touch block requires time_deltas_ms")
        words = pack_timed_simultaneous_frame(
            frame_id=int(metadata["frame_id"]),
            contacts=strokes,
            deltas_ms=[int(delta) for delta in deltas],
        )
    elif "anchor_offset" in metadata:
        if len(strokes) != 1:
            raise ValueError("anchored touch block requires exactly one TouchStroke")
        offset_x, offset_y = metadata["anchor_offset"]
        words = pack_anchored_touch(strokes[0], offset=(int(offset_x), int(offset_y)))
    else:
        words = encode_touch(strokes, metadata=dict(metadata))

    for region, descriptor in _coerce_raii_complete_entries(metadata.get("raii_complete")):
        words.extend(pack_raii_complete(region, descriptor))

    for region, bands in _coerce_raii_frequency_sequences(metadata.get("raii_frequency_sequences")):
        words.extend(pack_raii_frequency_sequence(region, bands))

    z_layers = metadata.get("z_layers")
    if isinstance(z_layers, Mapping):
        z_region = ensure_body_region(int(z_layers["region"]))
        words.extend(
            pack_touch_zlayers(
                directions=[int(direction) for direction in z_layers.get("directions", [])],
                pressures=[int(pressure) for pressure in z_layers.get("pressures", [])],
                region=z_region,
            )
        )

    return words


def _coerce_smell_payload(
    strokes: Iterable[OdorStroke] | Iterable[AugmentedOdorRecord] | OdorStroke | AugmentedOdorRecord,
) -> tuple[List[OdorStroke], List[AugmentedOdorRecord]]:
    if isinstance(strokes, AugmentedOdorRecord):
        return [], [strokes]
    if isinstance(strokes, OdorStroke):
        return [strokes], []

    items = list(strokes)
    if not items:
        return [], []

    if all(isinstance(item, AugmentedOdorRecord) for item in items):
        return [], list(items)
    if all(isinstance(item, OdorStroke) for item in items):
        return list(items), []
    raise TypeError("smell block must contain either OdorStroke values or AugmentedOdorRecord values")


def _coerce_adaptation(value: object) -> AdaptationParams | None:
    if value is None:
        return None
    if isinstance(value, AdaptationParams):
        return value
    if isinstance(value, Mapping):
        return AdaptationParams(half_life=int(value["half_life"]), floor=int(value["floor"]))
    raise TypeError(f"expected AdaptationParams or mapping, got {type(value)!r}")


def _encode_smell_block(
    strokes: Iterable[OdorStroke] | Iterable[AugmentedOdorRecord] | OdorStroke | AugmentedOdorRecord,
    metadata: Mapping[str, object] | None,
) -> List[int]:
    base_strokes, augmented_records = _coerce_smell_payload(strokes)
    if augmented_records:
        if metadata and "z_level" in metadata:
            z_level = metadata["z_level"]
            if not isinstance(z_level, SmellZLevel):
                z_level = SmellZLevel(int(z_level))
            return pack_z_episode(
                augmented_records,
                z_level=z_level,
                adaptation=_coerce_adaptation(metadata.get("adaptation")),
            )
        return pack_augmented_records(augmented_records)
    return encode_smell_strokes(base_strokes, metadata=dict(metadata) if metadata else None)


def _smell_word_parts(word: int) -> tuple[int, int] | None:
    mode = (word >> 18) & 0x3
    version = (word >> 16) & 0x3
    payload = word & PAYLOAD_16_MASK
    if mode != Mode.EXTENSION.value or version != DEFAULT_VERSION or not (payload & SMELL_TYPE_BIT):
        return None
    return (payload >> OP_SHIFT) & 0x3, payload & 0x3F


def _looks_like_smell_z_episode(words: Sequence[int]) -> bool:
    if len(words) < 3:
        return False

    header = _smell_word_parts(words[0])
    half = _smell_word_parts(words[1])
    floor = _smell_word_parts(words[2])
    if header is None or half is None or floor is None:
        return False
    if header[0] != OP_META or half[0] != OP_META or floor[0] != OP_META:
        return False
    return (header[1] & 0x30) == 0x30 and (half[1] & 0x30) == 0x20 and (floor[1] & 0x30) == 0x10


def _looks_like_augmented_smell_chunk(words: Sequence[int]) -> bool:
    idx = 0
    while idx < len(words):
        first = _smell_word_parts(words[idx])
        if first is None:
            idx += 1
            continue
        if first[0] == OP_META:
            idx += 1
            continue
        if first[0] != OP_HEADER_A or idx + 1 >= len(words):
            idx += 1
            continue
        second = _smell_word_parts(words[idx + 1])
        if second is None or second[0] != OP_HEADER_B:
            idx += 1
            continue
        cursor = idx + 2 + (second[1] & 0x7)
        meta_after = _smell_word_parts(words[cursor]) if cursor < len(words) else None
        if meta_after is not None and meta_after[0] == OP_META:
            return True
        idx = cursor
    return False


def _decode_touch_block(words: List[int]) -> tuple[dict | None, List[TouchStroke]]:
    metadata, strokes = decode_touch(words)
    decoded_meta: dict = dict(metadata or {})

    try:
        frame_meta, contacts = unpack_timed_simultaneous_frame(words)
    except Exception:
        contacts = []
    else:
        decoded_meta["timed_frame"] = {
            **frame_meta,
            "deltas_ms": [int(delta_ms) for delta_ms, _stroke in contacts],
            "contact_regions": [int(stroke.region) for _delta_ms, stroke in contacts],
        }

    try:
        anchor_meta, anchored = unpack_anchored_touch(words)
    except Exception:
        anchored = None
    else:
        if anchored is not None and anchor_meta.get("decoded"):
            decoded_meta["anchored_touch"] = {
                "anchor": anchored.anchor,
                "region": int(anchored.region),
            }

    raii_complete = unpack_raii_complete(words)
    if raii_complete:
        decoded_meta["raii_complete"] = [
            {
                "region": int(region),
                "descriptor": {
                    "frequency_band": descriptor.frequency_band,
                    "amplitude": descriptor.amplitude,
                    "envelope": descriptor.envelope,
                },
            }
            for region, descriptor in raii_complete
        ]

    raii_samples = unpack_raii_frequency_words(words)
    if raii_samples:
        decoded_meta["raii_frequency_samples"] = [
            {"region": int(sample.region), "band": sample.band} for sample in raii_samples
        ]

    z_layers = unpack_touch_zlayers(words)
    if z_layers["surface"] or z_layers["dermal"] or z_layers["anatomical_values"] or z_layers["proprioceptive_values"]:
        decoded_meta["z_layers"] = {
            "surface": list(z_layers["surface"]),
            "dermal": list(z_layers["dermal"]),
            "anatomical_region": (
                int(z_layers["anatomical_region"]) if z_layers["anatomical_region"] is not None else None
            ),
            "proprioceptive_values": list(z_layers["proprioceptive_values"]),
        }

    return (decoded_meta or None), strokes


def _decode_smell_block(words: List[int]) -> tuple[dict | None, List[OdorStroke]]:
    metadata, strokes = decode_smell_words(words)
    decoded_meta: dict = dict(metadata or {})

    if _looks_like_smell_z_episode(words):
        z_level, adaptation, records = unpack_z_episode(words)
        if records:
            decoded_meta["z_level"] = z_level.name.lower()
            if adaptation is not None:
                decoded_meta["adaptation"] = {
                    "half_life": adaptation.half_life,
                    "floor": adaptation.floor,
                }
            decoded_meta["augmented_records"] = records
            return decoded_meta, [record.stroke for record in records]

    if _looks_like_augmented_smell_chunk(words):
        records = unpack_augmented_words(words)
        if records:
            decoded_meta["augmented_records"] = records
            return decoded_meta, [record.stroke for record in records]

    return (decoded_meta or None), strokes


def _pitch_to_midi(step: str, octave: int, alter: int = 0) -> int:
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}.get(step.upper(), 0)
    return int((octave + 1) * 12 + base + alter)


def _fallback_musicxml_to_strokes(musicxml_path: str | Path) -> Tuple[List[MusicStroke], MusicMetadata]:
    tree = ET.parse(str(musicxml_path))
    root = tree.getroot()

    def strip(tag: str) -> str:
        return tag.split("}", 1)[-1]

    divisions = 1
    current_tick = 0
    strokes: List[MusicStroke] = []
    metadata = MusicMetadata()

    for elem in root.iter():
        name = strip(elem.tag)
        if name == "divisions":
            try:
                divisions = max(1, int((elem.text or "1").strip()))
            except ValueError:
                divisions = 1
        elif name == "time":
            beats = None
            beat_type = None
            for child in list(elem):
                child_name = strip(child.tag)
                if child_name == "beats":
                    beats = child.text
                elif child_name == "beat-type":
                    beat_type = child.text
            if beats and beat_type:
                try:
                    metadata = metadata.with_time_signature((int(beats), int(beat_type)))
                except Exception:
                    pass

    for note in root.iter():
        if strip(note.tag) != "note":
            continue

        duration_text = note.findtext(".//duration", default="1")
        try:
            duration_div = max(1, int(float(duration_text)))
        except ValueError:
            duration_div = 1

        quarter = max(1, int(round(duration_div / max(1, divisions))))
        is_rest = note.find(".//rest") is not None
        if is_rest:
            midi = 60
        else:
            step = note.findtext(".//step", default="C")
            octave_text = note.findtext(".//octave", default="4")
            alter_text = note.findtext(".//alter", default="0")
            try:
                octave = int(octave_text)
            except ValueError:
                octave = 4
            try:
                alter = int(alter_text)
            except ValueError:
                alter = 0
            midi = _pitch_to_midi(step, octave, alter=alter)

        commands = [MoveTo(current_tick, int(midi))]
        for _ in range(quarter):
            commands.append(DrawDir(0))
        anchor_tick = current_tick if 0 <= current_tick <= 0x7F else None
        strokes.append(
            MusicStroke(
                commands=commands,
                pitch=None if is_rest else int(midi),
                is_rest=is_rest,
                time_anchor_tick=anchor_tick,
            )
        )
        current_tick += quarter

    return strokes, metadata


class IMCEncoder:
    """Encode multimodal content into a single unified stream."""

    def __init__(self, *, require_env: bool = True):
        if require_env:
            _require_enabled_flags()
        self._stream: List[int] = []

    def _extend_checked(self, words: Sequence[int], modality: str) -> None:
        required_type_bit = 0
        allow_reserved_mode = False
        validate_image_family = False
        validate_taste_version = False
        if modality == "diagram":
            required_type_bit = DIAGRAM_TYPE_BIT
        elif modality == "music":
            required_type_bit = MUSIC_TYPE_BIT
        elif modality == "voice":
            required_type_bit = VOICE_TYPE_BIT
        elif modality == "image":
            validate_image_family = True
        elif modality == "bpe":
            required_type_bit = BPE_TYPE_BIT
        elif modality == "mental":
            required_type_bit = MENTAL_TYPE_BIT
            allow_reserved_mode = True
        elif modality == "touch":
            required_type_bit = TOUCH_TYPE_BIT
        elif modality == "smell":
            required_type_bit = SMELL_TYPE_BIT
        elif modality == "taste":
            required_type_bit = TASTE_TYPE_BIT
            validate_taste_version = True
        else:
            raise ValueError(f"unsupported modality for extension validation: {modality}")

        extension_mode = Mode.EXTENSION.value
        reserved_mode = Mode.RESERVED.value
        for word in words:
            if not isinstance(word, int):
                raise TypeError(f"{modality} encoder produced non-int word: {word!r}")
            if word < 0 or word > WORD_MASK:
                raise ValueError(f"{modality} encoder produced out-of-range word: {word}")
            mode, version, payload = _word_fields(word)
            if mode != extension_mode and not (allow_reserved_mode and mode == reserved_mode):
                if allow_reserved_mode:
                    raise ValueError(f"{modality} encoder produced unsupported mode word: {word:#x}")
                raise ValueError(f"{modality} encoder produced non-extension word: {word:#x}")
            if required_type_bit and not (payload & required_type_bit):
                raise ValueError(f"{modality} word missing {modality} type bit: {word:#x}")
            if validate_taste_version and version not in (0, 1, 2, 3):
                raise ValueError(f"taste word has unsupported version: {word:#x}")
            if validate_image_family and not _is_image_payload(payload):
                raise ValueError(f"image word missing image family marker: {word:#x}")
        self._stream.extend(words)

    def add_text(self, text: str) -> "IMCEncoder":
        """Append core text words to the stream."""
        self._stream.extend(encode(text))
        return self

    def add_svg(self, svg_string: str, canvas_size: int = 256) -> "IMCEncoder":
        """Append an SVG diagram as diagram extension words."""
        try:
            polylines = svg_to_polylines(svg_string, canvas_size=canvas_size)
        except Exception as exc:
            raise ValueError(f"failed to parse SVG input: {exc}") from exc
        paths = polylines_to_strokes(quantize_polylines(polylines))
        words = pack_diagram_paths(paths, canvas_size=canvas_size, encode_styles=True)
        self._extend_checked(words, "diagram")
        return self

    def add_music(self, musicxml_path: str | Path) -> "IMCEncoder":
        """Append a MusicXML document as music extension words."""
        src = str(musicxml_path)
        try:
            metadata, events = musicxml_to_events(src)
            grid = events_to_grid(events, metadata)
            strokes = grid_to_strokes(grid, preserve_time_anchors=True)
            words = pack_music_strokes(strokes, metadata=metadata)
        except Exception:
            strokes, metadata = _fallback_musicxml_to_strokes(src)
            words = pack_music_strokes(strokes, metadata=metadata)
        self._extend_checked(words, "music")
        return self

    def add_voice(
        self,
        voice_input: str | Path | Iterable[VoiceStroke],
        metadata: VoiceMetadata | None = None,
    ) -> "IMCEncoder":
        """Append either WAV-derived voice contours or promoted voice strokes."""
        strokes, metadata = _coerce_voice_payload(voice_input, metadata)
        words = pack_voice_strokes(strokes, metadata=metadata)
        self._extend_checked(words, "voice")
        return self

    def add_image(self, image_array: np.ndarray, bits: int = 3) -> "IMCEncoder":
        """Append an RGB (or grayscale) image as image extension words."""
        arr = np.asarray(image_array)
        if arr.ndim == 2:
            arr = np.repeat(arr[:, :, None], 3, axis=2)
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError("image_array must have shape (H, W, 3) or (H, W)")
        words, _meta = encode_enhanced(arr.astype(np.uint8), bit_depth=bits)
        self._extend_checked(words, "image")
        return self

    def add_bpe(self, tokens: Iterable[int]) -> "IMCEncoder":
        """Append BPE bridge tokens as extension words."""
        words = encode_bpe_bridge(tokens)
        self._extend_checked(words, "bpe")
        return self

    def add_mental(
        self,
        strokes: Iterable[MentalStroke] | Iterable[IngestResult] | Iterable[Mapping[str, object]],
        metadata: dict | None = None,
    ) -> "IMCEncoder":
        """Append mental modality extension words."""
        words = encode_mental(_coerce_mental_strokes(strokes), metadata=metadata)
        self._extend_checked(words, "mental")
        return self

    def add_touch(
        self,
        strokes: Iterable[TouchStroke] | TouchStroke,
        metadata: dict | None = None,
    ) -> "IMCEncoder":
        """Append touch modality extension words."""
        words = _encode_touch_block(_coerce_touch_strokes(strokes), metadata=metadata)
        self._extend_checked(words, "touch")
        return self

    def add_smell(
        self,
        strokes: Iterable[OdorStroke] | Iterable[AugmentedOdorRecord] | OdorStroke | AugmentedOdorRecord,
        metadata: dict | None = None,
    ) -> "IMCEncoder":
        """Append smell modality extension words."""
        words = _encode_smell_block(strokes, metadata=metadata)
        self._extend_checked(words, "smell")
        return self

    def add_taste(self, words: Iterable[int]) -> "IMCEncoder":
        """Append taste z-layer words already encoded with taste type bit."""
        packed = [int(word) for word in words]
        self._extend_checked(packed, "taste")
        return self

    def add_taste_events(self, events: Iterable[TasteEvent]) -> "IMCEncoder":
        """Append promoted taste events and let IMC own the packing path."""
        words = encode_taste_events(events)
        self._extend_checked(words, "taste")
        return self

    def add_taste_from_manifest(
        self,
        manifest_path: str | Path,
        *,
        corpus: Literal["minimum_closure", "expanded", "minimum_closure_corpus", "expanded_corpus"] = "minimum_closure",
    ) -> "IMCEncoder":
        """Append taste words loaded from the validated taste handoff corpus."""
        words = load_taste_words_from_manifest(manifest_path, corpus=corpus)
        self._extend_checked(words, "taste")
        return self

    def add_taste_fixture(self, fixture_path: str | Path) -> "IMCEncoder":
        """Append promoted taste events loaded from a canonical fixture."""
        return self.add_taste_events(load_taste_events_from_fixture(fixture_path))

    def build(self) -> List[int]:
        """Return a validated copy of the current unified stream."""
        valid, errors = validate_stream(self._stream)
        if not valid:
            raise ValueError(f"invalid stream build: {'; '.join(errors)}")
        return list(self._stream)

    def reset(self) -> "IMCEncoder":
        """Clear the stream and return self for fluent reuse."""
        self._stream.clear()
        return self


_CHUNK_MODALITIES = ("diagram", "music", "voice", "image", "mental", "touch", "smell", "taste")


def _new_modality_counts() -> Dict[str, int]:
    return {
        "text": 0,
        "diagram": 0,
        "music": 0,
        "voice": 0,
        "image": 0,
        "bpe": 0,
        "mental": 0,
        "touch": 0,
        "smell": 0,
        "taste": 0,
    }


def _new_chunk_store() -> Dict[str, List[List[int]]]:
    return {key: [] for key in _CHUNK_MODALITIES}


def _flush_current_chunk(
    *,
    chunk_store: Dict[str, List[List[int]]],
    current_type: str | None,
    current_chunk: List[int],
) -> tuple[str | None, List[int]]:
    if current_type and current_chunk:
        chunk_store[current_type].append(current_chunk)
    return None, []


def _segment_stream_by_modality(stream: Sequence[int]) -> tuple[Dict[str, int], List[int], Dict[str, List[List[int]]]]:
    scan = scan_stream_kernel(stream)
    return dict(scan.counts), materialize_text_words(scan), materialize_chunk_store(scan)


def _decode_chunk_blocks(
    chunks: Sequence[Sequence[int]],
    decoder: Callable[[Sequence[int]], object],
    fallback: Callable[[], object],
) -> List[object]:
    decoded: List[object] = []
    for words in chunks:
        try:
            decoded.append(decoder(words))
        except Exception:
            decoded.append(fallback())
    return decoded


def _decode_image_blocks(chunks: Sequence[Sequence[int]]) -> List[np.ndarray]:
    image_blocks: List[np.ndarray] = []
    for words in chunks:
        try:
            image_blocks.append(decode_image_words(words).image)
        except Exception:
            continue
    return image_blocks


def _decode_text_words_safe(text_words: Sequence[int], errors: List[str]) -> tuple[str, List[int], bool]:
    """Decode text words with a dirty-data fallback that never raises.

    Returns `(text, bpe_tokens, used_fallback)`.
    """
    try:
        text, bpe_tokens = decode_with_bpe(text_words)
        return text, bpe_tokens, False
    except Exception as exc:
        errors.append(f"text_decode_error: {exc}")

    # Fallback path: keep only syntactically safe text/BPE words.
    safe_text_words: List[int] = []
    for idx, word in enumerate(text_words):
        mode = (word >> 18) & 0x3
        payload = word & PAYLOAD_16_MASK
        version = (word >> 16) & 0x3
        keep = False

        if mode == Mode.NORMAL.value:
            keep = version == DEFAULT_VERSION and (word in WORD_TO_CHAR)
        elif mode == Mode.ESCAPE.value:
            keep = version == DEFAULT_VERSION
        elif mode == Mode.EXTENSION.value:
            keep = bool(payload & BPE_TYPE_BIT)

        if not keep:
            errors.append(f"index {idx}: dropped malformed text word {word:#x}")
            continue
        safe_text_words.append(word)

    if not safe_text_words:
        return "", [], True

    try:
        text, bpe_tokens = decode_with_bpe(safe_text_words)
        return text, bpe_tokens, True
    except Exception as exc:
        errors.append(f"text_decode_fallback_error: {exc}")
        return "", [], True


class IMCDecoder:
    """Decode a unified multimodal stream into structured modality outputs."""

    def decode(self, stream: Sequence[int]) -> IMCResult:
        """Decode a stream into text, modality blocks, counts, and validation state."""
        scan = scan_stream_kernel(stream, record_invalid=True)
        errors = scan.validation_errors
        valid = len(errors) == 0
        counts = dict(scan.counts)
        text_words = scan.text_words
        chunk_store = scan.chunk_store

        text, bpe_tokens, used_fallback = _decode_text_words_safe(text_words, errors)
        if used_fallback:
            valid = False

        diagram_blocks = _decode_chunk_blocks(
            chunk_store["diagram"],
            decoder=unpack_diagram_words,
            fallback=lambda: [],
        )
        music_blocks = _decode_chunk_blocks(
            chunk_store["music"],
            decoder=unpack_music_words,
            fallback=lambda: (None, []),
        )
        voice_blocks = _decode_chunk_blocks(
            chunk_store["voice"],
            decoder=unpack_voice_words,
            fallback=lambda: [],
        )
        mental_blocks = _decode_chunk_blocks(
            chunk_store["mental"],
            decoder=decode_mental,
            fallback=lambda: (None, []),
        )
        touch_blocks = _decode_chunk_blocks(
            chunk_store["touch"],
            decoder=_decode_touch_block,
            fallback=lambda: (None, []),
        )
        smell_blocks = _decode_chunk_blocks(
            chunk_store["smell"],
            decoder=_decode_smell_block,
            fallback=lambda: (None, []),
        )
        taste_blocks = _decode_chunk_blocks(
            chunk_store["taste"],
            decoder=decode_taste_words,
            fallback=lambda: (None, []),
        )
        image_blocks = _decode_image_blocks(chunk_store["image"])

        return IMCResult(
            text=text,
            diagram_blocks=diagram_blocks,
            music_blocks=music_blocks,
            voice_blocks=voice_blocks,
            mental_blocks=mental_blocks,
            touch_blocks=touch_blocks,
            smell_blocks=smell_blocks,
            taste_blocks=taste_blocks,
            image_blocks=image_blocks,
            bpe_tokens=bpe_tokens,
            word_count=len(stream),
            modality_counts=counts,
            stream_valid=valid,
            validation_errors=errors,
        )


def validate_stream(stream: Sequence[int]) -> Tuple[bool, List[str]]:
    return validate_stream_kernel(stream)


def get_kernel_backend_info() -> Dict[str, object]:
    return dict(_get_kernel_backend_info())


def _coerce_helper_word(word: object) -> int | None:
    if isinstance(word, bool):
        return None
    if not isinstance(word, Integral):
        return None
    value = int(word)
    if value < 0 or value > WORD_MASK:
        return None
    return value


def _valid_helper_words(stream: Sequence[object]) -> List[int]:
    valid_words: List[int] = []
    for word in stream:
        coerced = _coerce_helper_word(word)
        if coerced is None:
            continue
        valid_words.append(coerced)
    return valid_words


def _iter_classified_words(stream: Sequence[object]) -> Iterator[tuple[str, int]]:
    index = 0
    while index < len(stream):
        word = stream[index]
        coerced = _coerce_helper_word(word)
        if coerced is None:
            index += 1
            continue

        taste_len = _taste_sequence_length_in_stream(stream, index)
        if taste_len > 0:
            for offset in range(taste_len):
                yield "taste", int(stream[index + offset])
            index += taste_len
            continue

        yield _classify_word(coerced), coerced
        index += 1


def stream_stats(stream: Sequence[int]) -> Dict[str, object]:
    counts = {
        "text": 0,
        "diagram": 0,
        "music": 0,
        "voice": 0,
        "image": 0,
        "bpe": 0,
        "mental": 0,
        "touch": 0,
        "smell": 0,
        "taste": 0,
    }
    valid_words = _valid_helper_words(stream)
    for modality, _word in _iter_classified_words(stream):
        counts[modality] += 1
    total = len(valid_words)
    ratios = {k: (v / total if total else 0.0) for k, v in counts.items()}
    return {"total_words": total, "counts": counts, "ratios": ratios}


def filter_stream(
    stream: Sequence[int],
    modality: Literal["text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"],
) -> List[int]:
    filtered: List[int] = []
    for word_modality, word in _iter_classified_words(stream):
        if word_modality == modality:
            filtered.append(word)
    return filtered


def iter_stream(stream: Sequence[int]) -> Iterator[Tuple[str, int]]:
    for modality, word in _iter_classified_words(stream):
        yield modality, word


def remove_modality(
    stream: Sequence[int],
    modality: Literal["diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"],
) -> List[int]:
    kept: List[int] = []
    for word_modality, word in _iter_classified_words(stream):
        if word_modality != modality:
            kept.append(word)
    return kept


def stream_to_json(stream: Sequence[int]) -> str:
    return json.dumps(_valid_helper_words(stream))


def json_to_stream(json_str: str) -> List[int]:
    try:
        raw = json.loads(json_str)
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    out: List[int] = []
    for value in raw:
        coerced = _coerce_helper_word(value)
        if coerced is None:
            continue
        out.append(coerced)
    return out


def stream_summary(stream: Sequence[int]) -> Dict[str, object]:
    summary = stream_stats(stream)
    valid, errors = validate_stream(stream)
    summary["stream_valid"] = valid
    summary["validation_errors"] = errors
    return summary


def save_stream_json(stream: Sequence[int], path: str | Path) -> None:
    Path(path).write_text(stream_to_json(stream), encoding="utf-8")


def load_stream_json(path: str | Path) -> List[int]:
    try:
        payload = Path(path).read_text(encoding="utf-8")
    except Exception:
        return []
    return json_to_stream(payload)


def save_stream_binary(stream: Sequence[int], path: str | Path) -> None:
    out = bytearray()
    for word in _valid_helper_words(stream):
        out.extend(word.to_bytes(4, "big", signed=False))
    Path(path).write_bytes(bytes(out))


def load_stream_binary(path: str | Path) -> List[int]:
    try:
        data = Path(path).read_bytes()
    except Exception:
        return []
    usable = len(data) - (len(data) % 4)
    out: List[int] = []
    for i in range(0, usable, 4):
        value = int.from_bytes(data[i : i + 4], "big", signed=False)
        coerced = _coerce_helper_word(value)
        if coerced is None:
            continue
        out.append(coerced)
    return out


def gzip_stream_size(path: str | Path) -> int:
    payload = Path(path).read_bytes()
    return len(gzip.compress(payload, compresslevel=9))


__all__ = [
    "IMCEncoder",
    "IMCDecoder",
    "IMCResult",
    "validate_stream",
    "get_kernel_backend_info",
    "stream_stats",
    "filter_stream",
    "iter_stream",
    "remove_modality",
    "stream_to_json",
    "json_to_stream",
    "stream_summary",
    "save_stream_json",
    "load_stream_json",
    "save_stream_binary",
    "load_stream_binary",
    "gzip_stream_size",
]
