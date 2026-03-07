from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from .primitives import PRIMITIVES_PATH, Primitive, load_primitives, primitives_to_words

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "emoji"
MAPPING_PATH = DATA_DIR / "emoji_mapping_v2a.json"


@dataclass(frozen=True)
class EmojiMacro:
    emoji: str
    name: str
    macro_id: int
    primitives: List[str]
    notes: str = ""


@dataclass
class EmojiMapping:
    primitives: Dict[str, Primitive]
    macros: Dict[str, EmojiMacro]
    macros_by_id: Dict[int, EmojiMacro]
    macro_keys_longest_first: tuple[str, ...]

    def resolve_words(self, emoji: str) -> Optional[List[int]]:
        """
        Return the stroke words for a mapped emoji, or None if unmapped.
        Words are concatenated primitive words; callers may wrap or append
        mode/version bits as needed in future integrations.
        """
        macro = self.macros.get(emoji)
        if not macro:
            return None
        prims: List[Primitive] = []
        for name in macro.primitives:
            prim = self.primitives.get(name)
            if prim is None:
                raise KeyError(f"primitive {name} referenced by {emoji} is missing")
            prims.append(prim)
        return primitives_to_words(prims)

    def resolve_emoji(self, macro_id: int) -> Optional[str]:
        macro = self.macros_by_id.get(macro_id)
        return macro.emoji if macro else None


@lru_cache(maxsize=None)
def _load_default_mapping_cached(mapping_path_str: str, primitives_path_str: str) -> EmojiMapping:
    prims = load_primitives(Path(primitives_path_str))
    path = Path(mapping_path_str)
    if not path.exists():
        # Empty-but-valid fallback: text codec still runs without external emoji artifacts.
        return EmojiMapping(
            primitives=prims,
            macros={},
            macros_by_id={},
            macro_keys_longest_first=(),
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    macros: Dict[str, EmojiMacro] = {}
    macros_by_id: Dict[int, EmojiMacro] = {}
    for entry in data.get("macros", []):
        macro = EmojiMacro(
            emoji=entry["emoji"],
            name=entry.get("name", entry["emoji"]),
            macro_id=int(entry.get("macro_id", 0)),
            primitives=[p for p in entry.get("primitives", [])],
            notes=entry.get("notes", ""),
        )
        macros[macro.emoji] = macro
        macros_by_id[macro.macro_id] = macro
    return EmojiMapping(
        primitives=prims,
        macros=macros,
        macros_by_id=macros_by_id,
        macro_keys_longest_first=tuple(sorted(macros, key=len, reverse=True)),
    )


def load_default_mapping(
    mapping_path: Path | None = None, primitives_path: Path | None = None
) -> EmojiMapping:
    return _load_default_mapping_cached(
        str((mapping_path or MAPPING_PATH).resolve()),
        str((primitives_path or PRIMITIVES_PATH).resolve()),
    )


def make_macro_word(macro_id: int) -> int:
    """Encode an emoji macro id into an extension-mode word (version 0)."""
    if macro_id < 0 or macro_id >= (1 << 16):
        raise ValueError("emoji macro_id must fit in 16 bits")
    # mode=EXTENSION (2), version=0, payload=macro_id (16 bits)
    return (2 << 18) | (0 << 16) | macro_id
