from __future__ import annotations

# Reserved conceptual range for music-related words (20-bit space).
MUSIC_WORDSPACE_BASE = 0x30000
MUSIC_WORDSPACE_MAX = 0x3FFFF


def is_music_word(word: int) -> bool:
    """Return True if a word falls in the reserved music range."""
    return MUSIC_WORDSPACE_BASE <= word <= MUSIC_WORDSPACE_MAX


def music_macro_word(offset: int) -> int:
    """Placeholder for future music macros; offset must stay in-range."""
    word = MUSIC_WORDSPACE_BASE + offset
    if not is_music_word(word):
        raise ValueError(f"music word offset out of range: {offset}")
    return word
