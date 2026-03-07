"""Compatibility package that maps historical `source.*` imports to `zpe_multimodal.*`."""

from __future__ import annotations

import zpe_multimodal as _zpe_multimodal

# Reuse the real package module search path so `source.core`, `source.voice`,
# etc. resolve to `zpe_multimodal` modules without filesystem symlinks.
__path__ = _zpe_multimodal.__path__

from zpe_multimodal import *  # noqa: F401,F403
