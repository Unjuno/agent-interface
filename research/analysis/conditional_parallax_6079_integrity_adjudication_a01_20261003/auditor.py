"""Independent post-hoc integrity audit; never imports/runs either parent program."""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "conditional_parallax_6079_t0_v1_20261003"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pgm(encoded: str) -> tuple[int, int, bytes]:
    raw = base64.b64decode(encoded, validate=True)
    magic, dims, maximum, data = raw.split(b"\n", 3)
    if magic != b"P5" or maximum != b"255":
        raise ValueError("bad_pgm_header")
    width, height = (int(x) for x in dims.split())
    if len(data) != width * height:
        raise ValueError("bad_pgm_length")
    return width, height, data


def rel(encoded: str) -> tuple[float, float]:
    width, _, data = pgm(encoded)
    target = [(i % width, i // width) for i, value in enumerate(data) if value == 240]
    background = [(i % width, i // width) for i, value in enumerate(data) if value in (100, 101, 102)]
    if not target or not background:
        raise ValueError("missing_feature")
    return (sum(x for x, _ in target) / len(target) - sum(x for x, _ in background) / len(background),
            sum(y for _, y in target) / len(target) - sum(y for _, y in background) / len(background))


def reject_visible_truth_mismatch(visible: dict, truth: dict) -> bool:
    by_truth = {p["pair_id"]: p for p in truth["pairs"]}
    for pair in visible["pairs"]:
        t = by_truth.get(pair["pair_id"])
        if t is None or pair["probe_receipt"].get("actual_dx") != t.get("expected_actual_dx"):
            return True
    return False


def reject_truth_label_corruption(visible: dict, truth: dict) -> bool:
    contracts = {
        "screen_overlay": ["approach_contact", "screen_overlay_no_contact"],
        "sham": ["approach_contact", "screen_overlay_no_contact"],
        "world_match": ["approach_contact", "world_anchored_sprite_no_contact"],
    }
    return any(p.get("member_truth") != contracts.get(p.get("family")) for p in truth["pairs"])


def audit() -> dict:
    freeze = json.loads((PARENT / "FREEZE.json").read_text())
    manifest = {}
    for line in (PARENT / "SHA256SUMS.txt").read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        manifest[relative.strip()] = digest
    checked_files = ["PREREG.md", "fixture.py", "candidate.py", "auditor.py", "test_method.py",
                     "FREEZE.json", "candidate_input.json", "truth_sidecar.json", "candidate_output.json",
                     "audit_output.json"]
    actual = {name: sha(PARENT / name) for name in checked_files}
    frozen_sources = freeze["source_sha256"]
    frozen_inputs = freeze["input_sha256"]
    frozen_names = list(frozen_sources) + list(frozen_inputs)
    frozen_ok = {name: actual[name] == frozen_sources.get(name, frozen_inputs.get(name)) for name in frozen_names}
    manifest_names = [name for name in checked_files if name in manifest]
    manifest_ok = {name: actual[name] == manifest[name] for name in manifest_names}

    visible = json.loads((PARENT / "candidate_input.json").read_text())
    truth = json.loads((PARENT / "truth_sidecar.json").read_text())
    output = json.loads((PARENT / "candidate_output.json").read_text())
    rows = {r["pair_id"]: r for r in output["results"]}
    truths = {t["pair_id"]: t for t in truth["pairs"]}
    base_errors = []
    background_pixel_counts = []
    independently_reconstructed = []
    for pair in visible["pairs"]:
        pid = pair["pair_id"]
        t, row = truths.get(pid), rows.get(pid)
        if t is None or row is None:
            base_errors.append(f"missing_join:{pid}")
            continue
        members = pair["members"]
        if len(members) != 2 or any(len(m["frames"]) != 8 for m in members):
            base_errors.append(f"shape:{pid}")
            continue
        frames_a, frames_b = members[0]["frames"], members[1]["frames"]
        if any(frames_a[i]["pgm_b64"] != frames_b[i]["pgm_b64"] for i in range(5)):
            base_errors.append(f"passive_mismatch:{pid}")
        for mi, member in enumerate(members):
            for fi, frame in enumerate(member["frames"]):
                raw = base64.b64decode(frame["pgm_b64"], validate=True)
                expected = t["frame_sha256"][mi][fi]
                if hashlib.sha256(raw).hexdigest() != expected:
                    base_errors.append(f"truth_frame_hash:{pid}:{mi}:{fi}")
        distinct = []
        for frame in frames_a:
            _, _, pixels = pgm(frame["pgm_b64"])
            distinct.append(sum(v in (100, 101, 102) for v in pixels))
        background_pixel_counts.extend(distinct)
        max_sep = 0.0
        for fa, fb in zip(frames_a[5:], frames_b[5:], strict=True):
            ax, ay = rel(fa["pgm_b64"])
            bx, by = rel(fb["pgm_b64"])
            max_sep = max(max_sep, ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5)
        expected_class = ("DISTINGUISHED_UNDER_RIGID_OVERLAY_ASSUMPTIONS"
                          if pair["probe_receipt"]["actual_dx"] != 0 and max_sep >= 2.0 else "UNKNOWN")
        if row.get("classification") != expected_class:
            base_errors.append(f"output_reconstruction:{pid}")
        independently_reconstructed.append({"pair_id": pid, "max_separation_px": round(max_sep, 6),
                                             "observed": row.get("classification"), "reconstructed": expected_class})

    # Regenerate only fixture bytes. This establishes deterministic corpus identity;
    # it deliberately does not import or invoke candidate.run.
    fixture_spec = importlib.util.spec_from_file_location("parent_fixture_integrity_only", PARENT / "fixture.py")
    fixture = importlib.util.module_from_spec(fixture_spec)
    assert fixture_spec.loader is not None
    fixture_spec.loader.exec_module(fixture)
    rebuilt, rebuilt_truth = fixture.build()
    canonical = lambda obj: (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode()
    regenerated_visible_sha = hashlib.sha256(canonical(rebuilt)).hexdigest()
    regenerated_truth_sha = hashlib.sha256(canonical(rebuilt_truth)).hexdigest()

    test_text = (PARENT / "test_method.py").read_text()
    prefreeze_candidate_exposure_in_tests = bool(re.search(r"candidate\.run\(cls\.visible\)", test_text))
    controls = {}
    for name, mutate in (
        ("altered_probe_receipt", lambda v, t: v["pairs"][0]["probe_receipt"].__setitem__("actual_dx", v["pairs"][0]["probe_receipt"]["actual_dx"] + 0.4)),
        ("swapped_truth_label", lambda v, t: t["pairs"][0]["member_truth"].reverse()),
        ("sham_mislabeled_as_movement", lambda v, t: t["pairs"][3].__setitem__("expected_actual_dx", 0.85)),
        ("one_frame_pixel_alteration", lambda v, t: _flip_pixel(v["pairs"][0]["members"][0]["frames"][6])),
    ):
        mutant_v = json.loads(json.dumps(visible))
        mutant_t = json.loads(json.dumps(truth))
        mutate(mutant_v, mutant_t)
        if name == "swapped_truth_label":
            rejected = reject_truth_label_corruption(mutant_v, mutant_t)
        elif name == "one_frame_pixel_alteration":
            rejected = not _truth_frame_hashes_hold(mutant_v, truth)
        else:
            rejected = reject_visible_truth_mismatch(mutant_v, mutant_t)
        controls[name] = {"rejected": rejected, "route": "visible" if name in ("altered_probe_receipt", "one_frame_pixel_alteration") else "truth"}

    frozen_prereg_matches = frozen_ok["PREREG.md"]
    all_data_controls_rejected = all(x["rejected"] for x in controls.values())
    return {
        "schema": "conditional-parallax-integrity-adjudication-a01-v1",
        "parent_allocation": freeze["allocation_id"],
        "parent_candidate_invocations": 1,
        "candidate_invocations_in_this_adjudication": 0,
        "frozen_hash_checks": frozen_ok,
        "manifest_hash_checks": manifest_ok,
        "frozen_prereg_matches_delivered_bytes": frozen_prereg_matches,
        "delivered_prereg_sha256": actual["PREREG.md"],
        "freeze_expected_prereg_sha256": frozen_sources["PREREG.md"],
        "missing_original_source_bytes_reconstructed": False,
        "prefreeze_candidate_exposure_in_construction_tests": prefreeze_candidate_exposure_in_tests,
        "fixture_regeneration_matches_input": regenerated_visible_sha == freeze["input_sha256"]["candidate_input.json"],
        "fixture_regeneration_matches_truth": regenerated_truth_sha == freeze["input_sha256"]["truth_sidecar.json"],
        "parent_raw_reconstruction_errors": base_errors,
        "pair_reconstruction": independently_reconstructed,
        "visible_background_pixel_count_per_passive_member_a": background_pixel_counts[::8],
        "correctly_routed_mutation_controls": controls,
        "correctly_routed_mutation_controls_rejected": all_data_controls_rejected,
        "original_auditor_two_truth_control_routing_invalid": True,
        "disposition": "HOLD_PARENT_FORMAL_PROMOTION" if (not frozen_prereg_matches or prefreeze_candidate_exposure_in_tests or not all_data_controls_rejected or base_errors) else "PASS_RAW_RECONSTRUCTION_SCOPED",
        "interpretation": "Post-hoc raw reconstruction can corroborate the observed finite output, but cannot retroactively satisfy source-freeze identity or first-exposure ordering. Original 4/4 auditor control report is retained as history; two controls were misrouted and are not credited as valid controls."
    }


def _flip_pixel(frame: dict) -> None:
    raw = base64.b64decode(frame["pgm_b64"], validate=True)
    prefix, raster = raw.rsplit(b"\n", 1)
    pixels = bytearray(raster)
    pixels[-1] ^= 1
    frame["pgm_b64"] = base64.b64encode(prefix + b"\n" + pixels).decode()


def _truth_frame_hashes_hold(visible: dict, truth: dict) -> bool:
    by_truth = {p["pair_id"]: p for p in truth["pairs"]}
    for pair in visible["pairs"]:
        t = by_truth[pair["pair_id"]]
        for mi, member in enumerate(pair["members"]):
            for fi, frame in enumerate(member["frames"]):
                if hashlib.sha256(base64.b64decode(frame["pgm_b64"], validate=True)).hexdigest() != t["frame_sha256"][mi][fi]:
                    return False
    return True


if __name__ == "__main__":
    result = audit()
    (HERE / "audit_output.json").write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    print(f"disposition={result['disposition']} raw_errors={len(result['parent_raw_reconstruction_errors'])} corrected_controls={sum(v['rejected'] for v in result['correctly_routed_mutation_controls'].values())}/4 prereg_hash_match={result['frozen_prereg_matches_delivered_bytes']} candidate_calls=0")
