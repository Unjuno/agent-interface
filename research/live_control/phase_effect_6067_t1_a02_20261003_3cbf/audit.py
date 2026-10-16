"""Independent raw-only oracle. Imports no policy, producer, fixture or bridge."""
import argparse
import base64
import copy
import hashlib
import json
import struct
from pathlib import Path


def need(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value):
    need(type(value) is int, "exact integer required")
    return value


def unique(pairs):
    obj = {}
    for key, value in pairs:
        need(key not in obj, "duplicate JSON field")
        obj[key] = value
    return obj


def read(path):
    return parse_record(Path(path).read_text())

def check_fixture_plan(fixture):
    headers = {"issue": 6067, "period_ms": 120, "slot_ms": 10, "source_bias_ms": 2,
               "capture_bias_ms": 5, "window_ms": 960, "cues_per_pulse_cell": 8,
               "samples_per_cell": 8, "max_gap_ms": 190, "max_lateness_ms": 10,
               "exposure_tolerance_ms": 5}
    for k, v in headers.items():
        need(type(fixture.get(k)) is int and fixture[k] == v, "independent fixed header: " + k)
    arms = [("fixed", [0, 0, 0, 0]), ("irregular", [1, 7, 3, 9]), ("rotated", [0, 3, 6, 9])]
    expected = []
    def add(kind, arm, phase=None, width=None):
        name, offsets = arm
        c = {"id": f"c{len(expected):03}", "kind": kind, "schedule": name, "offsets": offsets}
        if kind == "pulse":
            c.update(phase=phase, width_ms=width)
        expected.append(c)
    for arm in arms:
        add("dark", arm)
    for wi, width in enumerate((10, 20, 30)):
        for phase in range(12):
            shift = (phase + wi) % 3
            for arm in arms[shift:] + arms[:shift]:
                add("pulse", arm, phase, width)
    for arm in reversed(arms):
        add("persistent", arm)
    join(fixture["cases"], expected, "independently complete ordered 114-cell plan")

def join(actual, expected, message):
    need(json.dumps(actual, sort_keys=True, allow_nan=False) ==
         json.dumps(expected, sort_keys=True, allow_nan=False), message)

