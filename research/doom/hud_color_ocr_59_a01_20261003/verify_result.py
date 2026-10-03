"""Saved-only closeout verification and deterministic result derivation; no OCR."""
import argparse
import datetime
import hashlib
import json
import math
import statistics
from pathlib import Path
from auditor import audit

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parents[2] / "research/doom/results/map01-v39-coast-liveness-live-01/runtime"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(name):
    return json.loads((ROOT / name).read_text())

def require(condition, message):
    if not condition:
        raise ValueError(message)

def derive():
    frozen, selection, truth = read("FREEZE.json"), read("SELECTION.json"), read("TRUTH.json")
    for name, digest in {**frozen["source_sha256"], **frozen["input_sha256"]}.items():
        require(sha(ROOT / name) == digest, "frozen source/input: " + name)
    frozen_time = datetime.datetime.fromisoformat(frozen["created_utc"])
    selected_time = datetime.datetime.fromisoformat(selection["created_utc"])
    bindings = {"FREEZE.json": sha(ROOT / "FREEZE.json"), "SELECTION.json": sha(ROOT / "SELECTION.json")}
    counts = {}
    engine = None
    for phase in ("pilot", "evaluation"):
        raw_name, audit_name = f"runs/{phase}_candidate/raw.json", f"runs/{phase}_auditor/audit.json"
        raw = read(raw_name)
        reconstructed = audit(raw, truth, phase, ROOT / f"input/{phase}", SOURCE)
        require(reconstructed == read(audit_name), "saved auditor disagrees")
        expected = ["gray", "red", "red_excess"] if phase == "pilot" else ["gray", selection["selected"]]
        require(raw["transforms"] == expected, "phase transform contract")
        current_engine = {key: raw[key] for key in ("python", "pillow", "tesseract", "traineddata_sha256")}
        require(engine is None or engine == current_engine, "calibration/evaluation engine drift")
        engine = current_engine
        challenge = read(f"CHALLENGE_{phase}.json")
        require(challenge["status"] == "PASS_8_SAVED_MUTATIONS" and challenge["original"] == reconstructed,
                "saved mutation challenge outcome")
        names = {"duplicate_id", "normalized_digits", "reference_health", "crop_hash", "negative_duration",
                 "missing_prediction", "memory_bound", "missing_source_row"}
        require(len(challenge["cases"]) == 8 and {c["case"] for c in challenge["cases"]} == names
                and all(c["rejected"] for c in challenge["cases"]), "mutation cases")
        counts[phase] = reconstructed["counts"]
        for name in (raw_name, audit_name, f"CHALLENGE_{phase}.json"):
            bindings[name] = sha(ROOT / name)
        for role in ("candidate", "auditor"):
            name = f"runs/{phase}_{role}/receipt.json"
            receipt = read(name)
            require(receipt["phase"] == phase and receipt["role"] == role, "receipt role")
            require(receipt["run"]["exit"] == 0 and receipt["terminal_inspection"]["exit"] == 0, "stage exit")
            require(receipt["freeze_sha256"] == bindings["FREEZE.json"], "receipt freeze")
            require(receipt["selection_sha256"] == (bindings["SELECTION.json"] if phase == "evaluation" else None),
                    "receipt selection")
            start = datetime.datetime.fromisoformat(receipt["started_utc"])
            require(start >= frozen_time and (phase != "evaluation" or start >= selected_time), "freeze order")
            if phase == "pilot":
                require(start + datetime.timedelta(seconds=receipt["elapsed_ns"] / 1e9) <= selected_time,
                        "selection precedes calibration closeout")
            container = json.loads(receipt["terminal_inspection"]["stdout"])[0]
            state, config = container["State"], container["HostConfig"]
            require(container["Image"] == frozen["image_id"] and container["Config"]["Labels"]["study.owner"] == frozen["owner"],
                    "container ownership/image")
            require(container["Name"] == f"/hud59-5ce3-{phase}-{role}" and state["Status"] == "exited"
                    and not state["Running"] and not state["OOMKilled"] and state["ExitCode"] == 0, "terminal container")
            require(config["NetworkMode"] == "none" and config["ReadonlyRootfs"] and config["NanoCpus"] == 1_000_000_000
                    and config["Memory"] == config["MemorySwap"] == 536_870_912 and config["PidsLimit"] == 64
                    and config["CapDrop"] == ["ALL"] and "no-new-privileges" in config["SecurityOpt"], "Docker bounds")
            destinations = {bind.rsplit(":", 2)[1] for bind in config["Binds"]}
            require(destinations == ({"/input", "/out", "/code/candidate.py"} if role == "candidate" else
                                     {"/input", "/out", "/code/auditor.py", "/raw", "/truth/TRUTH.json", "/source"}),
                    "candidate/auditor mount separation")
            require(all(bind.endswith(":ro") for bind in config["Binds"] if bind.rsplit(":", 2)[1] != "/out"), "read-only inputs")
            bindings[name] = sha(ROOT / name)
    require(selection["pilot_raw_sha256"] == bindings["runs/pilot_candidate/raw.json"]
            and selection["pilot_audit_sha256"] == bindings["runs/pilot_auditor/audit.json"]
            and selection["pilot_counts"] == counts["pilot"], "selection source")
    require(selection["selected"] == max(("red", "red_excess"), key=lambda m: counts["pilot"][m]["exact"]), "selection rule")
    baseline, selected = counts["evaluation"]["gray"], counts["evaluation"][selection["selected"]]
    require(baseline["n"] == selected["n"] == 204, "evaluation size")
    exact, wrong = selected["exact"] / 204, selected["wrong_nonempty"] / 204
    gain = (selected["exact"] - baseline["exact"]) / 204
    gate = {"exact_at_least_95_percent": exact >= frozen["eligibility"]["exact_fraction_min"],
            "nonempty_wrong_at_most_1_percent": wrong <= frozen["eligibility"]["wrong_nonempty_fraction_max"],
            "gain_at_least_25_percentage_points": gain >= frozen["eligibility"]["gain_fraction_min"]}
    raw = read("runs/evaluation_candidate/raw.json")
    latency = {}
    for method in raw["transforms"]:
        values = sorted(row["predictions"][method]["elapsed_ns"] / 1e6 for row in raw["rows"])
        latency[method] = {"median": statistics.median(values), "p95_nearest_rank": values[math.ceil(.95 * len(values))-1], "max": max(values)}
    return {"status": "PASS_FINITE_REFERENCE_AGREEMENT_GATE" if all(gate.values()) else "FAIL_FINITE_REFERENCE_AGREEMENT_GATE",
            "evidence_status": "PASS_SAVED_OUTPUT_PROVENANCE_RUNTIME_AND_ARITHMETIC",
            "selected": selection["selected"], "counts": counts, "gate": gate,
            "evaluation_fractions": {"exact": exact, "wrong_nonempty": wrong, "gain": gain},
            "latency_ms": latency, "engine": engine, "evidence_sha256": bindings,
            "derivation_sha256": sha(ROOT / "verify_result.py"),
            "scope": {"reference_ground_truth_independent": False, "held_out_episodes": False,
                      "live_game_or_input": False, "independent_useful_onset_established": False,
                      "issue_59_live_gate_closed": False}}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true", help="exclusive-create derived RESULT; otherwise verify saved RESULT")
    args = parser.parse_args()
    result = derive()
    if args.create:
        with (ROOT / "RESULT.json").open("x") as stream:
            json.dump(result, stream, indent=2); stream.write("\n")
    else:
        require(result == read("RESULT.json"), "derived result drift")
    print(json.dumps({key: result[key] for key in ("status", "evidence_status", "counts", "gate")}))

if __name__ == "__main__":
    main()
