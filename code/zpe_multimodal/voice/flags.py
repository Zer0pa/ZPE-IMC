from __future__ import annotations

import os


def voice_enabled() -> bool:
    # Tier-3B is now First-Class.
    return os.environ.get("STROKEGRAM_ENABLE_VOICE", "1").lower() not in ("0", "false", "no", "off")


def voice_placeholders_enabled() -> bool:
    return os.environ.get("STROKEGRAM_VOICE_PLACEHOLDERS", "1").lower() not in ("0", "false", "no", "off")
