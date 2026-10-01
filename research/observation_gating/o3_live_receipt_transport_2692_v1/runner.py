"""One-shot live X11 receipt transport experiment; no input or model API exists here."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "o3_relevant_region_successor_v1"))
from adapter import evaluate_delivery
from transport import LiveTransport

OUT = Path(os.environ.get("O3_OUT", "/out"))
DISPLAY_NAME = os.environ.get("DISPLAY", ":99")
SCHEDULE = json.loads((HERE / "case_schedule.json").read_text())


def dump_line(path, row):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def alter(case, receipt, trusted, source_id):
    value = copy.deepcopy(receipt)
    if case == "stale_frame":
        value["observation_id"] = "prior-observation"
    elif case == "missing_region":
        value["region_id"] = "missing-region"
    elif case == "partial_coverage":
        value["coverage"] = "PARTIAL"
    elif case == "focus_window_change":
        value["source_window"] = int(trusted["xid"]) + 999
        value["focus_xid"] = int(trusted["xid"]) + 999
    elif case == "generation_mismatch":
        value["source_generation"] = "generation-from-another-process"
    elif case == "malformed_receipt":
        return ["receipt-not-a-mapping"]
    elif case == "authority_bearing":
        value["authority_grants"] = 1
    elif case == "contradictory_effect_binding":
        value["effect_binding_ref"] = "0" * 64
    return value


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "frames").mkdir(exist_ok=True)
    (OUT / "meta").mkdir(exist_ok=True)
    for name in ("raw_events.jsonl", "deliveries.jsonl", "decisions.jsonl"):
        (OUT / name).write_text("", encoding="utf-8")
    xvfb = subprocess.Popen(["Xvfb", DISPLAY_NAME, "-screen", "0", "1200x500x24", "-nolisten", "tcp"],
                            stdout=(OUT / "xvfb.log").open("wb"), stderr=subprocess.STDOUT)
    fixtures = []
    transport = None
    try:
        time.sleep(0.5)
        for surface in SCHEDULE["surfaces"]:
            proc = subprocess.Popen([sys.executable, str(HERE / "gtk_fixture.py"), "--surface", surface,
                                     "--meta", str(OUT / "meta" / f"{surface}.json")],
                                    stdout=(OUT / f"{surface}.log").open("wb"), stderr=subprocess.STDOUT)
            fixtures.append(proc)
        deadline = time.monotonic() + 10
        while not all((OUT / "meta" / f"{surface}.json").exists() for surface in SCHEDULE["surfaces"]):
            if time.monotonic() > deadline:
                raise TimeoutError("GTK fixtures did not publish XIDs")
            if any(p.poll() is not None for p in fixtures) or xvfb.poll() is not None:
                raise RuntimeError("Xvfb or fixture exited before first capture")
            time.sleep(0.05)
        surfaces = {s: json.loads((OUT / "meta" / f"{s}.json").read_text()) for s in SCHEDULE["surfaces"]}
        transport = LiveTransport(DISPLAY_NAME, OUT / "raw_events.jsonl", OUT / "frames", "frames")
        counts = {}
        intent_epoch = 0
        for surface in SCHEDULE["surfaces"]:
            trusted = surfaces[surface]
            for region_id, rect in SCHEDULE["regions"].items():
                for case in SCHEDULE["cases"]:
                    intent_epoch += 1
                    request = {"observation_id": str(uuid.uuid4()), "intent_epoch": intent_epoch,
                               "region_id": region_id, "region_rect": rect,
                               "max_receipt_age_ns": SCHEDULE["max_receipt_age_ns"],
                               "surface": surface, "case": case,
                               "trusted_xid": trusted["xid"]}
                    raw = transport.capture(request, trusted)
                    full = (OUT / raw["receipt"]["full_frame_path"]).read_bytes()
                    region = (OUT / raw["receipt"]["region_frame_path"]).read_bytes()
                    delivered = alter(case, raw["receipt"], trusted, raw["capture_id"])
                    if isinstance(delivered, dict):
                        delivered["observation_id"] = ("prior-observation" if case == "stale_frame"
                                                       else delivered["observation_id"])
                    arrival_ns = time.monotonic_ns()
                    dump_line(OUT / "deliveries.jsonl", {
                        "case": case, "surface": surface, "request": request,
                        "source_capture_id": raw["capture_id"], "request_capture_id": raw["capture_id"],
                        "arrival_ns": arrival_ns, "receipt": delivered,
                    })
                    actual_trusted = {**trusted, "generation": raw["source_generation"]}
                    decision = evaluate_delivery(request, delivered, raw, actual_trusted, full, region,
                                                 arrival_ns)
                    decision.update({"case": case, "surface": surface, "region_id": region_id,
                                     "capture_id": raw["capture_id"]})
                    dump_line(OUT / "decisions.jsonl", decision)
                    counts[case] = counts.get(case, 0) + 1
        manifest = {"schema": "issue-2692-live-transport-allocation-v1",
                    "allocation": os.environ.get("O3_ALLOCATION", "UNSET_ALLOCATION_ID"),
                    "display": DISPLAY_NAME,
                    "surfaces": surfaces, "expected_rows": SCHEDULE["expected_rows"],
                    "actual_rows": sum(counts.values()), "case_counts": counts,
                    "model_calls": 0, "action_emissions": 0,
                    "input_events": 0, "network": "none",
                    "container_image_id": os.environ.get("OBSTAC_IMAGE_ID"),
                    "container_platform": os.environ.get("OBSTAC_PLATFORM"),
                    "fixture_returncodes": [p.poll() for p in fixtures],
                    "xvfb_returncode": xvfb.poll()}
        (OUT / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        # Independent process checks the live X server and all retained bytes before
        # the fixture processes are terminated. This is not a replay of producer rows.
        oracle = subprocess.run([sys.executable, str(HERE / "independent_oracle.py"), str(OUT)],
                                check=False, capture_output=True, text=True, timeout=60)
        (OUT / "oracle.stdout.txt").write_text(oracle.stdout, encoding="utf-8")
        (OUT / "oracle.stderr.txt").write_text(oracle.stderr, encoding="utf-8")
        if oracle.returncode != 0:
            raise RuntimeError(f"independent live oracle failed: rc={oracle.returncode}")
        print(json.dumps({"rows": manifest["actual_rows"], "case_counts": counts,
                          "model_calls": 0, "action_emissions": 0,
                          "independent_oracle": json.loads((OUT / "AUDIT_RESULT.json").read_text())[
                              "decision"]}, sort_keys=True))
    finally:
        if transport:
            transport.close()
        for proc in fixtures:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
        if xvfb.poll() is None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait()
        (OUT / "cleanup.json").write_text(json.dumps({
            "fixture_returncodes": [p.poll() for p in fixtures],
            "xvfb_returncode": xvfb.poll()}, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
