"""Independent raw-only verifier for #4448 retained evidence."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import shutil
import statistics
import tempfile
from pathlib import Path


FORMAL_PAIRS = 12
ACTIONS = 4
ARMS = ("EPHEMERAL_XTERM", "RESIDENT_XTERM")


def percentile(values: list[int], p: float) -> int:
    return sorted(values)[max(0, math.ceil(p * len(values)) - 1)]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(raw: dict, evidence_root: Path, expected_pairs: int, expected_schedule_id: str) -> list[str]:
    errors: list[str] = []
    if raw.get("schedule_id") != expected_schedule_id:
        errors.append("schedule_id_mismatch")
    if raw.get("pairs_planned") != expected_pairs:
        errors.append("planned_pair_count")
    pairs = raw.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != expected_pairs:
        errors.append("retained_pair_count")
        return errors
    if raw.get("actions_per_arm") != ACTIONS:
        errors.append("action_count_contract")
    if raw.get("errors"):
        errors.append("runner_errors_present")
    schedule = raw.get("schedule")
    if not isinstance(schedule, list) or len(schedule) != expected_pairs:
        errors.append("schedule_count")
        schedule = []
    schedule_by_id = {x.get("pair"): x for x in schedule if isinstance(x, dict)}
    all_arm_rows: dict[str, list[dict]] = {arm: [] for arm in ARMS}
    pair_medians: list[tuple[int, int]] = []

    for pair_index, pair in enumerate(pairs):
        prefix = f"pair{pair_index}"
        if pair.get("pair") != pair_index:
            errors.append(f"{prefix}_identity")
        expected_order = ["EPHEMERAL_XTERM", "RESIDENT_XTERM"]
        if pair_index % 2:
            expected_order.reverse()
        schedule_item = schedule_by_id.get(pair_index)
        if schedule_item is None or schedule_item.get("order") != expected_order:
            errors.append(f"{prefix}_schedule")
        if pair.get("order") != expected_order:
            errors.append(f"{prefix}_retained_order")
        if not isinstance(pair.get("xvfb_pid"), int) or not isinstance(pair.get("wm_pid"), int):
            errors.append(f"{prefix}_display_process_ids")
        if pair.get("xvfb_exit") != 0 or pair.get("wm_exit") != 0:
            errors.append(f"{prefix}_display_cleanup")
        arms = pair.get("arms", [])
        by_arm = {a.get("arm"): a for a in arms if isinstance(a, dict)}
        if set(by_arm) != set(ARMS):
            errors.append(f"{prefix}_arm_set")
            continue
        medians: dict[str, int] = {}
        for arm_name in ARMS:
            arm = by_arm[arm_name]
            ap = f"{prefix}_{arm_name.lower()}"
            rows = arm.get("rows")
            if not isinstance(rows, list) or len(rows) != ACTIONS:
                errors.append(f"{ap}_row_count")
                continue
            if arm.get("terminal_exit") != 0:
                errors.append(f"{ap}_terminal_cleanup")
            if arm.get("ended_ns", 0) - arm.get("started_ns", 0) != arm.get("session_ns"):
                errors.append(f"{ap}_session_duration")
            latencies = []
            for action, row in enumerate(rows):
                rp = f"{ap}_action{action}"
                all_arm_rows[arm_name].append(row)
                if row.get("pair") != pair_index or row.get("arm") != arm_name or row.get("action") != action:
                    errors.append(f"{rp}_identity")
                if row.get("input_keys") != ["r", "Return"]:
                    errors.append(f"{rp}_input_events")
                if not isinstance(row.get("terminal_pid"), int) or not isinstance(row.get("child_pid"), int):
                    errors.append(f"{rp}_process_ids")
                if row.get("ready_record", {}).get("pid") != row.get("child_pid") or row.get("ready_record", {}).get("stdin_tty") is not True:
                    errors.append(f"{rp}_child_ready_receipt")
                if row.get("key_up") is not True or row.get("keymap_hex") != "00" * 32:
                    errors.append(f"{rp}_neutral_keymap")
                if set(row.get("keycodes", {})) != {"r", "Return"}:
                    errors.append(f"{rp}_keycode_receipt")
                try:
                    observed_bytes = bytes.fromhex(row["effect_bytes_hex"])
                except (KeyError, ValueError, TypeError):
                    errors.append(f"{rp}_effect_hex")
                    observed_bytes = b""
                effect_index = action if arm_name == "RESIDENT_XTERM" else 0
                expected_bytes = b'{"value":"r"}\n' * (effect_index + 1)
                if observed_bytes != expected_bytes:
                    errors.append(f"{rp}_effect_exact_bytes")
                if hashlib.sha256(observed_bytes).hexdigest() != row.get("effect_sha256"):
                    errors.append(f"{rp}_effect_hash")
                try:
                    effect_records = [json.loads(line) for line in observed_bytes.decode("utf-8").splitlines()]
                    expected_records = [{"value": "r"} for _ in range(effect_index + 1)]
                    if effect_records != expected_records:
                        errors.append(f"{rp}_effect_content")
                except (UnicodeDecodeError, json.JSONDecodeError):
                    errors.append(f"{rp}_effect_json")
                effect_rel = (Path("scratch") / f"pair-{pair_index:02d}" / arm_name /
                              ("effects.jsonl" if arm_name == "RESIDENT_XTERM" else f"effects-{action}.jsonl"))
                effect_path = evidence_root / effect_rel
                if not effect_path.is_file():
                    errors.append(f"{rp}_effect_file_missing")
                else:
                    retained = effect_path.read_bytes()
                    if not retained.startswith(observed_bytes):
                        errors.append(f"{rp}_effect_file_prefix")
                    if arm_name == "EPHEMERAL_XTERM" or action == ACTIONS - 1:
                        if retained != observed_bytes:
                            errors.append(f"{rp}_effect_file_exact")
                if row.get("effect_observed_ns", 0) > row.get("key_up_ns", -1):
                    errors.append(f"{rp}_observation_order")
                if row.get("key_up_ns", 0) > row.get("next_ready_ns", -1):
                    errors.append(f"{rp}_readiness_order")
                if row.get("next_ready_ns", 0) - row.get("effect_observed_ns", 0) != row.get("latency_ns"):
                    errors.append(f"{rp}_latency_derivation")
                latency = row.get("latency_ns")
                if not isinstance(latency, int) or latency < 0:
                    errors.append(f"{rp}_latency_value")
                else:
                    latencies.append(latency)
                if arm_name == "EPHEMERAL_XTERM":
                    done = row.get("done_record") or {}
                    if done.get("pid") != row.get("child_pid") or done.get("actions") != 1 or done.get("exit") != "normal":
                        errors.append(f"{rp}_child_exit_receipt")
                    if row.get("terminal_exit_after_action") != 0 or row.get("terminal_exit_ns") != row.get("next_ready_ns"):
                        errors.append(f"{rp}_terminal_exit_receipt")
                else:
                    if action < ACTIONS - 1:
                        if row.get("terminal_exit_after_action") is not None or row.get("terminal_exit_ns") is not None or row.get("done_record") is not None:
                            errors.append(f"{rp}_premature_resident_exit")
                    else:
                        done = row.get("done_record") or {}
                        if done.get("pid") != row.get("child_pid") or done.get("actions") != ACTIONS or done.get("exit") != "normal":
                            errors.append(f"{rp}_resident_child_exit_receipt")
                        if row.get("terminal_exit_after_action") != 0 or row.get("terminal_exit_ns", 0) < row.get("next_ready_ns", 0):
                            errors.append(f"{rp}_resident_terminal_exit_receipt")
            if latencies:
                medians[arm_name] = int(statistics.median(latencies))
            pids = [row.get("terminal_pid") for row in rows]
            child_pids = [row.get("child_pid") for row in rows]
            if arm_name == "EPHEMERAL_XTERM":
                if len(set(pids)) != ACTIONS or len(set(child_pids)) != ACTIONS:
                    errors.append(f"{ap}_ephemeral_process_reuse")
            else:
                if len(set(pids)) != 1 or len(set(child_pids)) != 1:
                    errors.append(f"{ap}_resident_process_restart")
        if set(medians) == set(ARMS):
            pair_medians.append((medians["EPHEMERAL_XTERM"], medians["RESIDENT_XTERM"]))

    derived = {}
    for arm in ARMS:
        values = [row["latency_ns"] for row in all_arm_rows[arm] if isinstance(row.get("latency_ns"), int)]
        if values:
            derived[arm] = {"n": len(values), "p50_ns": percentile(values, .5), "p95_ns": percentile(values, .95)}
    if pair_medians:
        ratios = [resident / ephemeral if ephemeral else math.inf for ephemeral, resident in pair_medians]
        derived["paired_median_latency_ratio"] = statistics.median(ratios)
    ep_sessions, rs_sessions = [], []
    for pair in pairs:
        by_arm = {a.get("arm"): a for a in pair.get("arms", []) if isinstance(a, dict)}
        if set(by_arm) == set(ARMS):
            ep_sessions.append(by_arm["EPHEMERAL_XTERM"].get("session_ns"))
            rs_sessions.append(by_arm["RESIDENT_XTERM"].get("session_ns"))
    if all(isinstance(x, int) for x in ep_sessions + rs_sessions):
        derived["session_resident_wins"] = sum(r < e for e, r in zip(ep_sessions, rs_sessions))
        derived["session_pairs"] = len(ep_sessions)
    raw["_audit_derived"] = derived
    return errors


def corruptions(raw: dict, evidence_root: Path, expected_pairs: int, expected_schedule_id: str) -> dict:
    def mutate(mutator):
        candidate = copy.deepcopy(raw)
        mutator(candidate)
        return candidate

    mutations = {
        "planned_pair_count": lambda: mutate(lambda x: x.__setitem__("pairs_planned", 99)),
        "pair_order": lambda: mutate(lambda x: x["pairs"][0].__setitem__("order", list(reversed(x["pairs"][0]["order"]))),),
        "arm_name": lambda: mutate(lambda x: x["pairs"][0]["arms"][0].__setitem__("arm", "MUTATED")),
        "row_removed": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"].pop()),
        "effect_bytes": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"][0].__setitem__("effect_bytes_hex", "00" + x["pairs"][0]["arms"][0]["rows"][0]["effect_bytes_hex"][2:])),
        "effect_hash": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"][0].__setitem__("effect_sha256", "0" * 64)),
        "keymap": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"][0].__setitem__("keymap_hex", "01" + "00" * 31)),
        "latency_receipt": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"][0].__setitem__("next_ready_ns", x["pairs"][0]["arms"][0]["rows"][0]["next_ready_ns"] + 1)),
        "terminal_exit": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"][0].__setitem__("terminal_exit_after_action", 9)),
        "child_pid": lambda: mutate(lambda x: x["pairs"][0]["arms"][0]["rows"][0].__setitem__("child_pid", x["pairs"][0]["arms"][0]["rows"][0]["child_pid"] + 100000)),
        "resident_pid_restart": lambda: mutate(lambda x: next(a for a in x["pairs"][0]["arms"] if a["arm"] == "RESIDENT_XTERM")["rows"][2].__setitem__("terminal_pid", next(a for a in x["pairs"][0]["arms"] if a["arm"] == "RESIDENT_XTERM")["rows"][2]["terminal_pid"] + 100000)),
        "schedule_id": lambda: mutate(lambda x: x.__setitem__("schedule_id", "mutated-schedule")),
    }
    accepted = []
    rejected = []
    for name, factory in mutations.items():
        candidate = factory()
        with tempfile.TemporaryDirectory(prefix="ai4448-corrupt-") as tmp:
            copied = Path(tmp) / "evidence-copy"
            shutil.copytree(evidence_root, copied)
            (copied / "raw.json").write_text(json.dumps(candidate, sort_keys=True), encoding="utf-8")
            copied_raw = read_json(copied / "raw.json")
            result = validate(copied_raw, copied, expected_pairs, expected_schedule_id)
        (rejected if result else accepted).append(name)
    return {"attempted": len(mutations), "rejected": rejected, "accepted": accepted,
            "effective": len(rejected), "errors": [] if not accepted else ["mutation_accepted"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--pairs", type=int, required=True)
    parser.add_argument("--schedule-id", required=True)
    parser.add_argument("--mode", choices=("construction", "formal"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw_path = args.evidence / "raw.json"
    raw = read_json(raw_path)
    errors = validate(raw, args.evidence, args.pairs, args.schedule_id)
    if raw.get("label") != ("formal" if args.mode == "formal" else "construction-excluded"):
        errors.append("allocation_label")
    if args.mode == "formal":
        if args.pairs != FORMAL_PAIRS or raw.get("formal_invocations") != 1 or raw.get("with_window_manager") is not True:
            errors.append("formal_invocation_contract")
        if raw.get("reruns") != 0 or raw.get("replacements") != 0 or raw.get("tuning") != 0:
            errors.append("formal_rerun_contract")
    elif raw.get("formal_invocations") != 0:
        errors.append("construction_invocation_contract")
    mutation_result = corruptions(raw, args.evidence, args.pairs, args.schedule_id)
    derived = raw.pop("_audit_derived", {})
    if mutation_result["effective"] < 10 or mutation_result["accepted"]:
        errors.append("corruption_controls")
    if args.mode == "construction":
        decision = "CONSTRUCTION_AUDIT_ACCEPT" if not errors else "CONSTRUCTION_AUDIT_REJECT"
    elif errors:
        decision = "FAIL_INTEGRITY" if any("effect" in e or "keymap" in e or "process" in e or "terminal" in e or "child" in e for e in errors) else "HOLD_MISSING_EVIDENCE"
    else:
        ep = derived.get("EPHEMERAL_XTERM", {})
        resident = derived.get("RESIDENT_XTERM", {})
        ratio = derived.get("paired_median_latency_ratio", math.inf)
        wins = derived.get("session_resident_wins", 0)
        count = derived.get("session_pairs", 0)
        gate = (resident.get("p95_ns", math.inf) < 30_000_000 and
                ep.get("p50_ns", 0) > 100_000_000 and ratio <= .35 and
                wins >= math.ceil(.833333333333 * count))
        decision = "PASS_RESIDENT_XTERM_TEARDOWN_SCOPED" if gate else "HOLD_NO_CRITICAL_PATH_BENEFIT"
    result = {"audit_errors": errors, "derived": derived, "corruption_controls": mutation_result,
              "raw_bytes": raw_path.stat().st_size,
              "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
              "decision": decision}
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(1 if errors or decision in ("AUDIT_REJECT", "CONSTRUCTION_AUDIT_REJECT") else 0)


if __name__ == "__main__":
    main()
