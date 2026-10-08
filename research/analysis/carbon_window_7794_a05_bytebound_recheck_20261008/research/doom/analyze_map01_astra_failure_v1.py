"""Reconstruct the retained Astra failure and calibrate one-way visual invalidation."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "live_control"))
from policy_invalidation_guard_v1 import PolicyInvalidationGuard

ROOT = HERE / "results/map01-astra-attempt-v1"
HEALTH = [100, 100, 100, 100, 100, 84, 84, 53, 49, 22, 11, 4, 0]
AMMO = [50, 50, 50, 50, 48, 37, 37, 37, 37, 37, 37, 37, 37]
ARMOR = [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
HEALTH_BOX = [440, 585, 535, 635]
FACE_BOX = [610, 580, 675, 650]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def guard_spec(box, identifier):
    return {
        "op": "policy_invalidation_guard", "guard_id": identifier,
        "source_sequence": 1, "box": box, "metric": "rgb_change",
        "rgb_threshold": 32, "minimum_changed_pixels": 100,
        "max_source_age_ms": 30000, "on_change": "needs_decision",
        "on_unknown": "needs_decision",
    }


def make_hud_sheet(frames, target):
    rows = []
    for index, path in enumerate(frames):
        with Image.open(path) as opened:
            image = opened.convert("RGB")
        crop = image.crop((320, 580, 820, 665)).resize(
            (1000, 170), resample=Image.Resampling.NEAREST)
        canvas = Image.new("RGB", (1060, 200), "black")
        canvas.paste(crop, (60, 30))
        ImageDraw.Draw(canvas).text((10, 10), str(index), fill="white")
        rows.append(canvas)
    sheet = Image.new("RGB", (1060, 200 * len(rows)), "black")
    for index, row in enumerate(rows):
        sheet.paste(row, (0, index * 200))
    sheet.save(target, compress_level=9)


def main():
    report = read(ROOT / "report.json")
    events = [json.loads(line) for line in (ROOT / "events.jsonl").read_text().splitlines()]
    manifest = read(ROOT / "frame-manifest.json")
    frames = [ROOT / row["file"] for row in manifest]
    assert len(frames) == len(report["decisions"]) == len(HEALTH)
    assert all(sha(path) == row["sha256"] for path, row in zip(frames, manifest))
    assert report["score"]["player_dead"] and not report["score"]["map_exit"]
    assert report["score"]["kill_count"] == 1
    accepted = {row["id"]: row for row in events if row.get("event") == "accepted"}
    terminal = {row["id"]: row for row in events if row.get("event") == "terminal"}
    submitted = {row["command"].get("id"): row["command"] for row in events
                 if row.get("event") == "command" and row.get("command", {}).get("op") == "submit"}

    intervals = []
    guard_results = []
    face_invalidations = 0
    for index in range(len(frames) - 1):
        with Image.open(frames[index]) as opened:
            before = opened.convert("RGB")
        with Image.open(frames[index + 1]) as opened:
            after = opened.convert("RGB")
        health_guard = PolicyInvalidationGuard(
            guard_spec(HEALTH_BOX, f"health-{index}"), before, 1,
            "retained-map01-window", 1_000_000_000)
        outcome = health_guard.evaluate(
            after, 2, "retained-map01-window", 2_000_000_000)
        expected = HEALTH[index + 1] != HEALTH[index]
        assert (outcome["status"] == "INVALIDATED") == expected
        guard_results.append(outcome)
        face_guard = PolicyInvalidationGuard(
            guard_spec(FACE_BOX, f"face-{index}"), before, 1,
            "retained-map01-window", 1_000_000_000)
        if face_guard.evaluate(after, 2, "retained-map01-window", 2_000_000_000)["status"] == "INVALIDATED":
            face_invalidations += 1

        decision = report["decisions"][index]
        cover_id = f"cover-{index}"
        steps = submitted[cover_id]["steps"]
        cover_mode = "active_evasion_or_fire" if any(step["op"] == "hold" for step in steps) else "coast"
        uncovered_ms = max(0, decision["controller_model_ended_ns"] -
                           terminal[cover_id]["terminal_ns"]) / 1e6
        intervals.append({
            "from_iteration": index, "to_iteration": index + 1,
            "source_frame_sha256": sha(frames[index]),
            "next_frame_sha256": sha(frames[index + 1]),
            "health": [HEALTH[index], HEALTH[index + 1]],
            "health_delta": HEALTH[index + 1] - HEALTH[index],
            "ammo": [AMMO[index], AMMO[index + 1]],
            "armor": [ARMOR[index], ARMOR[index + 1]],
            "assessment": decision["action"]["assessment"],
            "commands": decision["action"]["commands"],
            "cover_id": cover_id, "cover_mode": cover_mode,
            "cover_terminal_status": terminal[cover_id]["status"],
            "model_ms": (decision["controller_model_ended_ns"] -
                         decision["controller_model_started_ns"]) / 1e6,
            "uncovered_model_tail_ms": uncovered_ms,
            "health_guard": outcome,
            "attribution_limit": "decision-to-decision window includes inference cover and the following primary program",
        })

    tails = [row["uncovered_model_tail_ms"] for row in intervals]
    coast_damage = -sum(min(0, row["health_delta"]) for row in intervals
                        if row["cover_mode"] == "coast")
    changed = sum(HEALTH[i] != HEALTH[i + 1] for i in range(len(HEALTH) - 1))
    unchanged = len(HEALTH) - 1 - changed
    hud_sheet = ROOT / "hud-numbers-contact-sheet-v1.png"
    make_hud_sheet(frames, hud_sheet)
    output = {
        "schema": "agent-interface-map01-failure-analysis-v1",
        "passed": True,
        "retained_run": "map01-astra-attempt-v1",
        "source_sha256": {
            str((ROOT / "report.json").relative_to(REPO)).replace("\\", "/"): sha(ROOT / "report.json"),
            str((ROOT / "events.jsonl").relative_to(REPO)).replace("\\", "/"): sha(ROOT / "events.jsonl"),
            str((HERE.parent / "live_control/policy_invalidation_guard_v1.py").relative_to(REPO)).replace("\\", "/"): sha(HERE.parent / "live_control/policy_invalidation_guard_v1.py"),
        },
        "visual_transcription": {
            "scope": "manual HUD transcription from the exact hash-checked decision frames; values are reviewable in the generated contact sheet",
            "health": HEALTH, "ammo": AMMO, "armor": ARMOR,
            "health_box": HEALTH_BOX,
            "contact_sheet": str(hud_sheet.relative_to(REPO)).replace("\\", "/"),
            "contact_sheet_sha256": sha(hud_sheet),
        },
        "cover_gap": {
            "total_uncovered_model_tail_ms": sum(tails),
            "maximum_uncovered_model_tail_ms": max(tails),
            "intervals_with_uncovered_tail": sum(value > 0 for value in tails),
        },
        "damage_windows": {
            "health_lost_total": HEALTH[0] - HEALTH[-1],
            "health_lost_in_windows_with_coast_inference_cover": coast_damage,
            "scope": "window-level association only; each window also contains the following primary program",
        },
        "one_way_visual_invalidation": {
            "health_roi_true_invalidations": changed,
            "health_roi_true_unchanged": unchanged,
            "health_roi_false_invalidations": 0,
            "health_roi_missed_changes": 0,
            "face_animation_control_invalidations": face_invalidations,
            "decision": "RETAIN_AS_ONE_WAY_INVALIDATION_CANDIDATE",
            "why_revisit": "single-ROI change was unsafe as evidence that a task postcondition succeeded; here it can only remove an already admitted policy and request a decision",
        },
        "intervals": intervals,
        "conclusion": "cover expiry is real but insufficient as the sole diagnosis: 84 health points were lost across decision windows whose inference cover was coast; a narrowly scoped visual change guard perfectly separated changed and unchanged health decision frames in this retained trace",
        "limits": "posthoc single-run calibration on decision frames; manual HUD values; no continuous-sample false-negative rate, semantic direction, causal survival benefit, live integration, or MAP01-clear claim",
        "next_test": "preregister one bounded v23/schema-v3 threat exposure with exact HUD-region observations; region change may only cancel/switch to a separately admitted conservative policy or escalate",
    }
    (ROOT / "failure-analysis-v1.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({
        "passed": output["passed"], "cover_gap": output["cover_gap"],
        "damage_windows": output["damage_windows"],
        "one_way_visual_invalidation": output["one_way_visual_invalidation"],
    }, indent=2))


if __name__ == "__main__":
    main()
