from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.touch.pack import (
    pack_proprioception_samples,
    pack_timed_simultaneous_frame,
    pack_timestamp_delta,
    pack_touch_strokes,
    pack_touch_zlayers,
    pack_zlayer_word,
    unpack_proprioception_samples,
    unpack_timed_simultaneous_frame,
    unpack_timestamp_delta,
    unpack_touch_words,
    unpack_touch_zlayers,
)
from source.touch.proprioception import JointID, ProprioSample, max_angle_error
from source.touch.types import BodyRegion, DrawDir, MoveTo, ReceptorType, TouchStroke, TouchZLevel

MODE_EXTENSION = 0b10
TEXT_TYPE_BIT = 0x1000


def _stroke(region: BodyRegion, directions: list[int], pressures: list[int]) -> TouchStroke:
    return TouchStroke(
        commands=[MoveTo(0, 0)] + [DrawDir(d) for d in directions],
        receptor=ReceptorType.SA_I,
        region=region,
        pressure_profile=pressures,
    )


def _dirs(stroke: TouchStroke) -> list[int]:
    return [cmd.direction for cmd in stroke.commands if isinstance(cmd, DrawDir)]


def test_temporal_precision_roundtrip() -> None:
    contacts = [
        _stroke(BodyRegion.THUMB_TIP, [2, 6], [3, 2]),
        _stroke(BodyRegion.INDEX_TIP, [0, 4], [2, 2]),
        _stroke(BodyRegion.MIDDLE_TIP, [2, 2, 6], [2, 4, 2]),
    ]
    deltas = [5, 8, 13]

    words = pack_timed_simultaneous_frame(frame_id=7, contacts=contacts, deltas_ms=deltas)
    meta, decoded = unpack_timed_simultaneous_frame(words)

    assert meta["cooccurrence_preserved"] is True
    assert [d for d, _ in decoded] == deltas
    assert [s.region for _, s in decoded] == [c.region for c in contacts]


def test_zlayer_and_proprio_roundtrip() -> None:
    z_words = pack_touch_zlayers(
        directions=[0, 6, 4],
        pressures=[2, 3, 2],
        region=BodyRegion.PALM_CENTER,
    )
    z_decoded = unpack_touch_zlayers(z_words)
    assert z_decoded["surface"] == [0, 6, 4]
    assert z_decoded["dermal"] == [2, 3, 2]
    assert z_decoded["anatomical_region"] == BodyRegion.PALM_CENTER

    samples = [
        ProprioSample(joint=JointID.LEFT_ELBOW, angle_deg=32.0, tension_level=2),
        ProprioSample(joint=JointID.RIGHT_ELBOW, angle_deg=38.0, tension_level=3),
        ProprioSample(joint=JointID.SPINE, angle_deg=16.0, tension_level=1),
    ]
    p_words = pack_proprioception_samples(samples)
    p_decoded = unpack_proprioception_samples(p_words)

    assert len(p_decoded) == len(samples)
    assert [s.joint for s in p_decoded] == [s.joint for s in samples]
    assert [s.tension_level for s in p_decoded] == [s.tension_level for s in samples]
    assert max_angle_error(samples, p_decoded) <= 2.0


def test_clone_and_wobbly_ruler() -> None:
    contacts = [
        _stroke(BodyRegion.INDEX_TIP, [0, 4, 0], [2, 2, 3]),
        _stroke(BodyRegion.MIDDLE_TIP, [2, 2, 6], [2, 4, 2]),
    ]
    a = pack_timed_simultaneous_frame(frame_id=3, contacts=contacts, deltas_ms=[1, 2])
    b = pack_timed_simultaneous_frame(frame_id=3, contacts=contacts, deltas_ms=[1, 2])
    c = pack_timed_simultaneous_frame(frame_id=3, contacts=contacts, deltas_ms=[1, 3])

    assert a == b
    assert a != c


def test_cross_modal_dispatch_preserved() -> None:
    touch = pack_touch_strokes([_stroke(BodyRegion.PALM_CENTER, [0, 6, 4], [2, 3, 2])])
    z_words = pack_touch_zlayers([0, 6, 4], [2, 3, 2], BodyRegion.PALM_CENTER)
    text_word = (MODE_EXTENSION << 18) | (0 << 16) | TEXT_TYPE_BIT | 0x0007

    mixed = [touch[0], z_words[0], text_word, *touch[1:], *z_words[1:]]
    _meta, decoded_touch = unpack_touch_words(mixed)
    decoded_z = unpack_touch_zlayers(mixed)

    assert len(decoded_touch) == 1
    assert decoded_touch[0].region == BodyRegion.PALM_CENTER
    assert _dirs(decoded_touch[0]) == [0, 6, 4]
    assert decoded_z["surface"] == [0, 6, 4]


def test_dirty_data_rejected() -> None:
    with pytest.raises(ValueError):
        unpack_timestamp_delta([pack_timestamp_delta(10)[0]])

    with pytest.raises(ValueError):
        pack_zlayer_word(TouchZLevel.SURFACE, 99)

    with pytest.raises(ValueError):
        unpack_timed_simultaneous_frame([pack_zlayer_word(TouchZLevel.ANATOMICAL, 2)])
