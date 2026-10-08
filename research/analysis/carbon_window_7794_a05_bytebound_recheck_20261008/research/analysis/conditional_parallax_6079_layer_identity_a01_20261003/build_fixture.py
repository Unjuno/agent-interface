"""Build the frozen public fixture and auditor-only truth for #6838."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def tracks(layer: str, xs0: list[int], xs1: list[int], *, source: str = "capture-A",
           frame0: str = "f0", frame1: str = "f1", provenance: str = "verified",
           ids: list[str] | None = None) -> list[dict]:
    ids = ids or [f"{layer}-{i}" for i in range(len(xs0))]
    return [
        {"track_id": track_id, "layer": layer, "membership": provenance,
         "source_id": source, "frame_ids": [frame0, frame1],
         "xy": [[x0, 0], [x1, 0]]}
        for track_id, x0, x1 in zip(ids, xs0, xs1, strict=True)
    ]


def pair(case_id: str, a: list[dict], b: list[dict], *, probe_status: str = "verified",
         probe_source: str = "capture-A", probe_frames: list[str] | None = None) -> dict:
    return {
        "case_id": case_id,
        "source_id": "capture-A",
        "frame_ids": ["f0", "f1"],
        "probe": {"status": probe_status, "source_id": probe_source,
                  "frame_ids": probe_frames or ["f0", "f1"], "intent_epoch": "e1"},
        "scenes": [{"scene_id": "left", "tracks": a}, {"scene_id": "right", "tracks": b}],
    }


def build() -> tuple[dict, dict]:
    # Formal values are intentionally disjoint from the construction mini-cases.
    base_t = [101, 119]
    base_b = [201, 221]
    base_f = [301, 331]
    cases = [
        pair("target-parallax-positive-1",
             tracks("target", base_t, [115, 133]) + tracks("background", base_b, [203, 223]),
             tracks("target", base_t, base_t) + tracks("background", base_b, base_b)),
        pair("target-parallax-positive-2",
             tracks("target", base_t, [119, 137]) + tracks("background", base_b, [205, 225]),
             tracks("target", base_t, [104, 122]) + tracks("background", base_b, base_b)),
        pair("foreground-dominance-sham",
             tracks("target", base_t, base_t) + tracks("background", base_b, base_b)
             + tracks("foreground", base_f, base_f),
             tracks("target", base_t, base_t) + tracks("background", base_b, base_b)
             + tracks("foreground", base_f, [385, 415])),
        pair("zero-relative-motion",
             tracks("target", base_t, [108, 126]) + tracks("background", base_b, [203, 223]),
             tracks("target", base_t, [108, 126]) + tracks("background", base_b, [203, 223])),
        pair("ambiguous-layer-membership",
             tracks("target", base_t, [115, 133], provenance="ambiguous")
             + tracks("background", base_b, base_b),
             tracks("target", base_t, base_t, provenance="ambiguous")
             + tracks("background", base_b, base_b)),
        pair("stale-track-identity",
             tracks("target", base_t, [115, 133]) + tracks("background", base_b, base_b),
             tracks("target", base_t, base_t, ids=["target-X", "target-Y"])
             + tracks("background", base_b, base_b)),
        pair("invalid-probe-receipt",
             tracks("target", base_t, [115, 133]) + tracks("background", base_b, base_b),
             tracks("target", base_t, base_t) + tracks("background", base_b, base_b),
             probe_status="unknown"),
        pair("insufficient-layer-support",
             tracks("target", [0], [12]) + tracks("background", base_b, base_b),
             tracks("target", [0], [0]) + tracks("background", base_b, base_b)),
    ]
    truth = {
        "schema": "conditional-parallax-layer-truth-v1",
        "cases": {
            "target-parallax-positive-1": {"expected": "DISTINGUISHED", "relative_dx": 12},
            "target-parallax-positive-2": {"expected": "DISTINGUISHED", "relative_dx": 11},
            "foreground-dominance-sham": {"expected": "UNKNOWN", "relative_dx": 0},
            "zero-relative-motion": {"expected": "UNKNOWN", "relative_dx": 0},
            "ambiguous-layer-membership": {"expected": "UNKNOWN", "relative_dx": None},
            "stale-track-identity": {"expected": "UNKNOWN", "relative_dx": None},
            "invalid-probe-receipt": {"expected": "UNKNOWN", "relative_dx": None},
            "insufficient-layer-support": {"expected": "UNKNOWN", "relative_dx": None},
        },
    }
    return {"schema": "conditional-parallax-layer-public-v1", "cases": cases}, truth


def write() -> None:
    public, truth = build()
    (ROOT / "fixture").mkdir(exist_ok=True)
    (ROOT / "fixture" / "public.json").write_text(
        json.dumps(public, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    (ROOT / "fixture" / "auditor_truth.json").write_text(
        json.dumps(truth, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write()
