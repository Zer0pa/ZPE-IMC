from __future__ import annotations

import os


def music_enabled() -> bool:
    # Tier-3A is now First-Class.
    return os.environ.get("STROKEGRAM_ENABLE_MUSIC", "1").lower() not in ("0", "false", "no", "off")


def music_placeholders_enabled() -> bool:
    return os.environ.get("STROKEGRAM_MUSIC_PLACEHOLDERS", "1").lower() not in ("0", "false", "no", "off")


def require_music_enabled() -> None:
    if not music_enabled():
        raise RuntimeError("music support requires STROKEGRAM_ENABLE_MUSIC=1")
