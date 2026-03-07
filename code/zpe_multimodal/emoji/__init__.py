"""
Emoji Tier-2A scaffolding for the Zer0pa stroke codec.

This module is intentionally decoupled from the main encoder/decoder until
the mapping is fully populated. It provides loaders and a helper encoder that
returns stroke sequences (or None for unmapped emoji).
"""

from .mapping import EmojiMapping, load_default_mapping
from .encoder import encode_emoji_text

__all__ = ["EmojiMapping", "load_default_mapping", "encode_emoji_text"]
