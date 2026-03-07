from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.diagram.quantize import DrawDir, MoveTo
from source.smell.adaptation import AdaptationParams, apply_adaptation
from source.smell.molecular_bridge import descriptor_to_tree_ops_safe
from source.smell.pack import unpack_odor_words
from source.smell.phase5_augment import (
    AugmentedOdorRecord,
    augmented_signature,
    pack_augmented_records,
    pack_z_episode,
    profile_to_augmented_record,
    unpack_augmented_words,
    unpack_instant_layer,
    unpack_z_episode,
)
from source.smell.types import SmellZLevel


def _profile(name: str, chirality: str = "ACHIRAL") -> dict:
    return {
        "name": name,
        "source": "phase3-test",
        "category": "FRUITY",
        "quality": [0.2, 0.7, 0.1, 0.1, 0.1],
        "complexity": 0.45,
        "chirality": chirality,
        "molecular_descriptors": {
            "molecular_weight": 128.2,
            "vapor_pressure_kpa": 1.8,
            "functional_groups": ["ester", "terpene", "aromatic"],
        },
    }


def _clone_with_intensity(record: AugmentedOdorRecord, intensity: int) -> AugmentedOdorRecord:
    commands = [MoveTo(record.stroke.pleasantness_start, 7 - intensity)]
    commands.extend(cmd for cmd in record.stroke.commands[1:] if isinstance(cmd, DrawDir))
    return AugmentedOdorRecord(
        stroke=record.stroke.__class__(
            commands=commands,
            category=record.stroke.category,
            pleasantness_start=record.stroke.pleasantness_start,
            intensity_start=intensity,
        ),
        tree_ops=record.tree_ops,
        complexity_axis=record.complexity_axis,
        chirality=record.chirality,
        label=record.label,
    )


def test_z_layer_episode_roundtrip() -> None:
    base = profile_to_augmented_record(_profile("citrus"))
    params = AdaptationParams(half_life=6, floor=4)
    expected = [apply_adaptation(base.stroke.intensity_start, i, params) for i in range(3)]
    records = [_clone_with_intensity(base, val) for val in expected]

    words = pack_z_episode(records, z_level=SmellZLevel.ADAPTATION, adaptation=params)
    z_level, decoded_params, decoded_records = unpack_z_episode(words)

    assert z_level == SmellZLevel.ADAPTATION
    assert decoded_params == params
    assert [r.stroke.intensity_start for r in decoded_records] == expected


def test_molecular_bridge_fallback_and_separation() -> None:
    fallback = (1, 2, 3)
    novel = {"molecular_weight": 0.0, "vapor_pressure_kpa": 0.0, "functional_groups": []}
    assert descriptor_to_tree_ops_safe(novel, fallback=fallback) == fallback

    pleasant = _profile("pleasant")
    aversive = dict(pleasant)
    aversive["name"] = "aversive"
    aversive["molecular_descriptors"] = {
        "molecular_weight": 98.0,
        "vapor_pressure_kpa": 1.2,
        "functional_groups": ["sulfur", "thiol"],
    }

    a = profile_to_augmented_record(pleasant)
    b = profile_to_augmented_record(aversive)
    assert a.tree_ops != b.tree_ops


def test_clone_and_wobbly_ruler() -> None:
    a = profile_to_augmented_record(_profile("alpha", chirality="L"))
    b = profile_to_augmented_record(_profile("beta", chirality="D"))

    aw1 = pack_augmented_records([a])
    aw2 = pack_augmented_records([a])
    bw = pack_augmented_records([b])

    assert aw1 == aw2
    assert aw1 != bw


def test_micro_and_backward_compatibility() -> None:
    records = [
        profile_to_augmented_record(_profile("one")),
        profile_to_augmented_record(_profile("two", chirality="L")),
    ]
    words = pack_z_episode(records, z_level=SmellZLevel.EPISODIC, adaptation=AdaptationParams(half_life=4, floor=2))

    assert 0 < len(words) < 1024

    instant = unpack_instant_layer(words)
    assert len(instant) == 2

    # Baseline smell decoder should still decode odor strokes from z-layered streams.
    _meta, base_strokes = unpack_odor_words(words)
    assert len(base_strokes) == 2

    recovered = unpack_augmented_words(pack_augmented_records(records))
    assert [augmented_signature(r) for r in recovered] == [augmented_signature(r) for r in records]


def test_dirty_data_rejected() -> None:
    bad_profile = _profile("bad")
    bad_profile["quality"] = [0.1, 0.2]  # invalid dimensionality
    with pytest.raises(ValueError):
        profile_to_augmented_record(bad_profile)

    with pytest.raises(ValueError):
        AdaptationParams(half_life=18, floor=2)
