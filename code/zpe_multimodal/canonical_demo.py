from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np

from .core.imc import IMCEncoder
from .diagram.quantize import DrawDir as DiagramDrawDir, MoveTo as DiagramMoveTo
from .smell.adaptation import AdaptationParams
from .smell.phase5_augment import AugmentedOdorRecord, TreeOp
from .smell.types import OdorCategory, OdorStroke, SmellZLevel
from .taste.codec import load_taste_events_from_fixture
from .taste.types import TasteEvent
from .touch.types import BodyRegion, DrawDir, MoveTo, RAIIDescriptor, ReceptorType, TouchStroke
from .voice.types import VoiceMetadata, VoiceStroke

CANONICAL_DEMO_TEXT = "ZPE IMC demo stream with all ten modalities, BPE, and emoji 🙂👩🏽‍💻🇿🇦."
CANONICAL_DEMO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
    '<g transform="translate(6 2) scale(0.9)">'
    '<polygon points="28,4 54,56 2,56" fill="none" stroke="#00ffff" stroke-width="3"/>'
    "</g>"
    "</svg>"
)
_FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"
_TASTE_PROMOTED_EVENTS = _FIXTURE_ROOT / "taste_promoted_events.json"


def runtime_voice_capability_mode() -> Literal["full", "fallback"]:
    return "full"


def _fixture_path(name: str) -> Path:
    path = _FIXTURE_ROOT / name
    if not path.exists():
        raise FileNotFoundError(f"missing canonical fixture: {path}")
    return path


def _build_image() -> np.ndarray:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:, :, 0] = np.tile(np.linspace(0, 255, 8, dtype=np.uint8), (8, 1))
    image[:, :, 1] = np.tile(np.linspace(255, 0, 8, dtype=np.uint8), (8, 1)).T
    image[:, :, 2] = 128
    return image


def build_promoted_voice_strokes() -> tuple[list[VoiceStroke], VoiceMetadata]:
    metadata = VoiceMetadata(language="en-us", time_step_sec=0.05, pitch_levels=8)
    strokes = [
        VoiceStroke(
            commands=[DiagramMoveTo(4, 0), DiagramDrawDir(0), DiagramDrawDir(0), DiagramDrawDir(1)],
            symbol="AA",
            stress=True,
            pitch_trend="UP",
            metadata=metadata,
            time_anchor_tick=4,
            formant_f1_band=5,
            formant_f2_band=10,
            speaking_rate_bucket=3,
            emotion_valence=5,
        ),
        VoiceStroke(
            commands=[DiagramMoveTo(11, 1), DiagramDrawDir(0), DiagramDrawDir(0), DiagramDrawDir(7)],
            symbol="N",
            stress=False,
            pitch_trend="DOWN",
            metadata=metadata,
            time_anchor_tick=11,
            formant_f1_band=3,
            formant_f2_band=7,
            speaking_rate_bucket=2,
            emotion_valence=4,
        ),
    ]
    return strokes, metadata


def build_promoted_mental_entries() -> list[dict[str, str]]:
    return [
        {"description": "hexagonal honeycomb lattice with converging radial rays"},
        {"description": "counter-clockwise spiral vortex with rotating coil"},
        {"description": "branching cobweb filigree pattern"},
    ]


def build_promoted_touch_frame() -> tuple[list[TouchStroke], dict[str, object]]:
    contacts = [
        TouchStroke(
            commands=[MoveTo(0, 0), DrawDir(0), DrawDir(1), DrawDir(2)],
            receptor=ReceptorType.SA_I,
            region=BodyRegion.INDEX_TIP,
            pressure_profile=[2, 3, 4],
        ),
        TouchStroke(
            commands=[MoveTo(0, 0), DrawDir(4), DrawDir(4), DrawDir(3)],
            receptor=ReceptorType.RA_I,
            region=BodyRegion.PALM_CENTER,
            pressure_profile=[5, 5, 4],
        ),
    ]
    metadata = {
        "frame_id": 3,
        "time_deltas_ms": [4, 12],
        "z_layers": {
            "directions": [0, 1, 2],
            "pressures": [2, 3, 4],
            "region": BodyRegion.INDEX_TIP,
        },
    }
    return contacts, metadata


def build_promoted_touch_anchor() -> tuple[list[TouchStroke], dict[str, object]]:
    contact = TouchStroke(
        commands=[MoveTo(0, 0), DrawDir(7), DrawDir(6), DrawDir(5)],
        receptor=ReceptorType.RA_II,
        region=BodyRegion.THUMB_TIP,
        pressure_profile=[3, 2, 1],
    )
    metadata = {
        "anchor_offset": (1, -1),
        "raii_complete": [
            {
                "region": BodyRegion.THUMB_TIP,
                "descriptor": RAIIDescriptor(frequency_band=9, amplitude=7, envelope=2),
            }
        ],
        "raii_frequency_sequences": [
            {"region": BodyRegion.THUMB_TIP, "bands": [4, 7, 9]}
        ],
    }
    return [contact], metadata


def build_promoted_smell_records() -> tuple[list[AugmentedOdorRecord], dict[str, object]]:
    records = [
        AugmentedOdorRecord(
            stroke=OdorStroke(
                commands=[DiagramMoveTo(5, 2), DiagramDrawDir(1), DiagramDrawDir(0), DiagramDrawDir(6)],
                category=OdorCategory.FLORAL,
                pleasantness_start=5,
                intensity_start=5,
            ),
            tree_ops=(TreeOp.BRANCH_RIGHT, TreeOp.DESCEND, TreeOp.ASCEND),
            complexity_axis=11,
            chirality=1,
            label="jasmine",
        ),
        AugmentedOdorRecord(
            stroke=OdorStroke(
                commands=[DiagramMoveTo(4, 3), DiagramDrawDir(0), DiagramDrawDir(0), DiagramDrawDir(4)],
                category=OdorCategory.WOODY_EARTHY,
                pleasantness_start=4,
                intensity_start=4,
            ),
            tree_ops=(TreeOp.BRANCH_LEFT, TreeOp.ASCEND, TreeOp.DESCEND),
            complexity_axis=8,
            chirality=0,
            label="cedar",
        ),
    ]
    metadata = {
        "z_level": SmellZLevel.EPISODIC,
        "adaptation": AdaptationParams(half_life=6, floor=3),
    }
    return records, metadata


def load_promoted_taste_events() -> list[TasteEvent]:
    return load_taste_events_from_fixture(_TASTE_PROMOTED_EVENTS)


def build_canonical_demo_stream(*, require_env: bool = False) -> list[int]:
    musicxml_path = _fixture_path("simple_scale.musicxml")
    voice_strokes, voice_metadata = build_promoted_voice_strokes()
    touch_frame_contacts, touch_frame_meta = build_promoted_touch_frame()
    touch_anchor_contact, touch_anchor_meta = build_promoted_touch_anchor()
    smell_records, smell_metadata = build_promoted_smell_records()

    return (
        IMCEncoder(require_env=require_env)
        .add_text(CANONICAL_DEMO_TEXT)
        .add_svg(CANONICAL_DEMO_SVG)
        .add_music(musicxml_path)
        .add_voice(voice_strokes, metadata=voice_metadata)
        .add_image(_build_image(), bits=3)
        .add_bpe([100, 200, 300])
        .add_mental(build_promoted_mental_entries())
        .add_touch(touch_frame_contacts, metadata=touch_frame_meta)
        .add_smell(smell_records, metadata=smell_metadata)
        .add_touch(touch_anchor_contact, metadata=touch_anchor_meta)
        .add_taste_events(load_promoted_taste_events())
        .build()
    )
