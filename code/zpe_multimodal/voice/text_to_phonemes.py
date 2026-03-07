from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from functools import lru_cache
from typing import Iterable, List, Sequence, Tuple

from .types import PhonemeSymbol


_FALLBACK_LETTER_TO_ARPA = {
    "a": "AH",
    "b": "B",
    "c": "K",
    "d": "D",
    "e": "EH",
    "f": "F",
    "g": "G",
    "h": "HH",
    "i": "IH",
    "j": "JH",
    "k": "K",
    "l": "L",
    "m": "M",
    "n": "N",
    "o": "OW",
    "p": "P",
    "q": "K",
    "r": "R",
    "s": "S",
    "t": "T",
    "u": "UH",
    "v": "V",
    "w": "W",
    "x": "K",
    "y": "Y",
    "z": "Z",
}

_IPA_TO_ARPA = {
    "p": "P",
    "b": "B",
    "t": "T",
    "d": "D",
    "k": "K",
    "g": "G",
    "ɡ": "G",
    "m": "M",
    "n": "N",
    "ŋ": "NG",
    "f": "F",
    "v": "V",
    "θ": "TH",
    "ð": "DH",
    "s": "S",
    "z": "Z",
    "ʃ": "SH",
    "ʒ": "ZH",
    "h": "HH",
    "ɹ": "R",
    "r": "R",
    "l": "L",
    "ɫ": "L",
    "j": "Y",
    "w": "W",
    "tʃ": "CH",
    "dʒ": "JH",
    "i": "IY",
    "iː": "IY",
    "ɪ": "IH",
    "e": "EH",
    "eɪ": "EY",
    "ɛ": "EH",
    "æ": "AE",
    "ə": "AH",
    "ɚ": "ER",
    "ɝ": "ER",
    "ɜ": "ER",
    "ʌ": "AH",
    "ɑ": "AA",
    "ɑː": "AA",
    "ɒ": "AA",
    "ɔ": "AO",
    "ɔː": "AO",
    "o": "OW",
    "oʊ": "OW",
    "ʊ": "UH",
    "u": "UW",
    "uː": "UW",
    "aɪ": "AY",
    "aʊ": "AW",
    "ɔɪ": "OY",
}

PHONEME_SOURCE_MODES = (
    "ground_truth_alignment",
    "g2p_text",
    "phonemizer_optional_adapter",
    "deterministic_fallback",
)


def _fallback_tokens(text: str) -> List[str]:
    out: List[str] = []
    for char in text.lower():
        if char in _FALLBACK_LETTER_TO_ARPA:
            out.append(_FALLBACK_LETTER_TO_ARPA[char])
        elif char.isspace() and (not out or out[-1] != "SP"):
            out.append("SP")
    return [token for token in out if token != "SP"] or ["AH"]


def _normalize_ipa_phone(phone: str) -> str:
    token = phone.strip().lower()
    if not token or token == "|":
        return "SP"
    token = token.replace("ˈ", "").replace("ˌ", "").replace("͡", "")
    mapped = _IPA_TO_ARPA.get(token)
    if mapped:
        return mapped

    for key in ("dʒ", "tʃ", "aɪ", "aʊ", "ɔɪ", "oʊ", "eɪ"):
        if key in token:
            return _IPA_TO_ARPA[key]

    for char in token:
        if char in _IPA_TO_ARPA:
            return _IPA_TO_ARPA[char]
        if char in _FALLBACK_LETTER_TO_ARPA:
            return _FALLBACK_LETTER_TO_ARPA[char]
    return "AH"


def _normalize_cli_tokens(raw_tokens: List[str]) -> List[str]:
    out = []
    for token in raw_tokens:
        norm = _normalize_ipa_phone(token)
        if norm != "SP":
            out.append(norm)
    return out


def _normalize_g2p_tokens(raw_tokens: Sequence[str]) -> List[str]:
    out: List[str] = []
    for token in raw_tokens:
        value = str(token).strip()
        if not value or value in {" ", "|"}:
            continue
        value = re.sub(r"[^A-Za-z0-2]", "", value).upper()
        if value:
            out.append(value)
    return out


