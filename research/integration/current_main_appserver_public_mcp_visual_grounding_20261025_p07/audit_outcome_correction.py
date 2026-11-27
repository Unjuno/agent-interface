from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"
SERVER = RUN / "server"
SESSION = SERVER / "guarded-session-077aece154e54fcebc255629071e2576"
COMPILED = "compiled-7cfd950e944243e09da4bd74e149cf30"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    original = load(RUN / "RESULT.json")
    provider = load(RUN / "provider-call" / "result.json")
    selected = load(RUN / "model-selected-point.json")
    mint_request = load(RUN / "model-derived-mint-request.json")
    mint_receipt = load(SESSION / "mint-grounded_green.json")
    click = load(SERVER / "synthetic-target-click.json")
    effect = load(SERVER / "synthetic-effect-receipt.json")
    terminal = load(SESSION / f"{COMPILED}-11-terminal.json")
    compiled_receipt = load(SESSION / f"{COMPILED}-19-receipt.json")
    close = load(SERVER / "session-077aece154e54fcebc255629071e2576-close.json")
    final_raw = (SERVER / "synthetic-application-state.rgb").read_bytes()
    pixel = list(Image.frombytes("RGB", (32, 32), final_raw, "raw", "BGRX").getpixel((1, 1)))
    checks = {
        "original_run_record_retained": original["classification"] == "FAIL_OR_HOLD_FIRST_OUTCOME_RETAINED",
        "provider_completed_with_point": provider["turn_status"] == "completed" and provider["raw"]["point"] == [16, 8],
        "provider_usage_matches_correction": provider["usage"]["input_tokens"] == 10185 and provider["usage"]["output_tokens"] == 58 and provider["usage"]["reasoning_output_tokens"] == 39,
        "model_saw_exact_observation": selected["image_sha256"] == original["observation_image_sha256"],
        "mint_bound_to_observation": mint_request["source_sequence"] == original["observation_sequence"] == mint_receipt["created_sequence"] == 1,
        "exactly_one_owner_click_at_selected_point": click["event"]["point"] == selected["point"] == [16, 8] and click["event"]["button"] == 1,
        "effect_receipt_matches_click": effect["click_point"] == click["event"]["point"] and effect["button_press_count"] == 1 and effect["rgb"] == [255, 0, 0],
        "persisted_effect_pixel_matches": pixel == [255, 0, 0],
        "compiled_terminal_verified_release": terminal["status"] == "completed" and terminal["release"]["verified"] is True and not terminal["release"]["buttons_down"] and not terminal["release"]["keys_down"],
        "compiled_effect_receipt_succeeded": compiled_receipt["outcome"] == "TASK_SUCCEEDED" and compiled_receipt["transitions"][0]["release_verified"] is True,
        "session_close_confirmed_release": close["verified"] is True and close["release_confirmed"] is True,
        "runtime_score_remains_null": original["runtime_task_success"] is None,
    }
    rows = []
    for line in (RUN / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        actual = hashlib.sha256((RUN / relative).read_bytes()).hexdigest()
        rows.append(actual == digest)
    checks["all_raw_hashes_match"] = bool(rows) and all(rows)
    checks["redaction_hashes_match"] = all(
        entry["redacted_sha256"] == hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
        for entry in load(ROOT / "REDACTIONS.json")["redactions"]
    )
    packet_manifest = ROOT / "PACKET_SHA256.json"
    if packet_manifest.is_file():
        manifest = load(packet_manifest)["files"]
        checks["packet_hashes_match"] = all(
            hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
            for relative, digest in manifest.items()
        )
    report = {
        "schema": "agent-interface/appserver-visual-grounding-p07-additive-audit-v1",
        "classification": "PASS_SCOPED" if all(checks.values()) else "FAIL_OR_HOLD",
        "checks": checks,
        "original_result_preserved": True,
        "independent_task_success": all(checks.values()),
        "scope": "real model selection through public MCP on synthetic Fake X only",
        "wslc_used": False,
        "physical_input": False,
    }
    (ROOT / "OUTCOME_CORRECTION_AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["classification"] != "PASS_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
