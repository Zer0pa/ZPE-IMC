from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .core.codec import decode as _decode_core
from .core.codec import encode as _encode_core


def _normalize_ids(ids: Iterable[int]) -> list[int]:
    normalized: list[int] = []
    for idx, word in enumerate(ids):
        if isinstance(word, bool) or not isinstance(word, int):
            raise TypeError(f"ids[{idx}] must be int, got {type(word).__name__}")
        normalized.append(word)
    return normalized


def encode(text: str) -> list[int]:
    """Public tokenizer encode surface."""
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    return _encode_core(text)


def decode(ids: list[int] | tuple[int, ...]) -> str:
    """Public tokenizer decode surface."""
    if isinstance(ids, (str, bytes, bytearray)):
        raise TypeError("ids must be a list[int] or tuple[int, ...]")
    if not isinstance(ids, (list, tuple)):
        ids = list(ids)
    return _decode_core(_normalize_ids(ids))


@dataclass(frozen=True)
class ZPETokenizer:
    """Stable tokenizer wrapper used by downstream integrations."""

    lattice_path: str | None = None

    @classmethod
    def from_lattice(cls, path: str) -> "ZPETokenizer":
        if not isinstance(path, str) or not path.strip():
            raise ValueError("path must be a non-empty string")
        lattice = Path(path).expanduser()
        if not lattice.exists():
            raise FileNotFoundError(f"lattice path does not exist: {path}")
        if lattice.is_dir():
            raise IsADirectoryError(f"lattice path must be a file: {path}")
        return cls(lattice_path=str(lattice.resolve()))

    def encode(self, text: str) -> list[int]:
        return encode(text)

    def decode(self, ids: list[int] | tuple[int, ...]) -> str:
        return decode(ids)
