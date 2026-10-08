"""Diagnostic structural derivative: timing/exposure are measured outcomes.
Original scientific eligibility is separately reported with unchanged reference.py.
No relaxed timing/exposure/gap gate qualifies the original science study.
"""
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
        need(clear <= cs, "source clear not before declared deadline")
        need(integer(e["color"]) == (0xFF0000 if identity % 2 else 0x00FF00), "source color")
        if spec["kind"] == "pulse":
            pass  # Exposure is a measured diagnostic outcome, not science admission.
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
        need(due <= start, "capture not before declared deadline")
        need(start <= returned <= extracted, "capture chronology")
        # Extraction/window overrun is a recorded timing outcome in this diagnostic.
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
    edges = [epoch] + starts + [max(epoch + 960_000_000, frames[-1]["extracted_ns"])]
    gaps = [b - a for a, b in zip(edges, edges[1:])]
    need(min(gaps) >= 0, "observation window chronology")
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
