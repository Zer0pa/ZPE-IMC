"""
Zer0paUnit v1 mapping module.

Loads normative mapping tables from generated JSON artifacts in /data.
This replaces hardcoded tables and allows regeneration via tools/export_mapping.py.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Tuple

from ..core.constants import DEFAULT_VERSION, Mode

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
MAPPING_JSON = DATA_DIR / "mapping_v1.json"
RATIONALES_JSON = DATA_DIR / "mapping_v1_rationales.json"

# These are loaded at import.
CHAR_TO_WORD: Dict[str, int] = {}
WORD_TO_CHAR: Dict[int, str] = {}
RATIONALES: Dict[str, str] = {}


def _load_tables() -> None:
    global CHAR_TO_WORD, WORD_TO_CHAR, RATIONALES

    def register_char(ch: str) -> None:
        codepoint = ord(ch)
        word = (Mode.NORMAL.value << 18) | (DEFAULT_VERSION << 16) | (codepoint & 0xFFFF)
        CHAR_TO_WORD[ch] = word
        WORD_TO_CHAR[word] = ch

    if MAPPING_JSON.exists():
        with MAPPING_JSON.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # JSON keys are stringified codepoints (e.g. "65") -> word (int)
        for char_code_str, word in data.items():
            ch = chr(int(char_code_str))
            CHAR_TO_WORD[ch] = int(word)
            WORD_TO_CHAR[int(word)] = ch
    else:
        # Fallback mapping for portable operation when generated data artifacts are absent.
        for cp in range(32, 127):
            register_char(chr(cp))
        for ch in ("\n", "\t", "\r"):
            register_char(ch)

    if RATIONALES_JSON.exists():
        with RATIONALES_JSON.open("r", encoding="utf-8") as f:
            RATIONALES = json.load(f)


def make_word(
    strokes: Tuple[int, int, int, int, int, int],
    style_bits: int = 0,
    *,
    mode: Mode = Mode.NORMAL,
    version: int = DEFAULT_VERSION,
) -> int:
    if len(strokes) != 6:
        raise ValueError("strokes must have 6 entries (H, V, ↘, ↗, ↙, ↖)")
    acc = 0
    order = [5, 4, 3, 2, 1, 0]
    for idx, state in enumerate(strokes):
        if not 0 <= state <= 3:
            raise ValueError(f"stroke state out of range: {state}")
        shift = (order[idx] * 2) + 4
        acc |= state << shift
    word = (mode.value << 18) | (version << 16) | acc | (style_bits & 0xF)
    return word


def make_escape(byte0: int, byte1: int = 0) -> int:
    if not (0 <= byte0 <= 0xFF and 0 <= byte1 <= 0xFF):
        raise ValueError("escape bytes must be in 0..255")
    return (Mode.ESCAPE.value << 18) | (byte0 << 8) | byte1


# Initialize tables on import.
_load_tables()

# Compatibility aliases used in the PRD.
CHAR_TO_IX = CHAR_TO_WORD
IX_TO_CHAR = WORD_TO_CHAR
