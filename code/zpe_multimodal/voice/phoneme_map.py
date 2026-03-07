from __future__ import annotations

from typing import Dict, List

# ARPAbet categories for coarse stroke patterns
VOWELS = {
    "AA",
    "AE",
    "AH",
    "AO",
    "AW",
    "AY",
    "EH",
    "ER",
    "EY",
    "IH",
    "IY",
    "OW",
    "OY",
    "UH",
    "UW",
}

STOPS = {"P", "B", "T", "D", "K", "G"}
AFFRICATES = {"CH", "JH"}
FRICATIVES = {"S", "Z", "SH", "ZH", "F", "V", "TH", "DH", "HH"}
NASALS = {"M", "N", "NG"}
LIQUIDS = {"L", "R"}
GLIDES = {"W", "Y"}
SILENCE = {"SIL", "SP", "PAU"}


def phoneme_category(sym: str) -> str:
    if sym in VOWELS:
        return "vowel"
    if sym in STOPS:
        return "stop"
    if sym in AFFRICATES:
        return "affricate"
    if sym in FRICATIVES:
        return "fricative"
    if sym in NASALS:
        return "nasal"
    if sym in LIQUIDS:
        return "liquid"
    if sym in GLIDES:
        return "glide"
    if sym in SILENCE:
        return "silence"
    return "other"
