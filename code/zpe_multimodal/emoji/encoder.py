from __future__ import annotations

from typing import List, Optional

from .mapping import EmojiMapping, load_default_mapping


def encode_emoji_text(text: str, mapping: EmojiMapping | None = None) -> Optional[List[int]]:
    """
    Encode a string containing a single emoji (scalar or ZWJ sequence) into stroke words.
    Returns None if the emoji is not mapped in Tier-2A scaffolding.

    This function does not alter the core codec; callers can opt-in and fall back to
    ESCAPE or existing paths when None is returned.
    """
    table = mapping or load_default_mapping()
    return table.resolve_words(text)
