from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List
import unicodedata

import os

from .constants import (
    DEFAULT_VERSION,
    Mode,
    PAYLOAD_16_MASK,
    STYLE_DOT,
    WORD_MASK,
    WORD_BITS,
)
from ..text.mapping_v1 import CHAR_TO_WORD, WORD_TO_CHAR, make_escape
from ..emoji.mapping import load_default_mapping as load_emoji_mapping
from ..emoji.mapping import make_macro_word

# Optional imports for extensions
try:
    from ..diagram.pack import DIAGRAM_TYPE_BIT, _diagram_enabled, unpack_diagram_words
except ImportError:
    DIAGRAM_TYPE_BIT = 0x8000
    def _diagram_enabled(): return False
    def unpack_diagram_words(w): return []

try:
    from ..music.flags import music_enabled, music_placeholders_enabled
    from ..music.pack import MUSIC_TYPE_BIT, unpack_music_words
except ImportError as e:
    MUSIC_TYPE_BIT = 0x4000
    def music_enabled(): return False
    def music_placeholders_enabled(): return False
    def unpack_music_words(w): return {}, []

try:
    from ..voice.flags import voice_enabled, voice_placeholders_enabled
    from ..voice.pack import VOICE_TYPE_BIT, unpack_voice_words
except ImportError:
    VOICE_TYPE_BIT = 0x2000
    def voice_enabled(): return False
    def voice_placeholders_enabled(): return False
    def unpack_voice_words(w): return []

try:
    from ..mental.codec import decode_mental
    from ..mental.pack import MENTAL_TYPE_BIT
except ImportError:
    MENTAL_TYPE_BIT = 0x0100

    def decode_mental(_words):
        return None, []

try:
    from ..touch.codec import decode_touch
    from ..touch.pack import TOUCH_TYPE_BIT
except ImportError:
    TOUCH_TYPE_BIT = 0x0800

    def decode_touch(_words):
        return None, []

try:
    from ..smell.codec import decode_smell_words
    from ..smell.pack import SMELL_TYPE_BIT
except ImportError:
    SMELL_TYPE_BIT = 0x0200

    def decode_smell_words(_words):
        return None, []

BPE_TYPE_BIT = 0x1000
# Use a Unicode non-character as a collision-resistant sentinel for embedded BPE markers.
# decode() stays string-only; decode_with_bpe() recovers tokens from the sentinel-wrapped payloads.
BPE_SENTINEL = "\ufffe"


