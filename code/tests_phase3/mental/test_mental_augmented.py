from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.mental.ingest import ingest_clinical_dataset
from source.mental.pack import pack_mental_strokes, unpack_mental_words
from source.mental.types import DirectionProfile, DrawDir, FormClass, MentalStroke, MoveTo, SymmetryOrder


def _stroke(profile: DirectionProfile, delta_ms: int) -> MentalStroke:
    directions = [0, 2, 4, 6] if profile == DirectionProfile.COMPASS_8 else [0, 2, 4, 6, 8, 10]
    return MentalStroke(
        commands=[MoveTo(10, 10)] + [DrawDir(d, profile=profile) for d in directions],
        form_class=FormClass.LATTICE,
        symmetry=SymmetryOrder.D6 if profile == DirectionProfile.D6_12 else SymmetryOrder.D4,
        direction_profile=profile,
        spatial_frequency=4,
        drift_speed=1,
        frame_index=3,
        delta_ms=delta_ms,
    )


def test_mixed_8_and_12_direction_roundtrip() -> None:
    strokes = [_stroke(DirectionProfile.COMPASS_8, 20), _stroke(DirectionProfile.D6_12, 40)]
    words = pack_mental_strokes(strokes)
    _meta, recovered = unpack_mental_words(words)
    assert len(recovered) == 2
    assert recovered[0].direction_profile == DirectionProfile.COMPASS_8
    assert recovered[1].direction_profile == DirectionProfile.D6_12


def test_delta_ms_preserved() -> None:
    strokes = [_stroke(DirectionProfile.D6_12, d) for d in (0, 5, 33, 120, 255)]
    words = pack_mental_strokes(strokes)
    _meta, recovered = unpack_mental_words(words)
    assert [s.delta_ms for s in recovered] == [0, 5, 33, 120, 255]


def test_ingest_pipeline_produces_strokes() -> None:
    entries = [
        {"description": "hexagonal lattice aura"},
        {"description": "rotating spiral tunnel"},
        {"description": "branching cobweb pattern"},
    ]
    results = ingest_clinical_dataset(entries)
    assert len(results) == 3
    assert all(result.stroke.commands for result in results)


def test_clone_and_wobbly_ruler() -> None:
    a = pack_mental_strokes([_stroke(DirectionProfile.COMPASS_8, 10)])
    b = pack_mental_strokes([_stroke(DirectionProfile.D6_12, 10)])
    assert a != b
    assert a == pack_mental_strokes([_stroke(DirectionProfile.COMPASS_8, 10)])


def test_dirty_data_invalid_profile_rejected() -> None:
    with pytest.raises(ValueError):
        MentalStroke(
            commands=[MoveTo(0, 0), DrawDir(0)],
            direction_profile=DirectionProfile.COMPASS_8,
            delta_ms=300,
        )
