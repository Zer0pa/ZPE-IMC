from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List

from ..text.mapping_v1 import make_word

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "emoji"
PRIMITIVES_PATH = DATA_DIR / "emoji_primitives_v2a.json"


@dataclass(frozen=True)
class Primitive:
    name: str
    description: str
    style_bits: int
    strokes: List[List[int]]

    def to_words(self) -> List[int]:
        """Convert the primitive's stroke state rows to unit words."""
        words: List[int] = []
        for states in self.strokes:
            if len(states) != 6:
                raise ValueError(f"primitive {self.name} has non-6-length stroke spec: {states}")
            words.append(make_word(tuple(states), style_bits=self.style_bits))
        return words


@lru_cache(maxsize=None)
def _load_primitives_cached(path_str: str) -> Dict[str, Primitive]:
    src = Path(path_str)
    if not src.exists():
        # Minimal fallback primitive set keeps emoji extension paths operational.
        return {
            "fallback": Primitive(
                name="fallback",
                description="fallback primitive generated at runtime",
                style_bits=0,
                strokes=[[1, 0, 0, 0, 0, 0]],
            )
        }
    data = json.loads(src.read_text(encoding="utf-8"))
    prims: Dict[str, Primitive] = {}
    for entry in data.get("primitives", []):
        prim = Primitive(
            name=entry["name"],
            description=entry.get("description", ""),
            style_bits=int(entry.get("style_bits", 0)),
            strokes=[list(map(int, row)) for row in entry.get("strokes", [])],
        )
        prims[prim.name] = prim
    return prims


def load_primitives(path: Path | None = None) -> Dict[str, Primitive]:
    src = (path or PRIMITIVES_PATH).resolve()
    return _load_primitives_cached(str(src))


def primitives_to_words(prims: Iterable[Primitive]) -> List[int]:
    words: List[int] = []
    for prim in prims:
        words.extend(prim.to_words())
    return words
