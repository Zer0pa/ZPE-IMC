from __future__ import annotations

import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.common import configure_env

configure_env()

from source.core.constants import Mode, WORD_MASK
from source.core.imc import (
    IMCDecoder,
    IMCEncoder,
    filter_stream,
    iter_stream,
    json_to_stream,
    load_stream_binary,
    load_stream_json,
    remove_modality,
    save_stream_binary,
    save_stream_json,
    stream_stats,
    stream_summary,
    stream_to_json,
)


def _base_stream() -> list[int]:
    return IMCEncoder(require_env=False).add_text("a").add_bpe([12, 34]).build()


def _dirty_case_streams(*, cases: int, seed: int) -> list[tuple[int, str, list[object]]]:
    rng = random.Random(seed)
    base = _base_stream()
    non_int_values = ["x", None, 3.14, {"k": "v"}, ["a"], True]
    out_values = [-1, WORD_MASK + 1, WORD_MASK + 77]
    malformed_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 65535, ((Mode.RESERVED.value << 18) | 0x0001)]

    out: list[tuple[int, str, list[object]]] = []
    for case_id in range(cases):
        s: list[object] = list(base)
        roll = rng.random()
        if roll < 0.40:
            klass = "non_int"
            s.insert(rng.randint(0, len(s)), rng.choice(non_int_values))
        elif roll < 0.80:
            klass = "out_of_range"
            s.insert(rng.randint(0, len(s)), rng.choice(out_values))
        elif roll < 0.95:
            klass = "malformed_int"
            s.insert(rng.randint(0, len(s)), rng.choice(malformed_values))
        else:
            klass = "mixed"
            s.insert(rng.randint(0, len(s)), rng.choice(non_int_values))
            s.insert(rng.randint(0, len(s)), rng.choice(out_values))
            s.insert(rng.randint(0, len(s)), rng.choice(malformed_values))
        out.append((case_id, klass, s))
    return out


def test_stream_summary_handles_malformed_int_without_crash() -> None:
    stream: list[object] = _base_stream()
    stream.insert(1, 0)

    summary = stream_summary(stream)
    stats = stream_stats(stream)

    assert summary["stream_valid"] is False
    assert any("unknown unit word" in err for err in summary["validation_errors"])
    assert stats["total_words"] >= 0
    assert isinstance(stats["counts"], dict)


def test_helper_serialization_apis_ignore_dirty_words(tmp_path: Path) -> None:
    valid_bpe = (Mode.EXTENSION.value << 18) | 0x1000 | 5
    dirty_stream: list[object] = [1, "x", -1, WORD_MASK + 1, 0, valid_bpe, {"bad": 1}, True]

    payload = stream_to_json(dirty_stream)
    restored = json_to_stream(payload)
    assert all(isinstance(v, int) and 0 <= v <= WORD_MASK for v in restored)

    assert json_to_stream("{not-json") == []
    assert json_to_stream('{"x":1}') == []

    json_path = tmp_path / "dirty.json"
    save_stream_json(dirty_stream, json_path)
    loaded_json = load_stream_json(json_path)
    assert loaded_json == restored

    bin_path = tmp_path / "dirty.bin"
    save_stream_binary(dirty_stream, bin_path)
    loaded_bin = load_stream_binary(bin_path)
    assert loaded_bin == restored

    # Trailing garbage byte should be safely ignored.
    bin_path.write_bytes(bin_path.read_bytes() + b"\xff")
    loaded_bin_tail = load_stream_binary(bin_path)
    assert loaded_bin_tail == restored


def test_dirty_campaign_decode_and_helper_apis_no_uncaught_crash() -> None:
    decoder = IMCDecoder()
    crashes: list[dict[str, object]] = []

    for case_id, klass, stream in _dirty_case_streams(cases=1000, seed=20260220):
        try:
            decoded = decoder.decode(stream)
            stats = stream_stats(stream)
            summary = stream_summary(stream)
            filtered_text = filter_stream(stream, "text")
            filtered_diagram = filter_stream(stream, "diagram")
            iter_rows = list(iter_stream(stream))
            removed_bpe = remove_modality(stream, "bpe")
            as_json = stream_to_json(stream)
            restored = json_to_stream(as_json)

            assert isinstance(decoded.stream_valid, bool)
            assert isinstance(summary["validation_errors"], list)
            assert isinstance(stats["counts"], dict)
            assert isinstance(filtered_text, list)
            assert isinstance(filtered_diagram, list)
            assert isinstance(removed_bpe, list)
            assert all(isinstance(word, int) and 0 <= word <= WORD_MASK for _, word in iter_rows)
            assert all(isinstance(word, int) and 0 <= word <= WORD_MASK for word in filtered_text)
            assert all(isinstance(word, int) and 0 <= word <= WORD_MASK for word in filtered_diagram)
            assert all(isinstance(word, int) and 0 <= word <= WORD_MASK for word in removed_bpe)
            assert all(isinstance(word, int) and 0 <= word <= WORD_MASK for word in restored)

        except Exception as exc:  # pragma: no cover - explicit failure capture
            if len(crashes) < 10:
                crashes.append({"case_id": case_id, "class": klass, "exception": repr(exc)})

    assert not crashes, f"helper dirty campaign crashes={len(crashes)} samples={crashes}"
