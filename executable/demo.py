from __future__ import annotations

import json
from pathlib import Path
import sys

V0_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = V0_ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from zpe_multimodal import IMCDecoder, stream_summary
from zpe_multimodal.canonical_demo import build_canonical_demo_stream, runtime_voice_capability_mode


def main() -> None:
    stream = build_canonical_demo_stream(require_env=False)

    result = IMCDecoder().decode(stream)
    summary = stream_summary(stream)
    counts = result.modality_counts

    for key in ("text", "diagram", "music", "voice", "image", "bpe", "mental", "touch", "smell", "taste"):
        assert counts[key] > 0, f"missing modality count for {key}"

    assert len(stream) >= 50, f"unexpectedly small stream ({len(stream)} words)"
    assert max(counts.values()) / len(stream) <= 0.9, "single-modality dominance exceeds 90%"

    print("STREAM_SUMMARY")
    print(json.dumps(summary, sort_keys=True))
    print("MODALITY_COUNTS")
    print(json.dumps(counts, sort_keys=True))
    print("VOICE_CAPABILITY_MODE")
    print(json.dumps({"voice_capability_mode": runtime_voice_capability_mode()}, sort_keys=True))
    print("DECODED_TEXT")
    print(result.text)


if __name__ == "__main__":
    main()
