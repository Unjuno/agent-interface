"""Audit the merged #7384 Chromium task-1 witness without making a new run.

This is a custody/consistency audit of one retained task. It deliberately
rejects interpreting the caller's task-1 success as six-task success or as an
efficiency comparison.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath

try:
    from research.live_control.append_checkpoint_v1 import inspect as inspect_journal
except ImportError:  # direct execution from the repository's research/live_control directory
    from append_checkpoint_v1 import inspect as inspect_journal


EXPECTED_FILES_SHA256 = "51cb390975c05f0972be9f0845dc63a180ddbee1705d802ccea674f7040ce70c"
EXPECTED_PUBLICATION_BASE = "446b2635c1ad3b7ed6c97b790c0a35b6fb58d7c3"
EXPECTED_EXPERIMENT_MAIN = "d908d8f9712139f1e88a605437442a97587cbe9c"
EXPECTED_TOKEN = "t991061-1"
EXPECTED_MISSING = ["task-2", "task-3", "task-4", "task-5", "task-6"]
HERE = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE = HERE / "research/integration/chromium_client_57_4d74_20261004"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _safe_member(root: Path, relative: str) -> Path:
    item = PurePosixPath(relative)
    _require(not item.is_absolute() and ".." not in item.parts,
             "unsafe evidence member reference")
    path = root.joinpath(*item.parts).resolve()
    _require(path.is_relative_to(root.resolve()), "evidence member escapes package")
    _require(path.is_file(), "missing evidence member: " + relative)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _exact_single_task_oracle(result: dict) -> dict:
    oracle = result.get("independent_evaluation")
    expected_counts = {f"task-{index}": int(index == 1) for index in range(1, 7)}
    _require(type(oracle) is dict and oracle.get("schema") == "integrated_efficiency_oracle_v1",
             "six-task oracle schema required")
    exact_counts = oracle.get("exact_counts")
    _require(oracle.get("success") is False
             and type(oracle.get("record_count")) is int
             and oracle.get("record_count") == 1
             and type(exact_counts) is dict
             and set(exact_counts) == set(expected_counts)
             and all(type(exact_counts[key]) is int
                     and exact_counts[key] == expected_counts[key] for key in expected_counts)
             and oracle.get("missing") == EXPECTED_MISSING
             and oracle.get("unexpected") == [] and oracle.get("duplicates") == {},
             "six-task oracle must show exactly task-1 and incomplete tasks 2-6")
    return oracle


def validate_result(result: dict, submissions: list[dict]) -> dict:
    """Check the retained task-1 caller/compiled/effect records against POST history."""
    _require(type(result) is dict and result.get("status") == "OBSERVED",
             "observed caller-composed result required")
    goal = result.get("goal")
    _require(type(goal) is dict and goal.get("task_id") == "task-1"
             and goal.get("token") == EXPECTED_TOKEN and goal.get("layout") == "A"
             and goal.get("phase") == "cold",
             "frozen task-1 goal required")
    _require(type(submissions) is list and len(submissions) == 1,
             "one append-only task-1 submission history record required")
    submission = submissions[0]
    _require(type(submission) is dict
             and submission.get("schema") == "integrated_efficiency_submission_v1"
             and submission.get("task_id") == "task-1"
             and submission.get("layout") == "A"
             and submission.get("expected_token") == EXPECTED_TOKEN
             and submission.get("submitted_values") == [EXPECTED_TOKEN]
             and submission.get("exact") is True
             and type(submission.get("received_ns")) is int,
             "submission history does not independently confirm the exact task-1 token")

    oracle = _exact_single_task_oracle(result)
    _require(type(oracle.get("known_ns")) is int
             and submission.get("received_ns") <= oracle["known_ns"],
             "submission must precede the retained independent evaluation")

    caller = result.get("caller")
    _require(type(caller) is dict and caller.get("outcome") == "TASK_SUCCEEDED"
             and caller.get("task_effect") == "succeeded"
             and caller.get("delivery") == "confirmed"
             and caller.get("execution_progress") == {"status": "completed"},
             "task-1 caller completion receipt required")
    _require(caller.get("route") == "reuse"
             and caller.get("comparison", {}).get("class") == "warm_reuse"
             and caller.get("comparison", {}).get("comparable_to_full_cold") is False
             and caller.get("comparison", {}).get("omitted_stages") == [
                 "observe_source", "coarse_model", "acquire_anchor", "anchor_model"],
             "caller route must retain its omitted cold-acquisition boundary")
    _require(caller.get("attempt_ledger") == [] and caller.get("model_call_ledger") == [],
             "attempt ledgers must remain exactly as observed")

    graph = result.get("graph")
    receipt = graph.get("receipt") if type(graph) is dict else None
    _require(type(receipt) is dict and receipt.get("outcome") == "TASK_SUCCEEDED"
             and receipt.get("completed_transitions") == 2
             and receipt.get("frontier_model_resumptions") == 0,
             "two-transition compiled completion required")
    transitions = receipt.get("transitions")
    _require(type(transitions) is list and len(transitions) == 2
             and [row.get("action") for row in transitions] == ["enter", "submit"],
             "compiled enter/submit transition pair required")
    action_ids = [row.get("action_id") for row in transitions]
    _require(all(type(value) is str and value for value in action_ids)
             and len(set(action_ids)) == 2,
             "compiled transitions require distinct action IDs")
    for transition in transitions:
        action_id = transition["action_id"]
        _require(transition.get("release_verified") is True
                 and transition.get("effect_ref") == "terminal:" + action_id,
                 "transition release/effect reference mismatch")
    observations = receipt.get("observations")
    _require(type(observations) is list and [row.get("sequence") for row in observations]
             == sorted(row.get("sequence") for row in observations),
             "ordered compiled observations required")
    by_ref = {row.get("evidence_ref"): row for row in observations}
    for transition in transitions:
        observation = by_ref.get(transition.get("evidence_ref"))
        _require(type(observation) is dict
                 and observation.get("sequence") == transition.get("observation_sequence"),
                 "transition evidence reference/sequence mismatch")
    _require(transitions[0].get("matched_conditions") == {"target_valid": True}
             and transitions[1].get("matched_conditions") == {
                 "exact_token_visible": True, "target_valid": True},
             "compiled action guards differ from current observations")
    programs = result.get("programs")
    _require(type(programs) is list, "durable action program records required")
    for transition in transitions:
        program = next((row for row in programs
                        if row.get("label") == "compiled-" + transition["action"]), None)
        terminal = program.get("terminal") if type(program) is dict else None
        release = terminal.get("release") if type(terminal) is dict else None
        _require(type(terminal) is dict and terminal.get("status") == "completed"
                 and terminal.get("id") == transition["action_id"]
                 and type(release) is dict and release.get("verified") is True
                 and release.get("keys_down") == [] and release.get("buttons_down") == [],
                 "transition does not reconcile with a released durable terminal")
    critical = receipt.get("critical_events", [])
    for transition in transitions:
        action = transition["action"]
        _require(any(row.get("event") == "action_terminal" and row.get("action") == action
                     and row.get("action_id") == transition["action_id"]
                     and row.get("release_verified") is True for row in critical),
                 "transition terminal/release event missing")
        effect_rows = [row for row in critical
                       if row.get("event") == "effect_checked"
                       and row.get("action") == action]
        _require(len(effect_rows) == 1 and effect_rows[0].get("status") == "succeeded"
                 and effect_rows[0].get("evidence_ref") in by_ref,
                 "transition effect check missing")
        effect_observation = by_ref[effect_rows[0]["evidence_ref"]]
        expected_effect = ("exact_token_visible" if action == "enter"
                           else "exact_saved_title")
        _require(effect_observation.get("sequence", 0)
                 > transition.get("observation_sequence", 0)
                 and effect_observation.get("predicates", {}).get(expected_effect) is True,
                 "transition effect lacks later exact observed evidence")
    _require(receipt.get("raw_evidence_retention") == "adapter_responsibility_unverified",
             "raw-evidence retention limitation must remain explicit")

    raw_observations = graph.get("raw_observations")
    _require(type(raw_observations) is list and len(raw_observations) == len(observations),
             "raw and compiled observation counts must reconcile")
    raw_by_sequence = {row.get("normalized", {}).get("sequence"): row
                       for row in raw_observations}
    for observed in observations:
        raw = raw_by_sequence.get(observed.get("sequence"))
        normalized = raw.get("normalized") if type(raw) is dict else None
        _require(type(normalized) is dict
                 and all(normalized.get(key) == value for key, value in observed.items())
                 and normalized.get("surface") == "integrated-form",
                 "raw observation does not match compiled observation")
    exact_ocr = [row for row in raw_observations
                 if row.get("ocr", {}).get("stdout", "").strip() == EXPECTED_TOKEN]
    _require(len(exact_ocr) == 1 and exact_ocr[0].get("ocr", {}).get("exit") == 0
             and exact_ocr[0].get("normalized", {}).get("predicates", {}).get(
                 "exact_token_visible") is True,
             "one successful exact-token OCR observation required")

    return {
        "status": "PASS_SCOPED_TASK1_EVIDENCE_INCOMPLETE_SIX_TASK",
        "task_id": "task-1",
        "exact_task_count": oracle["record_count"],
        "missing_tasks": list(oracle["missing"]),
        "full_six_success": oracle["success"],
        "compiled_transitions": len(transitions),
        "distinct_released_actions": len(set(action_ids)),
        "caller_route": caller["route"],
        "caller_model_ledger_entries": len(caller["model_call_ledger"]),
        "setup_elapsed_ns": result.get("setup", {}).get("elapsed_ns"),
        "grounding_cost": "unavailable",
        "raw_evidence_retention": receipt["raw_evidence_retention"],
        "efficiency_claim": False,
    }


def audit_package(root: Path = DEFAULT_PACKAGE) -> dict:
    root = Path(root).resolve()
    manifest_path = _safe_member(root, "FILES.json")
    manifest_bytes = manifest_path.read_bytes()
    _require(hashlib.sha256(manifest_bytes).hexdigest() == EXPECTED_FILES_SHA256,
             "frozen package manifest hash mismatch")
    manifest = json.loads(manifest_bytes)
    _require(type(manifest) is dict and len(manifest) == 360,
             "frozen 360-member manifest required")
    for relative, expected in manifest.items():
        _require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected) is not None,
                 "invalid member hash")
        member = _safe_member(root, relative)
        _require(_sha256(member) == expected, "member hash mismatch: " + relative)

    source_pin = _read_json(_safe_member(root, "SOURCE_CURRENT.json"))
    _require(source_pin.get("publication_base") == EXPECTED_PUBLICATION_BASE
             and source_pin.get("experiment_main") == EXPECTED_EXPERIMENT_MAIN
             and all(row.get("same") is True
                     and row.get("snapshot_sha256") == row.get("current_sha256")
                     for row in source_pin.get("sources", {}).values()),
             "fixed source snapshot/current-source comparison failed")

    client_root = root / "client/caller-compiled-output/client"
    result = _read_json(_safe_member(root, "client/caller-compiled-output/result.json"))
    submissions = _read_jsonl(_safe_member(
        root, "client/caller-compiled-output/client/runtime/submission-history.jsonl"))
    report = validate_result(result, submissions)

    journal = _safe_member(root, "client/caller-compiled-output/client/journal.jsonl")
    journal_state, journal_count, _journal_tip, _journal_size = inspect_journal(journal)
    _require(journal_count > 0 and type(journal_state) is dict,
             "valid append-checkpoint journal required")

    receipt = result["graph"]["receipt"]
    raw_by_sequence = {row["normalized"]["sequence"]: row
                       for row in result["graph"]["raw_observations"]}
    image_count = 0
    for observation in receipt["observations"]:
        reference = observation["evidence_ref"]
        _require(type(reference) is str and reference.startswith("runtime/"),
                 "runtime evidence reference required")
        image_path = _safe_member(client_root, "runtime/" + PurePosixPath(reference).name)
        image_hash = _sha256(image_path)
        raw = raw_by_sequence[observation["sequence"]]
        _require(raw.get("image_sha256") == image_hash,
                 "raw image digest mismatch for sequence " + str(observation["sequence"]))
        _require(raw.get("raw_observation", {}).get("image", "").endswith(
                     "/" + image_path.name),
                 "raw observation image path/name mismatch")
        expected_evidence_digest = hashlib.sha256((
            image_hash + json.dumps(observation["predicates"], sort_keys=True)
        ).encode("utf-8")).hexdigest()
        _require(observation.get("evidence_digest") == expected_evidence_digest,
                 "combined image/predicate digest mismatch")
        image_count += 1

    exact_ocr_sequence = next(row["normalized"]["sequence"]
                              for row in result["graph"]["raw_observations"]
                              if row.get("ocr", {}).get("stdout", "").strip() == EXPECTED_TOKEN)
    crop = _safe_member(root, f"client/caller-compiled-output/client/ocr-{exact_ocr_sequence}.png")
    _require(crop.stat().st_size > 0, "saved OCR crop is empty")
    tesseract = shutil.which("tesseract")
    ocr_recomputed = False
    if tesseract is not None:
        process = subprocess.run(
            [tesseract, str(crop), "stdout", "--psm", "7", "-c",
             "tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789-"],
            capture_output=True, text=True, timeout=10, check=False)
        _require(process.returncode == 0 and process.stdout.strip() == EXPECTED_TOKEN,
                 "saved OCR crop does not reproduce the exact task token")
        ocr_recomputed = True
    report["receipt_observations"] = image_count
    report["verified_journal_frames"] = journal_count
    report["saved_exact_ocr_crop"] = crop.relative_to(root).as_posix()
    report["ocr_recomputed_from_saved_crop"] = ocr_recomputed
    report["member_hashes_verified"] = len(manifest)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_PACKAGE)
    args = parser.parse_args()
    try:
        result = audit_package(args.root)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
