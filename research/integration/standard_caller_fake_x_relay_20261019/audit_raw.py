"""Independent post-run checks for the retained standard-caller Fake X packet."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODES = ("normal", "optimized")
EXPECTED_FILES = {
    "fake-x-accepted-press.json",
    "held-reply.json",
    "standard-caller-result.json",
    "stdout-stderr.txt",
    "sync-wait.json",
    "synthetic-effect-receipt.json",
    "target-generation-refusal.json",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def main():
    conditions = read_json(ROOT / "conditions.json")
    require(conditions["status"] == "FROZEN_BEFORE_RUN", "conditions were not frozen")
    normalized_results = []
    summaries = {}
    for mode in MODES:
        raw = ROOT / "raw" / mode
        files = {path.name for path in raw.iterdir() if path.is_file()}
        require(files == EXPECTED_FILES, f"{mode}: unexpected raw file set {sorted(files)}")
        press = read_json(raw / "fake-x-accepted-press.json")
        effect = read_json(raw / "synthetic-effect-receipt.json")
        held = read_json(raw / "held-reply.json")
        wait = read_json(raw / "sync-wait.json")
        result = read_json(raw / "standard-caller-result.json")
        generation = read_json(raw / "target-generation-refusal.json")
        test_log = (raw / "stdout-stderr.txt").read_text(encoding="utf-8-sig")

        require("Ran 2 tests" in test_log and "OK" in test_log,
                f"{mode}: unittest log does not show two passing tests")
        require(press == {
            "action_id": "standard-mcp-fake-x-action",
            "classification": "synthetic_fake_x_only",
            "event": "KeyPress",
            "keycode": 2,
            "request_hex": "c80209000202000000000000000000000000000000000000000000000000000000000000",
        }, f"{mode}: accepted synthetic press differs")
        require(effect["source"] == "independent_fake_effect_observer"
                and effect["action_id"] == press["action_id"]
                and effect["event"] == "KeyPress"
                and effect["keycode"] == 2
                and effect["task_success"] is None,
                f"{mode}: independent synthetic receipt mismatch")
        require(held == {
            "held_reply_bytes": 32,
            "independently_observed": True,
            "release_state": "UNKNOWN",
            "replay_enabled": False,
            "task_success": None,
        }, f"{mode}: held-reply record mismatch")
        require(wait == {"request": "GetPointerControl", "sequence": 3},
                f"{mode}: sync wait does not identify the held request")

        cancel = result["cancel"]
        terminal = result["terminal"]
        require(result["observation"]["status"] == "observed"
                and result["observation"]["sequence"] == 1
                and result["observation"]["process_generation"] == "a" * 64,
                f"{mode}: observation was not generation-bound")
        require(result["mint"]["status"] == "minted"
                and result["pending"]["status"] == "pending",
                f"{mode}: guarded input did not reach pending state")
        require(cancel["owner_process_retired"] is True
                and cancel["owner_input_obligations"] == {"buttons": [], "keys": {"a": 2}}
                and cancel["owner_release_attempt"]["status"] == "not_attempted"
                and cancel["release_confirmed"] is False
                and cancel["cleanup_status"] == "UNKNOWN"
                and cancel["task_success"] is None
                and cancel["replay_allowed"] is False
                and cancel["late_server_request_possible"] is True,
                f"{mode}: cancellation did not preserve fail-closed custody")
        require(cancel["owner_client_disconnect"]["status"] == "unknown"
                and cancel["owner_client_disconnect"]["reason"] ==
                "fake_x_only_no_server_disconnect_claim",
                f"{mode}: disconnect receipt scope changed")
        require(terminal == {
            "cleanup_status": "UNKNOWN",
            "release_confirmed": False,
            "replay_allowed": False,
            "status": "runtime_failed",
            "task_success": None,
        }, f"{mode}: terminal result mismatch")
        timing = result["timing"]
        require(0 <= timing["cancel_elapsed_ms"] < 3000,
                f"{mode}: cancel exceeded the frozen 3000ms bound")
        require(0 <= timing["terminal_elapsed_ms"] < 5000,
                f"{mode}: terminal result exceeded the frozen 5000ms bound")

        source_generation = "a" * 64
        current_generation = "b" * 64
        refusal = generation["result"]
        require(generation["source_generation"] == source_generation
                and generation["current_generation"] == current_generation
                and generation["relay_press_seen"] is False
                and generation["task_success"] is None
                and generation["replay_allowed"] is False
                and refusal["status"] == "refused"
                and refusal["input_dispatched"] is False
                and refusal["guard_checks"][0]["reason"] ==
                "process_generation_changed_or_missing",
                f"{mode}: stale process generation was not refused before input")

        normalized = dict(result)
        normalized.pop("timing")
        normalized_results.append(normalized)
        summaries[mode] = {
            "cancel_elapsed_ms": timing["cancel_elapsed_ms"],
            "terminal_elapsed_ms": timing["terminal_elapsed_ms"],
            "held_reply_bytes": held["held_reply_bytes"],
            "release": terminal["cleanup_status"],
            "task_success": terminal["task_success"],
            "replay_allowed": terminal["replay_allowed"],
        }

    require(normalized_results[0] == normalized_results[1],
            "normal and optimized caller semantics differ")

    digest_paths = [ROOT / "conditions.json", ROOT / "audit_raw.py"]
    digest_paths.extend(sorted(path for mode in MODES for path in
                               (ROOT / "raw" / mode).iterdir() if path.is_file()))
    hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in digest_paths
    }
    print(json.dumps({
        "audit": "PASS_RAW_CONSISTENCY_SCOPED",
        "modes": summaries,
        "normal_optimized_semantics_equal": True,
        "scope": "standard MCP caller on process-local Fake X sockets; no physical release or task effect",
        "sha256": hashes,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
