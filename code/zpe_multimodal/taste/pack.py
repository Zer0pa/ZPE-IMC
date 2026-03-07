from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from ..core.constants import Mode, PAYLOAD_16_MASK
from .types import TasteEvent

TASTE_TYPE_BIT = 0x0400

VERSION_QUALITY = 0
VERSION_INTENSITY = 1
VERSION_TEMPORAL = 2
VERSION_FLAVOR = 3


def _ext_word(version: int, payload: int) -> int:
    return (Mode.EXTENSION.value << 18) | ((version & 0x3) << 16) | (payload & PAYLOAD_16_MASK)


def _word_fields(word: int) -> tuple[int, int, int]:
    mode = (word >> 18) & 0x3
    version = (word >> 16) & 0x3
    payload = word & PAYLOAD_16_MASK
    return mode, version, payload


def _payload(byte_value: int) -> int:
    return TASTE_TYPE_BIT | (int(byte_value) & 0xFF)


def _is_taste_word(word: int) -> bool:
    mode, _version, payload = _word_fields(word)
    return mode == Mode.EXTENSION.value and bool(payload & TASTE_TYPE_BIT)


def pack_taste_events(events: Iterable[TasteEvent]) -> List[int]:
    words: List[int] = []
    for event in events:
        if not isinstance(event, TasteEvent):
            raise TypeError(f"expected TasteEvent, got {type(event)!r}")

        quality_byte = ((event.dominant_quality & 0x7) << 3) | (event.secondary_quality & 0x7)
        intensity_byte = ((event.intensity & 0x7) << 3) | (event.intensity_direction & 0x7)

        words.append(_ext_word(VERSION_QUALITY, _payload(quality_byte)))
        words.append(_ext_word(VERSION_INTENSITY, _payload(intensity_byte)))
        for byte_value in event.temporal_payload:
            words.append(_ext_word(VERSION_TEMPORAL, _payload(byte_value)))
        for byte_value in event.flavor_payload:
            words.append(_ext_word(VERSION_FLAVOR, _payload(byte_value)))
    return words


def unpack_taste_words(words: Iterable[int]) -> tuple[dict | None, List[TasteEvent]]:
    word_list = list(words)
    if not word_list:
        return None, []

    events: List[TasteEvent] = []
    consumed = 0
    ignored = 0

    idx = 0
    while idx < len(word_list):
        w0 = word_list[idx]
        if not isinstance(w0, int) or not _is_taste_word(w0):
            ignored += 1
            idx += 1
            continue

        mode0, version0, payload0 = _word_fields(w0)
        if mode0 != Mode.EXTENSION.value or version0 != VERSION_QUALITY:
            ignored += 1
            idx += 1
            continue

        if idx + 2 >= len(word_list):
            break

        w1 = word_list[idx + 1]
        w2 = word_list[idx + 2]
        if not (isinstance(w1, int) and isinstance(w2, int)):
            ignored += 1
            idx += 1
            continue

        m1, v1, p1 = _word_fields(w1)
        m2, v2, p2 = _word_fields(w2)
        if (
            m1 != Mode.EXTENSION.value
            or v1 != VERSION_INTENSITY
            or not (p1 & TASTE_TYPE_BIT)
            or m2 != Mode.EXTENSION.value
            or v2 != VERSION_TEMPORAL
            or not (p2 & TASTE_TYPE_BIT)
        ):
            ignored += 1
            idx += 1
            continue

        quality_byte = payload0 & 0xFF
        intensity_byte = p1 & 0xFF

        dominant_quality = (quality_byte >> 3) & 0x7
        secondary_quality = quality_byte & 0x7
        intensity = (intensity_byte >> 3) & 0x7
        intensity_direction = intensity_byte & 0x7

        temporal_payload = [p2 & 0xFF]
        flavor_payload: List[int] = []

        j = idx + 3
        while j < len(word_list):
            wj = word_list[j]
            if not isinstance(wj, int) or not _is_taste_word(wj):
                break
            mj, vj, pj = _word_fields(wj)
            if mj != Mode.EXTENSION.value:
                break
            if vj == VERSION_TEMPORAL:
                temporal_payload.append(pj & 0xFF)
                j += 1
                continue
            if vj == VERSION_FLAVOR:
                flavor_payload.append(pj & 0xFF)
                j += 1
                continue
            break

        events.append(
            TasteEvent(
                dominant_quality=dominant_quality,
                secondary_quality=secondary_quality,
                intensity=intensity,
                intensity_direction=intensity_direction,
                temporal_payload=tuple(temporal_payload),
                flavor_payload=tuple(flavor_payload),
            )
        )
        consumed += j - idx
        idx = j

    if not events:
        return None, []

    metadata = {
        "stroke_count": len(events),
        "consumed_words": consumed,
        "ignored_words": ignored,
        "type_bit": hex(TASTE_TYPE_BIT),
    }
    return metadata, events