@lru_cache(maxsize=1)
def _load_g2p_engine():
    try:
        from g2p_en import G2p  # type: ignore
    except Exception:
        return None
    _ensure_nltk_data()
    return G2p()


def _ensure_nltk_data() -> None:
    try:
        import nltk  # type: ignore
    except Exception:
        return

    code_root = Path(__file__).resolve().parents[2]
    nltk_dir = code_root / "fixtures" / "nltk_data"
    nltk_dir.mkdir(parents=True, exist_ok=True)
    if str(nltk_dir) not in nltk.data.path:
        nltk.data.path.insert(0, str(nltk_dir))
    os.environ["NLTK_DATA"] = str(nltk_dir)

    required = (
        ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
        ("corpora/cmudict", "cmudict"),
    )
    for lookup_key, package_name in required:
        try:
            nltk.data.find(lookup_key)
        except LookupError:
            try:
                nltk.download(package_name, download_dir=str(nltk_dir), quiet=True)
            except Exception:
                pass


def _run_g2p_en(text: str) -> List[str]:
    g2p = _load_g2p_engine()
    if g2p is None:
        return []
    try:
        tokens = g2p(text)
    except Exception:
        return []
    return _normalize_g2p_tokens(tokens)


def _run_phonemizer_cli(text: str, lang: str = "en-us", allow_fallback: bool = True) -> List[str]:
    """Call phonemizer CLI via espeak backend as an external process (GPL-safe)."""
    cmd = [
        _resolve_phonemize_binary(),
        "-l",
        lang,
        "-b",
        "espeak",
        "-p",
        " ",
        "-w",
        " | ",
        "--strip",
    ]
    try:
        out = subprocess.check_output(cmd, input=text.encode("utf-8"), stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return _fallback_tokens(text) if allow_fallback else []
    except subprocess.CalledProcessError:
        return _fallback_tokens(text) if allow_fallback else []

    phon_str = out.decode("utf-8").strip()
    tokens = phon_str.replace("\n", " ").split()
    normalized = _normalize_cli_tokens(tokens)
    if normalized:
        return normalized
    return _fallback_tokens(text) if allow_fallback else []


def _resolve_phonemize_binary() -> str:
    env_bin = os.environ.get("PHONEMIZE_BIN", "").strip()
    if env_bin and Path(env_bin).exists():
        return env_bin
    path_bin = shutil.which("phonemize")
    if path_bin:
        return path_bin
    py_bin = Path(sys.executable).resolve().parent / "phonemize"
    if py_bin.exists():
        return str(py_bin)
    return "phonemize"


def _split_stress(token: str) -> PhonemeSymbol:
    # ARPAbet stress digits at end (0/1/2). Treat 1/2 as stressed.
    if token and token[-1].isdigit():
        stress_flag = token[-1] in ("1", "2")
        base = token[:-1]
    else:
        stress_flag = False
        base = token
    return PhonemeSymbol(symbol=base.upper(), stress=stress_flag)


def phoneme_symbols_from_tokens(tokens: Iterable[str]) -> List[PhonemeSymbol]:
    return [_split_stress(token) for token in tokens]


def phoneme_tokens_with_mode(
    text: str,
    lang: str = "en-us",
    preferred_modes: Sequence[str] | None = None,
) -> Tuple[List[str], str]:
    order = list(preferred_modes or ("g2p_text", "phonemizer_optional_adapter", "deterministic_fallback"))
    for mode in order:
        if mode == "g2p_text":
            g2p_tokens = _run_g2p_en(text)
            if g2p_tokens:
                return g2p_tokens, "g2p_text"
        elif mode == "phonemizer_optional_adapter":
            cli_tokens = _run_phonemizer_cli(text, lang=lang, allow_fallback=False)
            if cli_tokens:
                return cli_tokens, "phonemizer_optional_adapter"
        elif mode == "deterministic_fallback":
            return _fallback_tokens(text), "deterministic_fallback"
    return _fallback_tokens(text), "deterministic_fallback"


def text_to_phonemes(text: str, lang: str = "en-us") -> List[PhonemeSymbol]:
    """Convert text to phoneme symbols via external phonemizer CLI."""
    tokens, _ = phoneme_tokens_with_mode(text, lang=lang)
    return phoneme_symbols_from_tokens(tokens)
