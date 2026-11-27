"""Build an independent task-oracle callback for one frozen MAP01 target.

The callback can be passed to ``create_server(...,
supervised_win32_task_oracle=callback)``. Capture is injected so tests can use
retained frames and live callers can use their exact Win32Backend target.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import io
import json
from pathlib import Path
import re
import time
from typing import Callable

from PIL import Image

from ammo_oracle import classify_ammo_frame


_CALL_ID = re.compile(r"^[0-9a-f]{32}$")


@dataclass(frozen=True)
class CapturedFrame:
    png_bytes: bytes
    generation_before: str
    generation_after: str
    geometry: dict
    started_ns: int
    ended_ns: int


def make_map01_task_oracle(*, trial_dir: Path, template_dir: Path,
                           target_windows: dict[str, int], oracle_id: str,
                           capture: Callable[[str, int, dict], CapturedFrame],
                           clock_ns: Callable[[], int] = time.monotonic_ns):
    """Return a receipt callback compatible with the supervised MCP task oracle."""
    trial_dir = Path(trial_dir)
    template_dir = Path(template_dir)

    def oracle(action: dict) -> dict:
        requested_ns = clock_ns()
        capture_timing = None
        evidence_path = trial_dir / "oracle-input.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        required = ("call_id", "operation_id", "target_generation", "target",
                    "before_png", "before_png_sha256", "release_readback",
                    "screen_region", "frame")
        if any(key not in evidence for key in required):
            raise ValueError("oracle evidence is incomplete")

        call_id = evidence["call_id"]
        operation_id = evidence["operation_id"]
        generation = evidence["target_generation"]
        release = evidence.get("release_readback")
        receipt_base = {"call_id": call_id, "operation_id": operation_id,
                        "target_generation": generation, "oracle_id": oracle_id}

        if not isinstance(call_id, str) or _CALL_ID.fullmatch(call_id) is None:
            outcome, reason = "unknown", "call_id_invalid"
        elif (not isinstance(operation_id, str)
              or _CALL_ID.fullmatch(operation_id) is None
              or not isinstance(generation, str)
              or re.fullmatch(r"[0-9a-f]{64}", generation) is None):
            outcome, reason = "unknown", "action_identity_fields_invalid"
        elif (action.get("status") not in ("completed", "recovered")
              or action.get("call_id") != call_id
              or action.get("operation_id") != operation_id
              or action.get("target_generation") != generation):
            outcome, reason = "unknown", "action_identity_or_terminal_state_mismatch"
        elif action.get("release_confirmed") is not True:
            outcome, reason = "unknown", "action_release_unverified"
        elif (not isinstance(release, dict)
              or release.get("same_generation") is not True
              or release.get("target_generation_before") != generation
              or release.get("target_generation_after") != generation
              or release.get("mouse_left_high_bit_down") is not False):
            outcome, reason = "unknown", "independent_release_readback_unverified"
        elif evidence["target"] not in target_windows:
            outcome, reason = "unknown", "target_not_configured"
        else:
            before_path = Path(evidence["before_png"])
            before_bytes = before_path.read_bytes()
            if sha256(before_bytes).hexdigest() != evidence["before_png_sha256"]:
                outcome, reason = "unknown", "baseline_image_hash_mismatch"
            else:
                screen_region = evidence["screen_region"]
                if (not isinstance(screen_region, list) or len(screen_region) != 4
                        or any(type(value) is not int for value in screen_region)
                        or evidence["frame"] not in ("screen_physical_px", "window_client")):
                    outcome, reason = "unknown", "frame_or_screen_region_invalid"
                else:
                    x, y, width, height = screen_region
                    frame = capture(evidence["target"],
                                    int(target_windows[evidence["target"]]), evidence)
                    capture_received_ns = clock_ns()
                    capture_timing = {"started_ns": frame.started_ns,
                                      "ended_ns": frame.ended_ns,
                                      "received_ns": capture_received_ns}
                    expected = ({"x": 0, "y": 0, "width": width, "height": height}
                                if evidence["frame"] == "window_client" else
                                {"x": x, "y": y, "width": width, "height": height})
                    if (any(type(value) is not int for value in (
                            requested_ns, frame.started_ns, frame.ended_ns,
                            capture_received_ns))
                            or not requested_ns <= frame.started_ns <= frame.ended_ns <= capture_received_ns):
                        outcome, reason = "unknown", "capture_outside_verification_window"
                    elif (frame.generation_before != generation
                            or frame.generation_after != generation
                            or frame.geometry != expected
                            or width != 1520 or height != 825):
                        outcome, reason = "unknown", "generation_or_geometry_changed_during_capture"
                    else:
                        try:
                            with Image.open(before_path) as image:
                                before = image.convert("RGB")
                            with Image.open(io.BytesIO(frame.png_bytes)) as image:
                                after = image.convert("RGB")
                            if before.size != (width, height) or after.size != (width, height):
                                outcome, reason = "unknown", "image_geometry_mismatch"
                            else:
                                before_result = classify_ammo_frame(before, template_dir)
                                after_result = classify_ammo_frame(after, template_dir)
                                transition = {"before": before_result, "after": after_result,
                                              "expected": ["50", "49"]}
                                if (before_result.get("status") != "classified"
                                        or after_result.get("status") != "classified"):
                                    outcome, reason = "unknown", "ammo_digit_classification_unknown"
                                elif before_result.get("value") != "50":
                                    outcome, reason = "unknown", "ammo_baseline_not_50"
                                elif after_result.get("value") == "49":
                                    outcome, reason = "success", "ammo_50_to_49"
                                elif after_result.get("value") == "50":
                                    outcome, reason = "failure", "ammo_remained_50"
                                else:
                                    outcome, reason = "failure", "unexpected_ammo_value"
                                (trial_dir / "ammo-transition.json").write_text(
                                    json.dumps(transition, indent=2, sort_keys=True) + "\n",
                                    encoding="utf-8")
                                Image.frombytes("RGB", (width, height), after.tobytes()).save(
                                    trial_dir / "oracle-after.png", format="PNG")
                        except (OSError, ValueError):
                            outcome, reason = "unknown", "ammo_image_decode_or_classification_error"

        observed_ns = clock_ns()
        if capture_timing is not None and (
                type(observed_ns) is not int
                or type(capture_timing["received_ns"]) is not int
                or observed_ns < capture_timing["received_ns"]):
            outcome, reason = "unknown", "capture_outside_verification_window"
        receipt = {**receipt_base, "outcome": outcome,
                   "observed_monotonic_ns": observed_ns,
                   "evidence_ref": str(evidence_path.resolve())}
        (trial_dir / "oracle-receipt.json").write_text(
            json.dumps({"requested_monotonic_ns": requested_ns,
                        "observed_monotonic_ns": observed_ns,
                        "capture_timing": capture_timing,
                        "receipt": receipt, "reason": reason,
                        "task_effect_scope": "pistol-ammo HUD transition 50 to 49"},
                       indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt

    return oracle
