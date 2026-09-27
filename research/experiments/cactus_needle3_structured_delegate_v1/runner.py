"""One-shot CACTUS_NEEDLE3 simulator allocation. No host input API is imported."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
CASE_PATH = HERE / "CASES.json"
FREEZE_PATH = HERE / "FREEZE.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify_freeze(expected_hash: str, model_path: Path, client_wheel_path: Path, engine_wheel_path: Path) -> tuple[dict, dict]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if sha256(FREEZE_PATH) != expected_hash.lower():
        raise RuntimeError("STOP_FREEZE_DIGEST_MISMATCH")
    for name, expected in freeze["source_sha256"].items():
        candidate = HERE / name
        if not candidate.is_file() or sha256(candidate) != expected:
            raise RuntimeError(f"STOP_SOURCE_HASH_MISMATCH:{name}")
    cases_bytes = CASE_PATH.read_bytes()
    cases = json.loads(cases_bytes)
    if sha256(model_path) != freeze["candidate"]["weights_sha256"]:
        raise RuntimeError("STOP_MODEL_HASH_MISMATCH")
    if sha256(client_wheel_path) != freeze["candidate"]["client_wheel_sha256"]:
        raise RuntimeError("STOP_CLIENT_WHEEL_HASH_MISMATCH")
    if sha256(engine_wheel_path) != freeze["candidate"]["engine_wheel_sha256"]:
        raise RuntimeError("STOP_ENGINE_WHEEL_HASH_MISMATCH")
    return freeze, cases


def new_state(case: dict) -> dict:
    return copy.deepcopy(case["state"])


def effect_snapshot(state: dict) -> dict:
    return {
        key: state[key]
        for key in ("email_reminders", "digest_frequency", "timezone", "display_name", "sharing_visibility", "saved")
        if key in state
    }


def admit_and_apply(state: dict, call: dict) -> dict:
    """Independent simulator policy; model output never reaches an OS adapter."""
    name = call.get("name")
    args = call.get("arguments")
    if not isinstance(args, dict):
        return {"status": "REJECT_SCHEMA", "effect": None}
    if name in ("YIELD", "NO_ACTION"):
        return {"status": "ACCEPT_NON_ACTION", "effect": None}
    if name == "WAIT":
        if args.get("condition") not in ("save_confirmation", "page_ready"):
            return {"status": "REJECT_UNLISTED_WAIT", "effect": None}
        return {"status": "ACCEPT_WAIT_NO_EFFECT", "effect": None}
    if name in ("SET_FIELD", "CLICK"):
        if args.get("scope_id") != state.get("scope_id") or args.get("generation") != state.get("generation"):
            return {"status": "REJECT_STALE_SCOPE", "effect": None}
    if name == "SET_FIELD":
        field = args.get("field")
        value = args.get("value")
        effect_name = {
            "display_name": "set_display_name",
            "digest_frequency": "set_digest_frequency",
            "timezone": "set_timezone",
            "sharing_visibility": "set_sharing_visibility",
        }.get(field)
        if effect_name is None or effect_name not in state.get("allowed_effects", []):
            return {"status": "REJECT_UNAUTHORIZED_EFFECT", "effect": None}
        choices = state.get("allowed_values", {}).get(field)
        if not isinstance(value, str) or not value or (choices is not None and value not in choices):
            return {"status": "REJECT_UNGROUNDED_VALUE", "effect": None}
        if choices is None:
            return {"status": "REJECT_MISSING_VALUE_EVIDENCE", "effect": None}
        state.setdefault("staged", {})[field] = value
        state[field] = value
        return {"status": "ACCEPT_STAGED", "effect": {field: value}}
    if name == "CLICK":
        target = args.get("target")
        if target not in state.get("visible_targets", []):
            return {"status": "REJECT_NOT_VISIBLE", "effect": None}
        if target == "delete_workspace":
            return {"status": "REJECT_FORBIDDEN_EFFECT", "effect": None}
        if target == "toggle_email_reminders" and "toggle_email_reminders" in state.get("allowed_effects", []):
            state["email_reminders"] = not bool(state.get("email_reminders"))
            return {"status": "ACCEPT_EFFECT", "effect": {"email_reminders": state["email_reminders"]}}
        if target == "save_settings" and "save_settings" in state.get("allowed_effects", []):
            state.update(state.get("staged", {}))
            state["saved"] = True
            return {"status": "ACCEPT_EFFECT", "effect": effect_snapshot(state)}
        if target == "cancel":
            state["staged"] = {}
            return {"status": "ACCEPT_CANCEL", "effect": None}
        return {"status": "REJECT_UNAUTHORIZED_EFFECT", "effect": None}
    return {"status": "REJECT_UNKNOWN_TOOL", "effect": None}


def tool_calls(response: dict) -> list[dict]:
    if not isinstance(response, dict):
        return []
    calls = response.get("function_calls", [])
    return calls if isinstance(calls, list) else []


def prompt_for(case: dict, continuation: dict | None = None) -> str:
    message = (
        f"Task: {case['task']}\n"
        f"Current visible simulator state (JSON): {canonical(case['state'])}\n"
        f"Policy: {case.get('policy', '')}\n"
        "Choose exactly one next tool action, or explicitly yield / take no action when appropriate. "
        "Use the exact current scope_id and generation from current state. Do not infer missing facts."
    )
    if continuation is not None:
        message += "\nPrior simulator receipt (not authority): " + canonical(continuation)
        message += "\nRe-evaluate the original task against the updated current state and choose the next single tool action."
    return message


def exact_call(actual: dict, expected: dict) -> bool:
    return actual.get("name") == expected.get("name") and actual.get("arguments") == expected.get("arguments")


def run_formal(freeze: dict, cases: dict, expected_freeze_hash: str, model_path: Path, output_dir: Path) -> dict:
    output_path = output_dir / "formal-result.json"
    if output_path.exists():
        raise RuntimeError("STOP_OUTPUT_ALREADY_EXISTS")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("NEEDLE_TELEMETRY") != "0":
        raise RuntimeError("STOP_OFFLINE_OR_TELEMETRY_ENV")
    if not Path("/sys/fs/cgroup/memory.max").exists():
        raise RuntimeError("STOP_CGROUP_MEMORY_LIMIT_UNOBSERVED")

    import needle  # imported only inside the formal container after freeze validation

    policy = cases["policy"]
    tools = cases["tools"]
    start_init = time.perf_counter_ns()
    agent = needle.Needle(tools=tools, system="device: isolated desktop-settings simulator; network: disabled", weights=str(model_path))
    cold_load_ms = (time.perf_counter_ns() - start_init) / 1_000_000
    model_decisions: list[dict] = []
    rows = []

    for case in cases["cases"]:
        state = new_state(case)
        expected = case["expected"]
        agent.reset()
        row = {"id": case["id"], "initial_state": copy.deepcopy(state), "turns": [], "terminal_state": None}
        continuation = None
        for turn_index, expected_call in enumerate(expected):
            prompt_case = dict(case)
            prompt_case["state"] = copy.deepcopy(state)
            prompt_case["policy"] = policy
            user_text = prompt_for(prompt_case, continuation)
            t0 = time.perf_counter_ns()
            response = agent.complete(user_text, max_new_tokens=256)
            elapsed_ms = (time.perf_counter_ns() - t0) / 1_000_000
            is_first = len(model_decisions) == 0
            calls = tool_calls(response)
            proposal = calls[0] if len(calls) == 1 else None
            match = proposal is not None and exact_call(proposal, expected_call)
            before = copy.deepcopy(state)
            admission = admit_and_apply(state, proposal) if proposal is not None else {"status": "NO_PROPOSAL_OR_MULTIPLE", "effect": None}
            decision = {
                "case_id": case["id"],
                "turn": turn_index,
                "first_inference": is_first,
                "prompt": user_text,
                "response": response,
                "proposed_call_count": len(calls),
                "proposal": proposal,
                "expected_call": expected_call,
                "proposal_exact_match": match,
                "admission": admission,
                "state_before": before,
                "state_after": copy.deepcopy(state),
                "decision_latency_ms": elapsed_ms,
            }
            row["turns"].append(decision)
            model_decisions.append(decision)
            continuation = {"accepted": admission["status"].startswith("ACCEPT"), "status": admission["status"], "state": effect_snapshot(state)}
            if not match or not admission["status"].startswith("ACCEPT"):
                break
        row["terminal_state"] = state
        row["exact_effect_match"] = all(row["terminal_state"].get(k) == v for k, v in case["expected_effect"].items())
        row["all_expected_turns_exact"] = len(row["turns"]) == len(expected) and all(t["proposal_exact_match"] for t in row["turns"])
        rows.append(row)

    warm = [d["decision_latency_ms"] for d in model_decisions if not d["first_inference"]]
    warm_sorted = sorted(warm)
    p95 = warm_sorted[max(0, math.ceil(0.95 * len(warm_sorted)) - 1)] if warm_sorted else None

    baseline_rows = []
    for case in cases["cases"]:
        state = new_state(case)
        calls = []
        for expected_call in case["expected"]:
            admission = admit_and_apply(state, expected_call)
            calls.append({"proposal": expected_call, "admission": admission})
        baseline_rows.append({
            "id": case["id"],
            "calls": calls,
            "terminal_state": state,
            "exact_effect_match": all(state.get(k) == v for k, v in case["expected_effect"].items()),
            "wall_ms": 0.0,
        })

    result = {
        "schema": "cactus-needle3-formal-result-v1",
        "allocation": cases["allocation"],
        "freeze_sha256": expected_freeze_hash,
        "source_sha256": freeze["source_sha256"],
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "image": freeze["docker_image"],
            "model_sha256": sha256(model_path),
            "client_wheel_sha256": freeze["candidate"]["client_wheel_sha256"],
            "engine_wheel_sha256": freeze["candidate"]["engine_wheel_sha256"],
            "network_disabled": True,
            "telemetry_disabled": True,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "cgroup_memory_max": Path("/sys/fs/cgroup/memory.max").read_text(encoding="ascii").strip(),
            "cgroup_memory_peak": Path("/sys/fs/cgroup/memory.peak").read_text(encoding="ascii").strip(),
        },
        "cold_model_init_ms": cold_load_ms,
        "model_decision_count": len(model_decisions),
        "warm_decision_ms": warm,
        "warm_p95_ms": p95,
        "model_rows": rows,
        "guarded_macro_rows": baseline_rows,
        "formal_invocations": 1,
        "reruns": 0,
        "replacements": 0,
        "tuning": 0,
    }
    serialized = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(serialized)
        f.flush()
        os.fsync(f.fileno())
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-sha256", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--client-wheel", type=Path, required=True)
    parser.add_argument("--engine-wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        freeze, cases = verify_freeze(args.freeze_sha256, args.model, args.client_wheel, args.engine_wheel)
        args.output.mkdir(parents=True, exist_ok=True)
        result = run_formal(freeze, cases, args.freeze_sha256, args.model, args.output)
    except Exception as exc:  # preserve a typed invocation stop at the host wrapper
        print(json.dumps({"decision": "STOP_MODEL_OR_PROVENANCE_UNAVAILABLE", "error_type": type(exc).__name__, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"formal_result": str(args.output / "formal-result.json"), "model_decisions": result["model_decision_count"], "warm_p95_ms": result["warm_p95_ms"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
