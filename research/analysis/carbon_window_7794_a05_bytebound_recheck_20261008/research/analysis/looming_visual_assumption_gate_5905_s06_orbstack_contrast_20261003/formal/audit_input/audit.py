#!/usr/bin/env python3
"""Independent raw-only audit; intentionally does not import candidate.py."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import sys
from pathlib import Path


def pixels(path):
    raw = path.read_bytes()
    if raw[:3] != b"P5\n":
        raise ValueError("bad-magic")
    header, data = raw.split(b"255\n", 1)
    _, dims = header.split(b"P5\n", 1)
    width, height = map(int, dims.split())
    if len(data) != width * height:
        raise ValueError("bad-length")
    return width, height, data, hashlib.sha256(raw).hexdigest()


def blobs(width, height, data):
    # Independent scanline flood fill with 8-neighbour connectivity.
    marked = set()
    result = []
    for pos, grey in enumerate(data):
        if grey <= 127 or pos in marked:
            continue
        todo = [pos]
        marked.add(pos)
        xs, ys = [], []
        while todo:
            cur = todo.pop()
            y, x = divmod(cur, width)
            xs.append(x)
            ys.append(y)
            for ny in range(max(y - 1, 0), min(y + 2, height)):
                for nx in range(max(x - 1, 0), min(x + 2, width)):
                    nxt = ny * width + nx
                    if data[nxt] > 127 and nxt not in marked:
                        marked.add(nxt)
                        todo.append(nxt)
        if len(xs) >= 9:
            result.append((sum(xs) / len(xs), sum(ys) / len(ys), len(xs)))
    return result


def binary_mask(path):
    width, height, data, _ = pixels(path)
    return width, height, bytes(v >= 128 for v in data)


def reconstruct(root, row):
    w0, h0, p0, hash0 = pixels(root / row["frame0"])
    w1, h1, p1, hash1 = pixels(root / row["frame1"])
    if (w0, h0, w1, h1) != (128, 128, 128, 128):
        return {"geometry": "UNKNOWN", "why": "dimensions"}
    x0 = [c for c in blobs(w0, h0, p0) if math.hypot(c[0] - 64, c[1] - 64) < 40]
    x1 = [c for c in blobs(w1, h1, p1) if math.hypot(c[0] - 64, c[1] - 64) < 48]
    a0 = [c for c in blobs(w0, h0, p0) if math.hypot(c[0] - 64, c[1] - 64) > 65]
    a1 = [c for c in blobs(w1, h1, p1) if math.hypot(c[0] - 64, c[1] - 64) > 65]
    out = {"frame_sha256": [hash0, hash1], "target_counts": [len(x0), len(x1)],
           "anchor_counts": [len(a0), len(a1)]}
    if len(a0) < 4 or len(a1) < 4:
        return {**out, "geometry": "UNKNOWN", "why": "anchors-missing"}
    if len(x0) != 7 or len(x1) != 7:
        return {**out, "geometry": "REJECT", "why": "feature-count"}
    center0 = (sum(c[0] for c in x0) / 7, sum(c[1] for c in x0) / 7)
    center1 = (sum(c[0] for c in x1) / 7, sum(c[1] for c in x1) / 7)
    if math.dist(center0, center1) > 2:
        return {**out, "geometry": "REJECT", "why": "center-shift"}
    free = list(x1)
    rates, area_change = [], []
    for px, py, area in x0:
        idx = min(range(len(free)), key=lambda j: (free[j][0] - px) ** 2 + (free[j][1] - py) ** 2)
        qx, qy, qarea = free.pop(idx)
        before = math.hypot(px - 64, py - 64)
        after = math.hypot(qx - 64, qy - 64)
        if before <= 3:
            continue
        rates.append(after / before)
        area_change.append(qarea / area)
    rate = sorted(rates)[len(rates) // 2]
    spread = sorted(abs(v - rate) for v in rates)[len(rates) // 2]
    if spread > .10:
        return {**out, "geometry": "REJECT", "why": "radial-incoherence"}
    if max(area_change) - min(area_change) > .25:
        return {**out, "geometry": "REJECT", "why": "component-shape"}
    anchor_motion = max(min(math.dist(u[:2], v[:2]) for v in a1) for u in a0)
    if anchor_motion > 2:
        return {**out, "geometry": "REJECT", "why": "anchor-drift"}
    # A 180-degree counterpart for every baseline feature is an explicit
    # ambiguity warning, not a semantic approach/rigid-growth classifier.
    paired = []
    for x, y, _ in x0:
        ds = [math.hypot((ox + x) - 128, (oy + y) - 128) for ox, oy, _ in x0]
        paired.append(min(ds) <= 2)
    if len(x0) >= 6 and all(paired):
        return {**out, "geometry": "UNKNOWN", "why": "radial-ambiguity"}
    dt = row["t"][1] - row["t"][0]
    tau = dt / (rate - 1) if rate > 1 else math.inf
    return {**out, "geometry": "CUE" if rate >= 1.2 and tau <= .30 else "REJECT",
            "scale": rate, "tau_s": tau, "why": "independent-image-replay"}


def audit(truth, public, candidate, root, challenge=True):
    assert len(truth["rows"]) == len(public["rows"]) == len(candidate["rows"]) == 36
    expected_ids = [r["opaque_id"] for r in public["rows"]]
    assert [r["opaque_id"] for r in candidate["rows"]] == expected_ids
    public_by_id = {r["opaque_id"]: r for r in public["rows"]}
    by_id = {r["opaque_id"]: r for r in candidate["rows"]}
    replay = {}
    eligible_ok = []
    visible_controls = 0
    rejected = unknown = 0
    for row in truth["rows"]:
        decision = by_id[row["opaque_id"]]
        observed = public_by_id[row["opaque_id"]]
        assert observed["t"] == row["t"] and observed["epoch"] == row["epoch"], "timestamp-epoch"
        assert [observed["frame0"], observed["frame1"]] == [row["frame0"], row["frame1"]], "frame-path"
        derived = reconstruct(root, row)
        assert derived["frame_sha256"] == row["sha256"], "frame-hash"
        if row["truth"] == "eligible_approach":
            assert derived["geometry"] == "CUE", (row["truth"], derived)
            assert decision["decision"] == "CUE", (row["truth"], decision)
            assert abs(decision["tau_s"] - derived["tau_s"]) <= .06, "ttc-error"
            assert decision["simulated_release"] is True and decision["safe"] is False
            eligible_ok.append(row["opaque_id"])
        else:
            assert decision["decision"] in ("REJECT", "UNKNOWN"), (row["truth"], decision)
            assert not decision.get("simulated_release", False), "false-release"
            if row["truth"] in ("missing_anchors", "pixel_indistinguishable_approach",
                                  "pixel_indistinguishable_rigid_growth"):
                assert decision["decision"] == "UNKNOWN", (row["truth"], decision)
            if row["truth"] not in ("pixel_indistinguishable_approach",
                                     "pixel_indistinguishable_rigid_growth"):
                visible_controls += 1
            if decision["decision"] == "REJECT":
                rejected += 1
            else:
                unknown += 1
        replay[row["opaque_id"]] = {"truth": row["truth"], **derived,
                                     "candidate": decision}
    assert all(r.get("safe") is False for r in candidate["rows"]), "safe-bit"

    by_family = {}
    by_truth = {}
    for row in truth["rows"]:
        by_family.setdefault(row["family_id"], {})[row["variant"]] = row
        by_truth.setdefault((row["variant"], row["truth"]), []).append(row)
    for family, variants in by_family.items():
        native = variants["native"]
        for variant in ("low_contrast", "near_threshold"):
            changed = variants[variant]
            for frame_key in ("frame0", "frame1"):
                assert binary_mask(root / native[frame_key]) == binary_mask(root / changed[frame_key]), "threshold-mask-drift"
            base_decision = by_id[native["opaque_id"]]
            changed_decision = by_id[changed["opaque_id"]]
            assert {k: v for k, v in base_decision.items() if k != "opaque_id"} == {
                k: v for k, v in changed_decision.items() if k != "opaque_id"}, "photometric-decision-drift"
    for variant in ("native", "low_contrast", "near_threshold"):
        pair = [by_id[row["opaque_id"]] for truth_name in
                ("pixel_indistinguishable_approach", "pixel_indistinguishable_rigid_growth")
                for row in by_truth[(variant, truth_name)]]
        pair_decisions = [{k: v for k, v in r.items() if k != "opaque_id"} for r in pair]
        assert len(pair_decisions) == 2 and pair_decisions[0] == pair_decisions[1]
        assert pair[0]["decision"] == "UNKNOWN", "pair-equivalence"

    checks = {}
    if challenge:
        mutants = []
        m = copy.deepcopy(truth)
        m["rows"][0]["sha256"][0] = "0" * 64
        mutants.append(("frame_hash", m, public, candidate))
        m = copy.deepcopy(public)
        m["rows"][0]["t"][1] += .2
        mutants.append(("timestamp", truth, m, candidate))
        m = copy.deepcopy(candidate)
        m["rows"][0]["decision"] = "REJECT"
        mutants.append(("classification", truth, public, m))
        m = copy.deepcopy(candidate)
        m["rows"][0]["safe"] = True
        mutants.append(("safe_bit", truth, public, m))
        m = copy.deepcopy(candidate)
        m["rows"][-1]["decision"] = "REJECT"
        mutants.append(("pair_equivalence", truth, public, m))
        for name, tdoc, pdoc, cdoc in mutants:
            try:
                audit(tdoc, pdoc, cdoc, root, challenge=False)
            except (AssertionError, KeyError, ValueError, ZeroDivisionError):
                checks[name] = True
            else:
                checks[name] = False
        assert all(checks.values()), checks
    return {"schema": "looming-contrast-audit-v1", "rows_reconstructed": len(replay),
            "eligible_pass": len(eligible_ok), "visible_controls_rejected": rejected,
            "visible_controls_no_cue": visible_controls,
            "visible_controls_total": visible_controls,
            "unknown_controls": unknown, "pair_equivalent_unknown_variants": 3,
            "photometric_invariance_families": len(by_family),
            "false_safe": 0, "mutation_rejections": checks, "replay": replay,
            "audit_errors": 0}


def main():
    root = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    result = audit(json.loads((root / "truth.json").read_text()),
                   json.loads((root / "candidate_input.json").read_text()),
                   json.loads((root / "candidate.json").read_text()), root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
