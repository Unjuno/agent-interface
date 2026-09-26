"""Fresh bounded live transport allocation for malformed receipt clock controls."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
V1 = HERE.parent / "o3_live_receipt_transport_2692_v1"
sys.path.insert(0, str(V1.parent / "o3_relevant_region_successor_v1"))
sys.path.insert(0, str(V1))
from transport import LiveTransport
sys.path.insert(0, str(HERE))
from adapter import evaluate_delivery

OUT = Path(os.environ.get("O3_OUT", "/out"))
DISPLAY_NAME = os.environ.get("DISPLAY", ":101")
SCHEDULE = json.loads((HERE / "case_schedule.json").read_text())


def write_line(path, row):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def corrupt(case, receipt, arrival):
    value = copy.deepcopy(receipt)
    if case == "capture_end_string":
        value["capture_end_ns"] = "not-an-integer"
    elif case == "capture_end_list":
        value["capture_end_ns"] = ["not", "an", "integer"]
    elif case == "capture_end_missing":
        value.pop("capture_end_ns")
    elif case == "capture_start_string":
        value["capture_start_ns"] = "not-an-integer"
    elif case == "arrival_string":
        arrival = "not-an-integer"
    elif case == "end_before_start":
        value["capture_end_ns"] = value["capture_start_ns"] - 1
    elif case == "end_future":
        value["capture_end_ns"] = arrival + 1
    return value, arrival


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
            fixtures.append(subprocess.Popen([
                sys.executable, str(V1 / "gtk_fixture.py"), "--surface", surface,
                "--meta", str(OUT / "meta" / f"{surface}.json")],
                stdout=(OUT / f"{surface}.log").open("wb"), stderr=subprocess.STDOUT))
        deadline = time.monotonic() + 10
        while not all((OUT / "meta" / f"{s}.json").exists() for s in SCHEDULE["surfaces"]):
            if time.monotonic() > deadline:
                raise TimeoutError("GTK fixture metadata timeout")
            if xvfb.poll() is not None or any(p.poll() is not None for p in fixtures):
                raise RuntimeError("Xvfb/GTK exited before allocation")
            time.sleep(0.05)
        surfaces = {s: json.loads((OUT / "meta" / f"{s}.json").read_text())
                    for s in SCHEDULE["surfaces"]}
        transport = LiveTransport(DISPLAY_NAME, OUT / "raw_events.jsonl", OUT / "frames", "frames")
        counts = {}
        adapter_calls = 0
        epoch = 0
        for surface in SCHEDULE["surfaces"]:
            trusted = surfaces[surface]
            for region_id, rect in SCHEDULE["regions"].items():
                for case in SCHEDULE["cases"]:
                    epoch += 1
                    request = {"observation_id": str(uuid.uuid4()), "intent_epoch": epoch,
                               "region_id": region_id, "region_rect": rect,
                               "max_receipt_age_ns": SCHEDULE["max_receipt_age_ns"],
                               "surface": surface, "case": case,
                               "trusted_xid": trusted["xid"]}
                    raw = transport.capture(request, trusted)
                    full = (OUT / raw["receipt"]["full_frame_path"]).read_bytes()
                    region = (OUT / raw["receipt"]["region_frame_path"]).read_bytes()
                    arrival = time.monotonic_ns()
                    receipt, delivered_arrival = corrupt(case, raw["receipt"], arrival)
                    delivery = {"surface": surface, "case": case, "request": request,
                                "source_capture_id": raw["capture_id"],
                                "receipt": receipt, "arrival_ns": delivered_arrival}
                    write_line(OUT / "deliveries.jsonl", delivery)
                    trusted_live = {**trusted, "generation": raw["source_generation"]}
                    decision = evaluate_delivery(request, receipt, raw, trusted_live, full,
                                                 region, delivered_arrival)
                    adapter_calls += 1
                    decision.update({"surface": surface, "case": case,
                                     "region_id": region_id, "capture_id": raw["capture_id"]})
                    write_line(OUT / "decisions.jsonl", decision)
                    counts[case] = counts.get(case, 0) + 1
        manifest = {"schema": "issue-2692-live-clock-typeguard-v2",
                    "allocation": "o3-live-receipt-typeguard-2692-v2-20260921-03",
                    "display": DISPLAY_NAME, "surfaces": surfaces,
                    "expected_rows": SCHEDULE["expected_rows"],
                    "actual_rows": sum(counts.values()), "case_counts": counts,
                    "adapter_module": evaluate_delivery.__module__,
                    "adapter_calls": adapter_calls,
                    "model_calls": 0, "input_events": 0, "action_emissions": 0,
                    "network": "none", "container_image_id": os.environ.get("OBSTAC_IMAGE_ID"),
                    "container_platform": os.environ.get("OBSTAC_PLATFORM")}
        (OUT / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        audit = subprocess.run([sys.executable, str(HERE / "independent_oracle.py"), str(OUT)],
                               check=False, capture_output=True, text=True, timeout=60)
        (OUT / "oracle.stdout.txt").write_text(audit.stdout, encoding="utf-8")
        (OUT / "oracle.stderr.txt").write_text(audit.stderr, encoding="utf-8")
        if audit.returncode != 0:
            raise RuntimeError(f"independent live oracle failed with {audit.returncode}")
        print((OUT / "AUDIT_RESULT.json").read_text().strip())
    finally:
        if transport:
            transport.close()
        for proc in fixtures:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait()
        if xvfb.poll() is None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                xvfb.kill(); xvfb.wait()
        (OUT / "cleanup.json").write_text(json.dumps({
            "fixture_returncodes": [p.poll() for p in fixtures],
            "xvfb_returncode": xvfb.poll()}, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
