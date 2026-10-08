"""One-shot hostile foreground perturbation for the frozen #6079 candidate."""
from __future__ import annotations

import base64
import copy
import json
import sys
from pathlib import Path

PARENT = Path(__file__).resolve().parent.parent / "conditional_parallax_6079_t0_v1_20261003"
sys.path.insert(0, str(PARENT))
import candidate  # noqa: E402


def decode(encoded: str) -> tuple[bytes, bytearray]:
    raw = base64.b64decode(encoded, validate=True)
    head, pixels = raw.split(b"\n", 3)[:3], raw.split(b"\n", 3)[3]
    return raw[: len(raw) - len(pixels)], bytearray(pixels)


def encode(header: bytes, pixels: bytearray) -> str:
    return base64.b64encode(header + bytes(pixels)).decode("ascii")


def target_coordinates(encoded: str) -> list[int]:
    _, pixels = decode(encoded)
    return [i for i, value in enumerate(pixels) if value == candidate.TARGET]


def run() -> dict:
    parent_input = json.loads((PARENT / "candidate_input.json").read_text())
    pair = copy.deepcopy(parent_input["pairs"][3])  # frozen sham pair 04
    pair["pair_id"] = "foreground-dominance-control-a01"
    pair["probe_receipt"]["actual_dx"] = 0.85
    left, right = pair["members"]
    for frame in right["frames"][5:]:
        header, pixels = decode(frame["pgm_b64"])
        for y in range(8, 20):
            for x in range(8, 48):
                pixels[y * 128 + x] = 100
        frame["pgm_b64"] = encode(header, pixels)
    return {"schema": parent_input["schema"], "pairs": [pair]}


if __name__ == "__main__":
    one_pair = run()
    out = Path(__file__).resolve().parent / "probe_input.json"
    out.write_text(json.dumps(one_pair, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"prepared_pairs={len(one_pair['pairs'])} frames_per_member={len(one_pair['pairs'][0]['members'][0]['frames'])}")
