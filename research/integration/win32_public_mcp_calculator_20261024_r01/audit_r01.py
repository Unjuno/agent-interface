"""Independent read-only audit of the retained R01 public MCP observation."""
import hashlib
import json
from pathlib import Path

from PIL import Image

PACKET = Path(__file__).resolve().parent
RUN = PACKET / "run"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    observed = read(RUN / "observe-0.json")
    result = read(RUN / "result.json")
    closed = read(RUN / "close-0.json")
    image_path = RUN / "observe-0-1.png"
    image_bytes = image_path.read_bytes()
    image = Image.open(image_path).convert("RGB")
    pixels = list(image.getdata())
    colors = sorted(set(pixels))
    report = observed["parsed"]["receipt"]["source"]["raw_report"]
    observation = report["observation"]
    action_files = sorted(p.name for p in RUN.glob("dispatch-*.json"))
    validation_files = sorted(p.name for p in RUN.glob("validation-*.json"))
    checks = [
        ("MCP observation returned without tool error", observed["isError"] is False),
        ("reported native HWND matches frozen target", observation["native_window_id"] == 55117672),
        ("reported generation is internally matched", report["target_generation_consistency"] == "matched"),
        ("runtime reported input_dispatched=false", report["input_dispatched"] is False),
        ("screenshot size matches frozen region", image.size == (320, 533)),
        ("screenshot is a uniform black image", len(colors) == 1 and colors[0] == (0, 0, 0)),
        ("validation was not called", not validation_files),
        ("dispatch was not called", not action_files),
        ("close shows zero input calls", closed["parsed"]["session"]["call_count"] == 0),
        ("close has no unresolved calls", closed["parsed"]["session"]["unresolved_call_ids"] == []),
        ("close release=false is consistent with no input attempt", closed["parsed"]["release_confirmed"] is False),
        ("prelaunch checker error occurred before runtime start", read(PACKET / "PRELAUNCH_CHECK_FAILURE.json")["runtime_started"] is False),
    ]
    audit = {
        "schema": "win32-public-mcp-calculator-r01-audit-v1",
        "attempt_id": "win32-public-mcp-calculator-20261024-r01-5909d88e5d7a4d69b030c39033cb4f73",
        "classification": "integrated_entry_path_observation_failure",
        "disposition": "HOLD_BEFORE_INPUT",
        "passed": sum(ok for _, ok in checks),
        "total": len(checks),
        "checks": [{"name": name, "passed": ok} for name, ok in checks],
        "screenshot": {
            "path": image_path.name,
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "size": list(image.size),
            "pixels": len(pixels),
            "unique_rgb_colors": len(colors),
            "nonblack_pixels": sum(pixel != (0, 0, 0) for pixel in pixels),
            "only_rgb_color": list(colors[0]) if len(colors) == 1 else None,
            "raw_capture_sha256": observation["sha256"],
            "raw_capture_bytes": observation["bytes"],
        },
        "action_boundary": {
            "observation_calls": 1,
            "validation_calls": len(validation_files),
            "dispatch_calls": len(action_files),
            "input_sent": False,
            "task_success": None,
            "release_confirmed": None,
            "close_release_confirmed": closed["parsed"]["release_confirmed"],
            "close_release_interpretation": "No action input was issued; interface_close did not release this call.",
        },
        "evidence": {
            "observation_id": report["observation_id"],
            "call_id": observed["parsed"]["call_id"],
            "target_generation": report["target_generation"],
            "native_window_id": observation["native_window_id"],
            "capture_frame": observation["frame"],
            "source_commit": "e3b6293b4be42c54739936160e524b92ba706178",
        },
        "limitations": [
            "One app, one observation, and no input dispatch; no task effect or release result.",
            "Uniform black output does not prove why the capture was black.",
            "The exact source routes window_client capture through GDI PrintWindow(PW_CLIENTONLY); API branch outcomes were not separately instrumented.",
            "Not a model-efficiency or reliability measurement, MAP01 result, or WSLc result.",
        ],
    }
    audit["passed"] = sum(row["passed"] for row in audit["checks"])
    audit["status"] = "PASS_AUDIT" if audit["passed"] == audit["total"] else "AUDIT_MISMATCH"
    (PACKET / "audit_r01.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(json.dumps({"status": audit["status"], "passed": audit["passed"],
                      "total": audit["total"], "unique_colors": len(colors),
                      "input_sent": False}, indent=2))


if __name__ == "__main__":
    main()
