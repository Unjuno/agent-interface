"""Independent raw-only audit for Issue #6079; does not import candidate code."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path


def _pgm(encoded: str) -> tuple[int, bytes]:
    raw = base64.b64decode(encoded, validate=True)
    p = raw.split(b"\n", 3)
    if len(p) != 4 or p[0] != b"P5" or p[2] != b"255":
        raise ValueError("bad pgm")
    w, h = [int(x) for x in p[1].split()]
    if len(p[3]) != w * h:
        raise ValueError("bad raster length")
    return w, p[3]


def _rel(encoded: str) -> tuple[float, float]:
    width, pixels = _pgm(encoded)
    ts, bs = [], []
    for pos, value in enumerate(pixels):
        x, y = pos % width, pos // width
        if value == 240:
            ts.append((x, y))
        elif value in (100, 101, 102):
            bs.append((x, y))
    if not ts or not bs:
        raise ValueError("missing visible feature")
    return (sum(x for x, _ in ts) / len(ts) - sum(x for x, _ in bs) / len(bs),
            sum(y for _, y in ts) / len(ts) - sum(y for _, y in bs) / len(bs))


def evaluate(visible: dict, truth: dict, candidate: dict) -> list[str]:
    errors = []
    vp = visible.get("pairs", [])
    tp = truth.get("pairs", [])
    cr = candidate.get("results", [])
    if visible.get("schema") != "conditional-parallax-input-v1" or truth.get("schema") != "conditional-parallax-truth-v1":
        errors.append("schema_mismatch")
    if len(vp) != 9 or len(tp) != 9 or len(cr) != 9:
        errors.append("nine_pair_denominator_mismatch")
    if len({p.get("pair_id") for p in vp}) != len(vp) or len({p.get("pair_id") for p in tp}) != len(tp):
        errors.append("duplicate_pair_id")
    by_truth = {p.get("pair_id"): p for p in tp}
    by_result = {r.get("pair_id"): r for r in cr}
    if set(by_truth) != {p.get("pair_id") for p in vp} or set(by_result) != set(by_truth):
        errors.append("pair_identity_join_mismatch")
    counts = {"screen_overlay": 0, "sham": 0, "world_match": 0}
    for p in vp:
        pid = p.get("pair_id")
        t = by_truth.get(pid)
        r = by_result.get(pid)
        if t is None or r is None:
            continue
        family = t.get("family")
        if family not in counts:
            errors.append(f"unknown_family:{pid}")
            continue
        counts[family] += 1
        expected_truth = {
            "screen_overlay": ["approach_contact", "screen_overlay_no_contact"],
            "sham": ["approach_contact", "screen_overlay_no_contact"],
            "world_match": ["approach_contact", "world_anchored_sprite_no_contact"],
        }[family]
        if t.get("member_truth") != expected_truth or t.get("contact_time_ms") != [1000, None]:
            errors.append(f"hidden_truth_contract:{pid}")
        expected_result = {
            "screen_overlay": "DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS",
            "sham": "UNKNOWN",
            "world_match": "UNKNOWN",
        }[family]
        if t.get("expected_disposition") != expected_result:
            errors.append(f"truth_disposition_contract:{pid}")
        members = p.get("members", [])
        if len(members) != 2:
            errors.append(f"member_count:{pid}")
            continue
        a, b = members
        af, bf = a.get("frames", []), b.get("frames", [])
        if len(af) != 8 or len(bf) != 8:
            errors.append(f"frame_count:{pid}")
            continue
        expected_hashes = t.get("frame_sha256", [])
        if len(expected_hashes) != 2 or any(len(row) != 8 for row in expected_hashes):
            errors.append(f"frame_hash_manifest_shape:{pid}")
        else:
            for member_index, frames in enumerate((af, bf)):
                for frame_index, frame in enumerate(frames):
                    try:
                        actual_hash = hashlib.sha256(base64.b64decode(frame.get("pgm_b64", ""), validate=True)).hexdigest()
                    except (ValueError, TypeError):
                        actual_hash = "INVALID"
                    if actual_hash != expected_hashes[member_index][frame_index]:
                        errors.append(f"frame_hash_mismatch:{pid}:{member_index}:{frame_index}")
        if [x.get("t_ms") for x in af] != [x.get("t_ms") for x in bf] or [x.get("t_ms") for x in af] != [0, 125, 250, 375, 500, 625, 750, 875]:
            errors.append(f"timestamp_mismatch:{pid}")
            continue
        receipt = p.get("probe_receipt", {})
        if receipt.get("authority") != "none" or receipt.get("event_t_ms") != 500 or receipt.get("coordinate_frame") != "synthetic-world-x":
            errors.append(f"receipt_contract:{pid}")
        if receipt.get("actual_dx") != t.get("expected_actual_dx"):
            errors.append(f"actual_translation_truth_mismatch:{pid}")
        if any(x.get("source_binding", {}).get("viewport_generation") != 1 for x in af + bf):
            errors.append(f"source_binding_invalid:{pid}")
        passive_same = all(x.get("pgm_b64") == y.get("pgm_b64") for x, y in zip(af[:5], bf[:5], strict=True))
        whole_same = all(x.get("pgm_b64") == y.get("pgm_b64") for x, y in zip(af, bf, strict=True))
        if not passive_same:
            errors.append(f"passive_equivalence_failed:{pid}")
        if family == "screen_overlay":
            if receipt.get("actual_dx") == 0 or whole_same:
                errors.append(f"positive_probe_not_discriminating:{pid}")
            if r.get("classification") != "DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS":
                errors.append(f"positive_candidate_disposition:{pid}")
        elif family == "sham":
            if receipt.get("actual_dx") != 0 or not whole_same:
                errors.append(f"sham_not_observationally_equivalent:{pid}")
            if r.get("classification") != "UNKNOWN":
                errors.append(f"sham_not_unknown:{pid}")
        else:
            if receipt.get("actual_dx") == 0 or not whole_same:
                errors.append(f"world_match_not_equivalent:{pid}")
            if r.get("classification") != "UNKNOWN":
                errors.append(f"world_match_not_unknown:{pid}")
        # Independent reconstruction of the candidate's visible-feature statistic.
        if r.get("authority") is not False or r.get("contact_claim") is not False:
            errors.append(f"authority_or_contact_claim:{pid}")
        if not whole_same and receipt.get("actual_dx") != 0:
            delta = 0.0
            for x, y in zip(af[5:], bf[5:], strict=True):
                rx, ry = _rel(x["pgm_b64"]), _rel(y["pgm_b64"])
                delta = max(delta, ((rx[0] - ry[0]) ** 2 + (rx[1] - ry[1]) ** 2) ** 0.5)
            if abs(delta - float(r.get("max_relative_separation_px", -999))) > 1e-5:
                errors.append(f"candidate_statistic_mismatch:{pid}")
    if counts != {"screen_overlay": 3, "sham": 3, "world_match": 3}:
        errors.append("family_denominator_mismatch")
    return errors


def run(visible: dict, truth: dict, candidate: dict) -> dict:
    base_errors = evaluate(visible, truth, candidate)
    controls = {}
    # Controls operate on deep JSON copies; frozen candidate/input bytes are untouched.
    mutations = {}
    mutations["altered_probe_receipt"] = json.loads(json.dumps(visible))
    mutations["altered_probe_receipt"]["pairs"][0]["probe_receipt"]["actual_dx"] += 0.4
    mutations["swapped_truth_label"] = json.loads(json.dumps(truth))
    mutations["swapped_truth_label"]["pairs"][0]["member_truth"].reverse()
    mutations["sham_mislabeled_as_movement"] = json.loads(json.dumps(truth))
    mutations["sham_mislabeled_as_movement"]["pairs"][3]["expected_actual_dx"] = 0.85
    mutations["one_frame_mismatch"] = json.loads(json.dumps(visible))
    damaged = mutations["one_frame_mismatch"]["pairs"][0]["members"][0]["frames"][6]
    raw = base64.b64decode(damaged["pgm_b64"], validate=True)
    header, raster = raw.split(b"\n", 3)[:3], raw.split(b"\n", 3)[3]
    pixels = bytearray(raster)
    pixels[-1] ^= 1
    damaged["pgm_b64"] = base64.b64encode(b"\n".join(header) + b"\n" + bytes(pixels)).decode("ascii")
    for name, mutant in mutations.items():
        controls[name] = bool(evaluate(mutant, truth, candidate))
    return {"schema": "conditional-parallax-audit-v1", "base_errors": base_errors, "mutation_controls_rejected": controls, "control_count": len(controls), "all_controls_rejected": all(controls.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("truth", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    v = json.loads(args.input.read_text(encoding="utf-8"))
    t = json.loads(args.truth.read_text(encoding="utf-8"))
    c = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = run(v, t, c)
    args.output.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"base_errors={len(result['base_errors'])} mutation_controls_rejected={sum(result['mutation_controls_rejected'].values())}/{result['control_count']}")
    return 0 if not result["base_errors"] and result["all_controls_rejected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