def parse_record(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def audit_cell(spec, source, capture, lifecycle):
    epoch = integer(source["epoch_ns"])
    need(integer(capture["epoch_ns"]) == epoch, "clock/epoch identity")
    need(integer(source["window"]) == integer(capture["window"]), "window identity")
    need(integer(source["pid"]) == integer(lifecycle["fixture_pid"]), "fixture pid")
    need(integer(capture["pid"]) == integer(lifecycle["observer_pid"]), "observer pid")
    pids = [integer(lifecycle[k]) for k in ("fixture_pid", "observer_pid", "xvfb_pid")]
    need(len(set(pids)) == 3 and min(pids) > 0, "unique child pids")
    for key in ("fixture_exit", "observer_exit", "xvfb_exit"):
        need(integer(lifecycle[key]) == 0, "child terminal exit")
    for obj, key in ((source, "final_keymap"), (capture, "initial_keymap"), (capture, "final_keymap")):
        need(obj[key] == "00" * 32, "neutral private X keymap")
    need(len(source["final_pixels"]) == 1024 and
         all(type(p) is int and p == 0 for p in source["final_pixels"]), "final clear")
    offsets = spec["offsets"]
    need(len(offsets) == 4 and all(type(x) is int and 0 <= x < 12 for x in offsets), "offset domain")
    expected = {}
    if spec["kind"] == "pulse":
        phase, width = integer(spec["phase"]), integer(spec["width_ms"])
        need(phase in range(12) and width in (10, 20, 30), "cue family")
        for i in range(8):
            due = epoch + (120 * i + 10 * phase + 2) * 1_000_000
            expected[i + 1] = (due, due + width * 1_000_000)
    elif spec["kind"] == "persistent":
        expected[1] = (epoch - 20_000_000, epoch + 1_000_000_000)
    else:
        need(spec["kind"] == "dark", "known source kind")
    events = source["events"]
    need(len(events) == len(expected), "complete source denominator")
    need([integer(e["id"]) for e in events] == list(expected), "canonical source event order")
    by_id = {}
    exposures = []
    previous_clear_end = None
    for e in events:
        identity = integer(e["id"])
        need(identity in expected and identity not in by_id, "source ID membership/duplicate")
        onset, clear = expected[identity]
        need(integer(e["onset_ns"]) == onset and integer(e["due_clear_ns"]) == clear, "source schedule")
        times = [integer(e[k]) for k in ("draw_start_ns", "draw_end_ns", "clear_start_ns", "clear_end_ns")]
        ds, de, cs, ce = times
        need(onset <= ds <= de <= cs <= ce, "source XSync chronology")
        if previous_clear_end is not None:
            need(previous_clear_end <= ds, "serial source XSync intervals")
        previous_clear_end = ce
        need(clear <= cs <= clear + 10_000_000 and ds <= onset + 10_000_000, "source lateness")
        need(integer(e["color"]) == (0xFF0000 if identity % 2 else 0x00FF00), "source color")
        if spec["kind"] == "pulse":
            need(abs((cs - de) - spec["width_ms"] * 1_000_000) <= 5_000_000, "rendered exposure")
        else:
            need(de < epoch and cs > epoch + 960_000_000, "persistent control exposure")
        exposures.append(cs - de)
        by_id[identity] = e
    frames = capture["frames"]
    need(len(frames) == 8, "equal eight-capture budget")
    starts, native_costs, materialization_costs, hits = [], [], [], []
    unknown = 0
    for i, frame in enumerate(frames):
        need(integer(frame["index"]) == i, "capture ID/order")
        due = epoch + (120 * i + 10 * offsets[i % 4] + 5) * 1_000_000
        need(integer(frame["due_ns"]) == due, "capture intended schedule")
        start, returned, extracted = [integer(frame[k]) for k in ("start_ns", "native_return_ns", "extracted_ns")]
        need(due <= start <= due + 10_000_000, "capture lateness")
        need(start <= returned <= extracted, "capture chronology")
        need(extracted <= epoch + 960_000_000, "capture extraction within observation window")
        if starts:
            need(starts[-1] < start and frames[i - 1]["extracted_ns"] < start, "serial captures")
        raw = base64.b64decode(frame["pixels_b64"], validate=True)
        need(len(raw) == 4096 and hashlib.sha256(raw).hexdigest() == frame["pixel_sha256"], "recoverable exact pixels")
        values = struct.unpack("<1024I", raw)
        identity, color = values[:2]
        expected_decode = None
        if 1 <= identity <= 8 and color in (0xFF0000, 0x00FF00) and len(set(values[1:])) == 1:
            expected_decode = {"id": identity, "color": color}
            need(identity in by_id, "false cue identity")
            e = by_id[identity]
            need(e["color"] == color and start <= e["clear_end_ns"] and
                 returned >= e["draw_start_ns"], "pixel/source overlap")
            hits.append(identity)
        elif any(values):
            unknown += 1
        need(json.dumps(frame["decoded"], sort_keys=True) == json.dumps(expected_decode, sort_keys=True), "decoded pixels/type")
        starts.append(start)
        native_costs.append(returned - start)
        materialization_costs.append(extracted - returned)
    edges = [epoch] + starts + [epoch + 960_000_000]
    gaps = [b - a for a, b in zip(edges, edges[1:])]
    need(min(gaps) >= 0 and max(gaps) <= 190_000_000, "observed maximum gap")
    seen = sorted(set(hits))
    missing = [identity for identity in expected if identity not in seen]
    streak = current = 0
    for identity in expected:
        current = current + 1 if identity in missing else 0
        streak = max(streak, current)
    if spec["kind"] == "persistent":
        need(hits == [1] * 8 and unknown == 0, "persistent detection control")
    if spec["kind"] == "dark":
        need(not hits and unknown == 0, "dark false-positive control")
    return {"seen_ids": seen, "misses": len(missing), "missing_ids": missing,
            "max_miss_streak": streak, "max_gap_ns": max(gaps), "unknown_frames": unknown,
            "native_cost_ns": native_costs, "materialization_ns": materialization_costs,
            "exposures_ns": exposures, "false_positives": 0}


def validate(root, fixture, source_pins):
    check_fixture_plan(fixture)
    summary = read(root / "raw.json")
    join(summary["source_sha256"], source_pins, "frozen producer source receipt")
    need(summary["allocation"] == fixture["allocation"], "allocation identity")
    need(summary["status"] == "COMPLETE" and summary["mode"] == "formal", "complete formal block")
    need(summary["cells"] == [c["id"] for c in fixture["cases"]], "complete planned case order")
    need(summary["cgroups"] == {"cpu.max": "100000 100000", "memory.max": "536870912",
         "memory.swap.max": "0", "pids.max": "64"}, "actual cgroup limits")
    results = []
    for spec in fixture["cases"]:
        cell = root / "cells" / spec["id"]
        saved = read(cell / "cell.json")
        join(saved["spec"], spec, "case specification")
        need(set(saved["files_sha256"]) == {"source.json", "capture.json", "source.jsonl", "frames.jsonl"}, "complete raw byte pins")
        for filename, digest in saved["files_sha256"].items():
            need(filename in ("source.json", "capture.json", "source.jsonl", "frames.jsonl"), "raw path allowlist")
            need(hashlib.sha256((cell / filename).read_bytes()).hexdigest() == digest, "raw byte identity")
        source, capture = read(cell / "source.json"), read(cell / "capture.json")
        frame_stream = [parse_record(s) for s in (cell / "frames.jsonl").read_text().splitlines()]
        join(frame_stream, capture["frames"], "complete typed frame stream join")
        traces = [parse_record(s) for s in (cell / "source.jsonl").read_text().splitlines()]
        need(len(traces) == 2 * len(source["events"]), "complete source event stream")
        for i, e in enumerate(source["events"]):
            join(traces[2*i], {"event": "draw", "id": e["id"], "start": e["draw_start_ns"], "end": e["draw_end_ns"]}, "typed draw stream join")
            join(traces[2*i+1], {"event": "clear", "id": e["id"], "start": e["clear_start_ns"], "end": e["clear_end_ns"]}, "typed clear stream join")
        result = audit_cell(spec, source, capture, saved["lifecycle"])
        results.append({"id": spec["id"], "schedule": spec["schedule"], "kind": spec["kind"],
                        "phase": spec.get("phase"), "width_ms": spec.get("width_ms"), **result})
    counts = {name: sum(r["kind"] == "pulse" and r["misses"] == 8 for r in results if r["schedule"] == name)
              for name in ("fixed", "irregular", "rotated")}
    fixed_blind_per_width = all(any(r["schedule"] == "fixed" and r["width_ms"] == w and r["misses"] == 8
                                   for r in results) for w in (10, 20, 30))
    benefit = fixed_blind_per_width and counts["irregular"] < counts["fixed"] and counts["rotated"] < counts["fixed"]
    return {"status": "PASS_TRANSFER_SCOPED" if benefit else "HOLD_BENEFIT_NOT_ESTABLISHED",
            "cells_checked": len(results), "captures_checked": 8 * len(results),
            "all_miss_pulse_episodes": counts, "false_positives": 0,
            "max_gap_ns": max(r["max_gap_ns"] for r in results), "results": results,
            "scope": "private colour/ID X11 acquisition only; no input, model, task effect or safety"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    here = Path(__file__).resolve().parent
    freeze = read(here / "FREEZE.json")
    need(hashlib.sha256(a.fixture.read_bytes()).hexdigest() == freeze["candidate_sha256"]["fixture.json"], "immutable fixture bytes")
    need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == freeze["auditor_sha256"], "frozen auditor bytes")
    for name, digest in freeze["candidate_sha256"].items():
        need(hashlib.sha256((here / name).read_bytes()).hexdigest() == digest, "staged producer source bytes")
    result = validate(a.raw, read(a.fixture), freeze["candidate_sha256"])
    first = read(a.raw / "cells" / "c000" / "cell.json")
    spec = first["spec"]
    source = read(a.raw / "cells" / "c000" / "source.json")
    capture = read(a.raw / "cells" / "c000" / "capture.json")
    trials = []
    mutations = ("time_bool", "missing_frame", "pixel_hash", "decode_id", "child_exit", "source_time", "epoch", "keymap")
    for name in mutations:
        so, ca, li = copy.deepcopy(source), copy.deepcopy(capture), copy.deepcopy(first["lifecycle"])
        if name == "time_bool": ca["frames"][0]["start_ns"] = True
        if name == "missing_frame": ca["frames"].pop()
        if name == "pixel_hash": ca["frames"][0]["pixel_sha256"] = "0" * 64
        if name == "decode_id": ca["frames"][0]["decoded"] = {"id": 8, "color": 0xFF0000}
        if name == "child_exit": li["observer_exit"] = 1
        if name == "source_time": so["epoch_ns"] = -1
        if name == "epoch": ca["epoch_ns"] += 1
        if name == "keymap": ca["final_keymap"] = "01" * 32
        try:
            audit_cell(spec, so, ca, li)
        except (ValueError, KeyError, TypeError) as e:
            trials.append({"case": name, "rejected": True, "reason": str(e),
                           "source": so, "capture": ca, "lifecycle": li})
        else:
            raise ValueError("ineffective corruption: " + name)
    a.out.mkdir(exist_ok=False)
    (a.out / "audit.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    (a.out / "mutations.json").write_text(json.dumps(trials, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, sort_keys=True))


if __name__ == "__main__":
    main()
