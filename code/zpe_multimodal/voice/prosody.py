from __future__ import annotations

from typing import Iterable, List, Optional


def quantize_pitch_trend(f0_series: Iterable[float], window: int = 5, threshold: float = 5.0) -> List[str]:
    """Quantize pitch contour to UP/DOWN/LEVEL using a sliding window slope."""
    f0 = [v for v in f0_series if v is not None]
    if len(f0) < 2:
        return []
    trends: List[str] = []
    for i in range(0, len(f0), window):
        seg = f0[i : i + window]
        if len(seg) < 2:
            continue
        slope = seg[-1] - seg[0]
        if slope > threshold:
            trends.append("UP")
        elif slope < -threshold:
            trends.append("DOWN")
        else:
            trends.append("LEVEL")
    return trends


def assign_pitch_trends(f0_series: Iterable[float], span_count: int) -> List[str]:
    """Generate pitch trends sized to span_count by repeating quantized buckets."""
    trends = quantize_pitch_trend(f0_series)
    if not trends:
        return []
    out: List[str] = []
    for i in range(span_count):
        out.append(trends[i % len(trends)])
    return out


def trends_from_alignment(f0_series: Iterable[float], sr: int, alignment: list[dict]) -> list[str]:
    """Assign UP/DOWN/LEVEL per aligned phoneme using F0 slope over its interval."""
    f0 = list(f0_series)
    trends: list[str] = []
    for seg in alignment:
        start = float(seg["start"])
        end = float(seg["end"])
        if end <= start:
            trends.append("LEVEL")
            continue
        s_idx = max(0, int(start * sr))
        e_idx = min(len(f0), int(end * sr))
        if e_idx - s_idx < 2:
            trends.append("LEVEL")
            continue
        slope = f0[e_idx - 1] - f0[s_idx]
        if slope > 5.0:
            trends.append("UP")
        elif slope < -5.0:
            trends.append("DOWN")
        else:
            trends.append("LEVEL")
    return trends


def descriptor_distance(
    f1_a: int | None,
    f2_a: int | None,
    rate_a: int | None,
    emo_a: int | None,
    f1_b: int | None,
    f2_b: int | None,
    rate_b: int | None,
    emo_b: int | None,
) -> float:
    """Normalized descriptor distance across formants, speaking rate, and emotion."""

    def norm(value: int | None, denom: float) -> float:
        if value is None:
            return 0.0
        return max(0.0, min(1.0, float(value) / denom))

    total = abs(norm(f1_a, 15.0) - norm(f1_b, 15.0))
    total += abs(norm(f2_a, 15.0) - norm(f2_b, 15.0))
    total += abs(norm(rate_a, 15.0) - norm(rate_b, 15.0))
    total += abs(norm(emo_a, 7.0) - norm(emo_b, 7.0))
    return total / 4.0


def augmented_js(base_js: float, descriptor_delta: float, weight: float = 0.35) -> float:
    """Combine JS divergence with descriptor distance into a bounded [0, 1] score."""
    out = float(base_js) + float(weight) * float(descriptor_delta)
    if out < 0.0:
        return 0.0
    if out > 1.0:
        return 1.0
    return out
