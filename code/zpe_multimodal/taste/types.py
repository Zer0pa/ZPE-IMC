from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Tuple


def _validate_u3(name: str, value: int) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be int, got {type(value).__name__}")
    if value < 0 or value > 7:
        raise ValueError(f"{name} must be in [0, 7], got {value}")
    return value


class TasteQuality(IntEnum):
    SWEET = 0
    SOUR = 1
    SALTY = 2
    BITTER = 3
    UMAMI = 4


@dataclass(frozen=True)
class TasteEvent:
    dominant_quality: int
    secondary_quality: int
    intensity: int
    intensity_direction: int
    temporal_payload: Tuple[int, ...]
    flavor_payload: Tuple[int, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dominant_quality", _validate_u3("dominant_quality", int(self.dominant_quality)))
        object.__setattr__(self, "secondary_quality", _validate_u3("secondary_quality", int(self.secondary_quality)))
        object.__setattr__(self, "intensity", _validate_u3("intensity", int(self.intensity)))
        object.__setattr__(self, "intensity_direction", _validate_u3("intensity_direction", int(self.intensity_direction)))

        temporal = tuple(int(v) & 0xFF for v in self.temporal_payload)
        if not temporal:
            raise ValueError("temporal_payload must contain at least one byte")
        object.__setattr__(self, "temporal_payload", temporal)

        flavor = tuple(int(v) & 0xFF for v in self.flavor_payload)
        object.__setattr__(self, "flavor_payload", flavor)
