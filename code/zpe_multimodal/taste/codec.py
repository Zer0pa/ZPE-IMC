from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Literal, Mapping

from .pack import pack_taste_events, unpack_taste_words
from .types import TasteEvent


def encode_taste_events(events: Iterable[TasteEvent]) -> List[int]:
    return pack_taste_events(events)


def decode_taste_words(words: Iterable[int]) -> tuple[dict | None, List[TasteEvent]]:
    return unpack_taste_words(words)


def load_taste_events_from_fixture(fixture_path: str | Path) -> List[TasteEvent]:
    data = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    events_node = data.get("events") if isinstance(data, dict) else data
    if not isinstance(events_node, list) or not events_node:
        raise ValueError("taste fixture must contain a non-empty events list")

    events: List[TasteEvent] = []
    for idx, entry in enumerate(events_node):
        if not isinstance(entry, Mapping):
            raise ValueError(f"taste fixture entry {idx} must be a mapping")
        events.append(
            TasteEvent(
                dominant_quality=int(entry["dominant_quality"]),
                secondary_quality=int(entry["secondary_quality"]),
                intensity=int(entry["intensity"]),
                intensity_direction=int(entry["intensity_direction"]),
                temporal_payload=tuple(int(value) for value in entry["temporal_payload"]),
                flavor_payload=tuple(int(value) for value in entry.get("flavor_payload", [])),
            )
        )
    return events


def load_taste_words_from_manifest(
    manifest_path: str | Path,
    *,
    corpus: Literal["minimum_closure", "expanded", "minimum_closure_corpus", "expanded_corpus"] = "minimum_closure",
) -> List[int]:
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    if corpus == "minimum_closure":
        corpus_keys = ("minimum_closure_corpus", "minimum_closure")
    elif corpus == "expanded":
        corpus_keys = ("expanded_corpus", "expanded")
    else:
        corpus_keys = (corpus,)

    encoded_by_record = None
    matched_key = None
    for corpus_key in corpus_keys:
        corpus_node = data.get(corpus_key)
        if not isinstance(corpus_node, dict):
            continue
        maybe_words = corpus_node.get("encoded_words_by_record")
        if isinstance(maybe_words, dict) and maybe_words:
            encoded_by_record = maybe_words
            matched_key = corpus_key
            break

    if not isinstance(encoded_by_record, dict) or not encoded_by_record:
        raise ValueError(f"missing encoded_words_by_record in any corpus keys: {corpus_keys!r}")

    merged: List[int] = []
    for record_id in sorted(encoded_by_record.keys()):
        words = encoded_by_record[record_id]
        if not isinstance(words, list):
            raise ValueError(f"record {record_id} words must be list")
        for word in words:
            if not isinstance(word, int):
                raise ValueError(f"record {record_id} contains non-int word: {word!r}")
            merged.append(int(word))

    if not merged:
        raise ValueError(f"no taste words found in corpus key: {matched_key}")

    return merged