def _flush_escape_buffer(buf: bytearray, out_chars: List[str]) -> None:
    if not buf:
        return
    try:
        out_chars.append(buf.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("invalid UTF-8 bytes in escape buffer") from exc
    buf.clear()


def _emoji_enabled() -> bool:
    # Tier-2A is now First-Class. Feature flag is deprecated but respected if explicitly disabled.
    return os.environ.get("STROKEGRAM_ENABLE_EMOJI", "1").lower() not in ("0", "false", "no", "off")


def _emoji_macro_enabled() -> bool:
    # Macro-word transport is opt-in because upstream macro-id ranges collide with
    # extension type bits used by other modalities in unified streams.
    return os.environ.get("STROKEGRAM_ENABLE_EMOJI_MACROS", "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


@lru_cache(maxsize=1)
def _native_text_encoder():
    try:
        from .imc_native import encode_text_kernel
    except Exception:
        return None
    return encode_text_kernel


def _validate_text_input(text: str) -> None:
    for ch in text:
        if 0xD800 <= ord(ch) <= 0xDFFF:
            raise ValueError("surrogate characters are not supported")


def _encode_noemoji_python(text: str) -> List[int]:
    ids: List[int] = []
    escape_bytes = bytearray()
    append_id = ids.append

    def flush_escape():
        nonlocal escape_bytes
        if not escape_bytes:
            return
        buf = escape_bytes
        n = len(buf)
        for i in range(0, n, 2):
            b0 = buf[i]
            b1 = buf[i + 1] if i + 1 < n else 0
            append_id(make_escape(b0, b1))
        buf.clear()

    text_nfd = unicodedata.normalize("NFD", text)
    lookup = CHAR_TO_WORD.get

    for ch in text_nfd:
        word = lookup(ch)
        if word is None:
            escape_bytes.extend(ch.encode("utf-8"))
            continue
        flush_escape()
        append_id(word)

    flush_escape()
    return ids


def _encode_noemoji(text: str) -> List[int]:
    _validate_text_input(text)
    native_encode = _native_text_encoder()
    if native_encode is not None:
        return [int(word) for word in native_encode(text)]
    return _encode_noemoji_python(text)


def encode(text: str) -> List[int]:
    """Encode Unicode text to Zer0paUnit v1 IDs (NFD normalized).

    Emoji Tier-2A mapping is opt-in via STROKEGRAM_ENABLE_EMOJI=1. When disabled,
    behavior matches the original Tier-0 encoder.
    """
    if not _emoji_enabled() or not _emoji_macro_enabled():
        return _encode_noemoji(text)

    _validate_text_input(text)
    ids: List[int] = []
    escape_bytes = bytearray()
    append_id = ids.append

    mapping = load_emoji_mapping()
    macro_lookup = mapping.macros
    emoji_keys = mapping.macro_keys_longest_first

    def flush_escape():
        nonlocal escape_bytes
        if not escape_bytes:
            return
        buf = escape_bytes
        n = len(buf)
        for i in range(0, n, 2):
            b0 = buf[i]
            b1 = buf[i + 1] if i + 1 < n else 0
            append_id(make_escape(b0, b1))
        buf.clear()

    def _prefer_macro(seq: str) -> bool:
        # Preserve Phase-2 scalar behavior by default; prioritize composed emoji
        # sequences that require semantic glue (ZWJ/VS16/skin-tone/keycap/flags).
        if "\u200d" in seq or "\ufe0f" in seq or "\u20e3" in seq:
            return True
        if any("\U0001F3FB" <= ch <= "\U0001F3FF" for ch in seq):
            return True
        if len(seq) > 1 and all("\U0001F1E6" <= ch <= "\U0001F1FF" for ch in seq):
            return True
        return False

    i = 0
    text_len = len(text)
    while i < text_len:
        matched = None
        matched_macro_id = None
        # attempt emoji match at position i
        for ek in emoji_keys:
            if text.startswith(ek, i):
                macro = macro_lookup.get(ek)
                if macro:
                    matched = ek
                    matched_macro_id = macro.macro_id
                    break
        if matched is not None and _prefer_macro(matched):
            flush_escape()
            append_id(make_macro_word(matched_macro_id))
            i += len(matched)
            continue
        ch = text[i]
        # Normal Tier-0 path per character (NFD)
        for subch in unicodedata.normalize("NFD", ch):
            word = CHAR_TO_WORD.get(subch)
            if word is None:
                escape_bytes.extend(subch.encode("utf-8"))
            else:
                flush_escape()
                append_id(word)
        i += 1

    flush_escape()
    return ids


_EXTENSION_MODALITY_KEYS = ("diagram", "music", "voice", "mental", "touch", "smell")


def _init_extension_state() -> tuple[dict[str, List[List[int]]], dict[str, List[int]]]:
    blocks = {key: [] for key in _EXTENSION_MODALITY_KEYS}
    collecting = {key: [] for key in _EXTENSION_MODALITY_KEYS}
    return blocks, collecting


def _flush_extension_state(collecting: dict[str, List[int]], blocks: dict[str, List[List[int]]]) -> None:
    for key in _EXTENSION_MODALITY_KEYS:
        if collecting[key]:
            blocks[key].append(collecting[key])
            collecting[key] = []


def _resolve_extension_emoji(
    *,
    mode: int,
    payload: int,
    emoji_enabled: bool,
    emoji_mapping,
) -> str | None:
    if not (
        _emoji_macro_enabled()
        and emoji_enabled
        and emoji_mapping
        and mode == Mode.EXTENSION.value
        and (payload & (DIAGRAM_TYPE_BIT | MUSIC_TYPE_BIT | VOICE_TYPE_BIT | BPE_TYPE_BIT | TOUCH_TYPE_BIT | SMELL_TYPE_BIT | MENTAL_TYPE_BIT)) == 0
    ):
        return None
    return emoji_mapping.resolve_emoji(payload)


def _decode_normal_word(
    word: int,
    *,
    default_version: int,
    out: List[str],
    escape_buf: bytearray,
    lookup,
) -> None:
    version = (word >> 16) & 0x3
    if version != default_version:
        raise ValueError(f"unsupported version {version} in word {word:#x}")
    _flush_escape_buffer(escape_buf, out)
    ch = lookup(word)
    if ch is None:
        raise ValueError(f"unknown unit word {word:#x}")
    out.append(ch)


def _decode_escape_word(word: int, *, default_version: int, escape_buf: bytearray) -> None:
    version = (word >> 16) & 0x3
    if version != default_version:
        raise ValueError(f"unsupported version {version} in escape word {word:#x}")
    b0 = (word >> 8) & 0xFF
    b1 = word & 0xFF
    escape_buf.append(b0)
    if b1:
        escape_buf.append(b1)


def _decode_extension_word(
    *,
    word: int,
    mode: int,
    payload: int,
    out: List[str],
    escape_buf: bytearray,
    collecting: dict[str, List[int]],
    emoji_enabled: bool,
    emoji_mapping,
    diagram_enabled: bool,
    music_flag: bool,
    voice_flag: bool,
) -> None:
    resolved_emoji = _resolve_extension_emoji(
        mode=mode,
        payload=payload,
        emoji_enabled=emoji_enabled,
        emoji_mapping=emoji_mapping,
    )
    if resolved_emoji:
        _flush_escape_buffer(escape_buf, out)
        out.append(resolved_emoji)
        return

    if payload & DIAGRAM_TYPE_BIT:
        if not diagram_enabled:
            raise ValueError(
                f"diagram extension encountered but STROKEGRAM_ENABLE_DIAGRAM is not set: {word:#x}"
            )
        collecting["diagram"].append(word)
        return

    if payload & MUSIC_TYPE_BIT:
        if not music_flag:
            raise ValueError(f"music extension encountered but STROKEGRAM_ENABLE_MUSIC is not set: {word:#x}")
        collecting["music"].append(word)
        return

    if payload & VOICE_TYPE_BIT:
        if not voice_flag:
            raise ValueError(f"voice extension encountered but STROKEGRAM_ENABLE_VOICE is not set: {word:#x}")
        collecting["voice"].append(word)
        return

    if payload & BPE_TYPE_BIT:
        token = payload & 0xFFF
        out.append(f"{BPE_SENTINEL}{token:X}{BPE_SENTINEL}")
        return

    if payload & TOUCH_TYPE_BIT:
        collecting["touch"].append(word)
        return

    if payload & SMELL_TYPE_BIT:
        collecting["smell"].append(word)
        return

    if payload & MENTAL_TYPE_BIT:
        collecting["mental"].append(word)
        return

    raise ValueError(f"unsupported extension mode in word {word:#x}")


def decode(ids: Iterable[int]) -> str:
    """Decode Zer0paUnit v1 IDs to text (NFC normalized)."""
    out: List[str] = []
    extension_blocks, collecting = _init_extension_state()
    escape_buf = bytearray()
    lookup = WORD_TO_CHAR.get
    mode_normal = Mode.NORMAL.value
    mode_escape = Mode.ESCAPE.value
    mode_extension = Mode.EXTENSION.value
    payload_mask = WORD_MASK
    default_version = DEFAULT_VERSION
    emoji_enabled = _emoji_enabled()
    diagram_enabled = _diagram_enabled()
    music_flag = music_enabled()
    voice_flag = voice_enabled()
    emoji_mapping = load_emoji_mapping() if emoji_enabled else None

    for word in ids:
        if word < 0 or word > payload_mask:
            raise ValueError(f"word out of range: {word}")
        mode = (word >> 18) & 0x3
        if mode == mode_normal:
            _flush_extension_state(collecting, extension_blocks)
            _decode_normal_word(
                word,
                default_version=default_version,
                out=out,
                escape_buf=escape_buf,
                lookup=lookup,
            )
        elif mode == mode_escape:
            _flush_extension_state(collecting, extension_blocks)
            _decode_escape_word(word, default_version=default_version, escape_buf=escape_buf)
        elif mode == mode_extension or mode == Mode.RESERVED.value:
            payload = word & PAYLOAD_16_MASK
            _decode_extension_word(
                word=word,
                mode=mode,
                payload=payload,
                out=out,
                escape_buf=escape_buf,
                collecting=collecting,
                emoji_enabled=emoji_enabled,
                emoji_mapping=emoji_mapping,
                diagram_enabled=diagram_enabled,
                music_flag=music_flag,
                voice_flag=voice_flag,
            )
        else:
            raise ValueError(f"unsupported mode in word {word:#x}")

    _flush_escape_buffer(escape_buf, out)
    _flush_extension_state(collecting, extension_blocks)

    diagram_blocks = extension_blocks["diagram"]
    music_blocks = extension_blocks["music"]
    voice_blocks = extension_blocks["voice"]

    if diagram_blocks:
        placeholders = os.environ.get("STROKEGRAM_DIAGRAM_PLACEHOLDERS", "1").lower() not in (
            "0",
            "false",
            "no",
            "off",
        )
        if placeholders:
            for idx in range(len(diagram_blocks)):
                out.append(f"<diagram:{idx}>")
    if music_blocks and music_placeholders_enabled():
        for idx in range(len(music_blocks)):
            out.append(f"<music:{idx}>")
    if voice_blocks and voice_placeholders_enabled():
        for idx in range(len(voice_blocks)):
            out.append(f"<voice:{idx}>")
    return unicodedata.normalize("NFC", "".join(out))


def _to_word_list(ids: Iterable[int]) -> List[int]:
    return [int(w) for w in ids]


def decode_with_diagrams(ids: Iterable[int]) -> tuple[str, list]:
    """Decode text and collect diagram blocks (packed extension words) if diagram flag is on."""
    word_list = _to_word_list(ids)
    text = decode(word_list)
    diagrams: List = []
    if _diagram_enabled():
        diag_words: List[int] = [
            w for w in word_list if ((w >> 18) & 0x3) == Mode.EXTENSION.value and (w & DIAGRAM_TYPE_BIT)
        ]
        if diag_words:
            diagrams = unpack_diagram_words(diag_words)
    return text, diagrams


def decode_with_music(ids: Iterable[int]) -> tuple[str, list]:
    """Decode text and collect music stroke blocks + metadata if music flag is on."""
    word_list = _to_word_list(ids)
    text = decode(word_list)
    music_paths: List = []
    if music_enabled():
        music_words: List[int] = [
            w for w in word_list if ((w >> 18) & 0x3) == Mode.EXTENSION.value and (w & MUSIC_TYPE_BIT)
        ]
        if music_words:
            meta, paths = unpack_music_words(music_words)
            music_paths = [(meta, paths)]
    return text, music_paths


def decode_with_voice(ids: Iterable[int]) -> tuple[str, list]:
    """Decode text and collect voice stroke blocks if voice flag is on."""
    word_list = _to_word_list(ids)
    text = decode(word_list)
    voice_paths: List = []
    if voice_enabled():
        voice_words: List[int] = [
            w for w in word_list if ((w >> 18) & 0x3) == Mode.EXTENSION.value and (w & VOICE_TYPE_BIT)
        ]
        if voice_words:
            voice_paths = unpack_voice_words(voice_words)
    return text, voice_paths


def decode_with_mental(ids: Iterable[int]) -> tuple[str, list]:
    word_list = _to_word_list(ids)
    text = decode(word_list)
    mental_words: List[int] = [w for w in word_list if ((w & PAYLOAD_16_MASK) & MENTAL_TYPE_BIT)]
    if not mental_words:
        return text, []
    meta, strokes = decode_mental(mental_words)
    return text, [(meta, strokes)]


def decode_with_touch(ids: Iterable[int]) -> tuple[str, list]:
    word_list = _to_word_list(ids)
    text = decode(word_list)
    touch_words: List[int] = [
        w
        for w in word_list
        if ((w >> 18) & 0x3) == Mode.EXTENSION.value and ((w & PAYLOAD_16_MASK) & TOUCH_TYPE_BIT)
    ]
    if not touch_words:
        return text, []
    meta, strokes = decode_touch(touch_words)
    return text, [(meta, strokes)]


def decode_with_smell(ids: Iterable[int]) -> tuple[str, list]:
    word_list = _to_word_list(ids)
    text = decode(word_list)
    smell_words: List[int] = [
        w
        for w in word_list
        if ((w >> 18) & 0x3) == Mode.EXTENSION.value and (((w & PAYLOAD_16_MASK) & 0x0E00) == SMELL_TYPE_BIT)
    ]
    if not smell_words:
        return text, []
    meta, strokes = decode_smell_words(smell_words)
    return text, [(meta, strokes)]


def decode_with_bpe(ids: Iterable[int], vocab: dict | None = None) -> tuple[str, List[int]]:
    """Decode IDs and extract BPE tokens from typed extension words only.

    This avoids spoofable text-regex extraction and treats plain text as plain text,
    even when it contains sentinel-like characters.
    """
    bpe_tokens: List[int] = []
    out_parts: List[str] = []
    text_chunk: List[int] = []
    append_text_word = text_chunk.append
    append_out = out_parts.append
    append_bpe = bpe_tokens.append

    def flush_text_chunk() -> None:
        if not text_chunk:
            return
        append_out(decode(text_chunk))
        text_chunk.clear()

    for raw_word in ids:
        word = int(raw_word)
        mode = (word >> 18) & 0x3
        payload = word & PAYLOAD_16_MASK
        if mode == Mode.EXTENSION.value and (payload & BPE_TYPE_BIT):
            flush_text_chunk()
            token = payload & 0x0FFF
            append_bpe(token)
            if vocab and token in vocab:
                append_out(str(vocab[token]))
            continue
        append_text_word(word)

    flush_text_chunk()
    return "".join(out_parts), bpe_tokens


def encode_batch(texts: Iterable[str]) -> List[List[int]]:
    return [encode(t) for t in texts]


def decode_batch(batch_ids: Iterable[Iterable[int]]) -> List[str]:
    return [decode(seq) for seq in batch_ids]


def encode_bpe_bridge(tokens: Iterable[int]) -> List[int]:
    """Encode a sequence of BPE tokens into Zer0paUnit extension words.
    
    Each token is wrapped in an extension word with the BPE_TYPE_BIT set.
    Note: This assumes tokens fit in the remaining payload bits (12 bits: 0-4095).
    For larger vocabularies, a multi-word scheme would be needed.
    """
    ids = []
    for token in tokens:
        if token > 0xFFF:
            raise ValueError(f"BPE token {token} exceeds 12-bit limit for bridge mode")
        # Construct word: Mode.EXTENSION | Version 0 | BPE_TYPE | Token
        word = (Mode.EXTENSION.value << 18) | (DEFAULT_VERSION << 16) | BPE_TYPE_BIT | token
        ids.append(word)
    return ids


# --- Masterunit / Physics Layer Integration ---

try:
    from .masterunit import Masterunit
    from .spatial_codec import SpatialEncoder
    from .physics.symplectic import SymplecticCA
    _MASTERUNIT_AVAILABLE = True
except Exception:
    Masterunit = None
    SpatialEncoder = None
    SymplecticCA = None
    _MASTERUNIT_AVAILABLE = False

def encode_to_masterunits(text: str) -> List[Masterunit]:
    if not _MASTERUNIT_AVAILABLE:
        raise RuntimeError("Masterunit layer unavailable; missing masterunit/spatial_codec")
    """
    Encode text to a sequence of 160-bit Masterunits with Physics Layer (Symplectic CA) applied.
    Uses SpatialEncoder to enforce topological constraints (Betti numbers > 0).
    """
    words = encode(text)
    
    encoder = SpatialEncoder()
    physics = SymplecticCA()
    
    # Chunk into groups of encoder.capacity_bits // 20 (which is 6 words)
    chunk_size = encoder.capacity_bits // 20
    
    mgs = []
    for i in range(0, len(words), chunk_size):
        chunk = words[i:i+chunk_size]
        # Encode with Spatial (Topology)
        mg = encoder.encode_chunk(chunk)
        # Apply Physics (Conservation + Chaos)
        physics.apply(mg, steps=10)
        mgs.append(mg)
        
    return mgs

def decode_from_masterunits(mgs: List[Masterunit]) -> str:
    if not _MASTERUNIT_AVAILABLE:
        raise RuntimeError("Masterunit layer unavailable; missing masterunit/spatial_codec")
    """
    Decode a sequence of Masterunits back to text, reversing the Physics Layer.
    """
    encoder = SpatialEncoder()
    physics = SymplecticCA()
    
    all_words = []
    for mg in mgs:
        # Create a copy to avoid mutating input
        mg_copy = Masterunit(mg.data)
        
        # Reverse Physics
        physics.reverse(mg_copy, steps=10)
        
        # Decode Spatial
        words = encoder.decode_chunk(mg_copy)
        all_words.extend(words)
        
    # Filter out 0s (padding) if they are not valid spaces?
    # In Zer0paUnit, 0 is often mapped to Space or Null.
    # If 0 is Space, we might have extra spaces.
    # Let's strip trailing spaces from the final string.
    return decode(all_words).rstrip()
