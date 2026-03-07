"""Text mapping exports used by the integrated codec."""

from .mapping_v1 import (
    CHAR_TO_IX,
    CHAR_TO_WORD,
    IX_TO_CHAR,
    WORD_TO_CHAR,
    make_escape,
    make_word,
)

__all__ = [
    "CHAR_TO_WORD",
    "WORD_TO_CHAR",
    "CHAR_TO_IX",
    "IX_TO_CHAR",
    "make_word",
    "make_escape",
]
