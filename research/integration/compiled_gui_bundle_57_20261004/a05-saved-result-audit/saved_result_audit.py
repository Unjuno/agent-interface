"""Offline consistency audit for the retained #57 task-1 construction records.

This checks byte custody and cross-record consistency. It does not establish
provenance, generic grounding, benchmark completion, or efficiency.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath


TASKS = tuple(f"task-{index}" for index in range(1, 7))
CASES = (
    ("graph-cropocr-output", "t991060-1", False),
    ("caller-compiled-output", "t991061-1", True),
)
IGNORED_MANIFEST_FILES = {"FILES.json", "README.md", ".gitattributes"}
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class DuplicateJSONKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def _strict_loads(value: str | bytes) -> object:
    return json.loads(value, object_pairs_hook=_unique_object)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


class _Audit:
    def __init__(self, root: Path, verify_all_manifest: bool, expected_manifest_entries: int | None):
        self.root = root.resolve()
        self.verify_all_manifest = verify_all_manifest
        self.expected_manifest_entries = expected_manifest_entries
        self.errors: list[str] = []
        self.warnings: set[str] = set()
        self.manifest: dict[str, str] = {}
        self.checked_manifest_paths: set[str] = set()
        self.checked_journal_frames = 0
        self.case_reports: list[dict[str, object]] = []

    def error(self, code: str) -> None:
        self.errors.append(code)

    def read_file(self, relative: str) -> bytes | None:
        pure = PurePosixPath(relative)
        windows = PureWindowsPath(relative)
        if ("\\" in relative or pure.is_absolute() or windows.is_absolute() or windows.drive
                or not pure.parts or any(part in ("", ".", "..") for part in pure.parts)):
            self.error(f"unsafe_path:{relative}")
            return None
        candidate = self.root.joinpath(*pure.parts)
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            self.error(f"missing_file:{relative}")
            return None
        if not resolved.is_relative_to(self.root):
            self.error(f"path_escape:{relative}")
            return None
        if not resolved.is_file():
            self.error(f"not_a_file:{relative}")
            return None
        try:
            return resolved.read_bytes()
        except OSError:
            self.error(f"unreadable_file:{relative}")
            return None

    def check_manifest_entry(self, relative: str) -> bytes | None:
        data = self.read_file(relative)
        expected = self.manifest.get(relative)
        if expected is None:
            self.error(f"manifest_entry_missing:{relative}")
            return data
        if data is not None:
            actual = hashlib.sha256(data).hexdigest()
            self.checked_manifest_paths.add(relative)
            if actual != expected:
                self.error(f"manifest_hash_mismatch:{relative}")
        return data

    def load_json(self, relative: str) -> object | None:
        data = self.check_manifest_entry(relative)
        if data is None:
            return None
        try:
            return _strict_loads(data)
        except DuplicateJSONKey:
            self.error(f"duplicate_json_key:{relative}")
            return None
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.error(f"invalid_json:{relative}")
            return None

    def load_manifest(self) -> None:
        raw = self.read_file("FILES.json")
        if raw is None:
            return
        try:
            manifest = _strict_loads(raw)
        except DuplicateJSONKey:
            self.error("duplicate_json_key:FILES.json")
            return
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.error("invalid_json:FILES.json")
            return
        if not isinstance(manifest, dict):
            self.error("manifest_not_object")
            return
        for relative, digest in manifest.items():
            if not isinstance(relative, str) or not isinstance(digest, str) or not HEX_SHA256.fullmatch(digest):
                self.error("manifest_entry_malformed")
                continue
            pure = PurePosixPath(relative)
            windows = PureWindowsPath(relative)
            if ("\\" in relative or pure.is_absolute() or windows.is_absolute() or windows.drive
                    or any(part in ("", ".", "..") for part in pure.parts)):
                self.error(f"unsafe_manifest_path:{relative}")
                continue
            self.manifest[relative] = digest
        if self.expected_manifest_entries is not None and len(self.manifest) != self.expected_manifest_entries:
            self.error("manifest_entry_count_mismatch")
        if self.verify_all_manifest:
            for relative in sorted(self.manifest):
                data = self.read_file(relative)
                if data is None:
                    continue
                self.checked_manifest_paths.add(relative)
                if hashlib.sha256(data).hexdigest() != self.manifest[relative]:
                    self.error(f"manifest_hash_mismatch:{relative}")
            try:
                present = {
                    path.relative_to(self.root).as_posix()
                    for path in self.root.rglob("*")
                    if path.is_file() and path.name not in IGNORED_MANIFEST_FILES
                }
                missing = set(self.manifest) - present
                extra = present - set(self.manifest)
                for relative in sorted(missing):
                    self.error(f"manifest_member_missing:{relative}")
                for relative in sorted(extra):
                    self.error(f"unmanifested_member:{relative}")
            except OSError:
                self.error("manifest_tree_unreadable")

    def audit_journal(self, run_root: str, programs: object, durable_calls: object, case: str) -> None:
        relative = f"{run_root}/client/journal.jsonl"
        data = self.check_manifest_entry(relative)
        if data is None:
            return
        try:
            lines = data.splitlines()
            if not data.endswith(b"\n") or not lines or len(lines) > 256 or len(data) > 16 * 1024 * 1024:
                raise ValueError("journal boundary")
            previous = None
            request_ids: set[str] = set()
            terminal_ids: set[str] = set()
            terminal_by_request: dict[str, str] = {}
            last_state: dict[str, object] | None = None
            for index, line in enumerate(lines, 1):
                frame = _strict_loads(line)
                if not isinstance(frame, dict) or set(frame) != {"version", "index", "previous", "state", "sha256"}:
                    raise ValueError("journal frame shape")
                checksum = frame.pop("sha256")
                if (frame.get("version") != "append-checkpoint-v1" or type(frame.get("index")) is not int
                        or frame["index"] != index or frame.get("previous") != previous
                        or not isinstance(frame.get("state"), dict)
                        or hashlib.sha256(_canonical(frame)).hexdigest() != checksum):
                    raise ValueError("journal hash chain")
                previous = checksum
                state = frame["state"]
                last_state = state
                pending = state.get("pending")
                if isinstance(pending, dict):
                    request = pending.get("request")
                    if isinstance(request, dict) and isinstance(request.get("request_id"), str):
                        request_ids.add(request["request_id"])
                resolution = state.get("last_resolution")
                if isinstance(resolution, dict):
                    request_id = resolution.get("request_id")
                    if isinstance(request_id, str):
                        request_ids.add(request_id)
                    terminal = resolution.get("terminal")
                    if isinstance(terminal, dict) and isinstance(terminal.get("id"), str):
                        terminal_ids.add(terminal["id"])
                        if isinstance(request_id, str):
                            prior = terminal_by_request.setdefault(request_id, terminal["id"])
                            if prior != terminal["id"]:
                                raise ValueError("request resolved to different terminal ids")
            self.checked_journal_frames += len(lines)
            if not isinstance(last_state, dict) or last_state.get("pending") is not None:
                self.error(f"{case}:journal_pending_at_end")
            program_rows = programs if isinstance(programs, list) else []
            program_ids = {
                row.get("terminal", {}).get("id")
                for row in program_rows
                if isinstance(row, dict) and isinstance(row.get("terminal"), dict)
                and isinstance(row["terminal"].get("id"), str)
            }
            if not program_rows or len(program_ids) != len(program_rows) or terminal_ids != program_ids:
                self.error(f"{case}:journal_program_id_mismatch")
            if len(set(terminal_by_request.values())) != len(terminal_by_request):
                self.error(f"{case}:journal_terminal_id_duplicated")
            if type(durable_calls) is not int or durable_calls != len(request_ids):
                self.error(f"{case}:journal_call_count_mismatch")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError):
            self.error(f"{case}:journal_chain_invalid")

    def audit_case(self, run_name: str, expected_token: str, caller_case: bool) -> None:
        case = run_name
        run_root = f"client/{run_name}"
        result_path = f"{run_root}/result.json"
        result = self.load_json(result_path)
        if not isinstance(result, dict):
            return
        if result.get("status") not in ("GRAPH_OBSERVED", "OBSERVED"):
            self.error(f"{case}:run_not_observed")
        goal = result.get("goal")
        if not isinstance(goal, dict) or goal.get("task_id") != "task-1" or goal.get("token") != expected_token:
            self.error(f"{case}:task_identity_mismatch")
        root_graph = result.get("graph") if isinstance(result.get("graph"), dict) else result
        receipt = root_graph.get("receipt")
        raw_observations = root_graph.get("raw_observations")
        if not isinstance(receipt, dict) or not isinstance(raw_observations, list):
            self.error(f"{case}:compiled_graph_missing")
            return
        transitions = receipt.get("transitions")
        if (receipt.get("outcome") != "TASK_SUCCEEDED"
                or type(receipt.get("completed_transitions")) is not int
                or receipt.get("completed_transitions") != 2
                or type(receipt.get("frontier_model_resumptions")) is not int
                or receipt.get("frontier_model_resumptions") != 0 or not isinstance(transitions, list)
                or len(transitions) != 2):
            self.error(f"{case}:compiled_receipt_mismatch")
        if receipt.get("raw_evidence_retention") == "adapter_responsibility_unverified":
            self.warnings.add("compiled_raw_evidence_retention_unverified")

        observations_by_sequence: dict[int, dict[str, object]] = {}
        observation_states: list[str] = []
        token_observations = 0
        saved_title_observations = 0
        evidence_refs: set[str] = set()
        for item in raw_observations:
            if not isinstance(item, dict):
                self.error(f"{case}:observation_malformed")
                continue
            normalized = item.get("normalized")
            raw = item.get("raw_observation")
            ocr = item.get("ocr")
            if not isinstance(normalized, dict) or not isinstance(raw, dict) or not isinstance(ocr, dict):
                self.error(f"{case}:observation_evidence_missing")
                continue
            sequence = normalized.get("sequence")
            if type(sequence) is not int or sequence in observations_by_sequence:
                self.error(f"{case}:observation_sequence_invalid")
                continue
            observations_by_sequence[sequence] = item
            observation_states.append(str(item.get("state")))
            ref = normalized.get("evidence_ref")
            if (not isinstance(ref, str) or "\\" in ref or not ref.startswith("runtime/")
                    or "/" in ref[len("runtime/"):]
                    or any(part in ("", ".", "..") for part in PurePosixPath(ref).parts)):
                self.error(f"{case}:unsafe_observation_reference")
                continue
            image_name = Path(str(raw.get("image", ""))).name
            if image_name != ref[len("runtime/"):]:
                self.error(f"{case}:observation_reference_mismatch")
                continue
            image_path = f"{run_root}/client/runtime/{image_name}"
            image = self.check_manifest_entry(image_path)
            image_hash = hashlib.sha256(image).hexdigest() if image is not None else None
            if image_hash != item.get("image_sha256"):
                self.error(f"{case}:image_digest_mismatch")
            predicates = normalized.get("predicates")
            if not isinstance(predicates, dict):
                self.error(f"{case}:observation_predicates_missing")
                continue
            expected_evidence_digest = hashlib.sha256(
                (str(item.get("image_sha256")) + json.dumps(predicates, sort_keys=True)).encode("utf-8")
            ).hexdigest()
            if normalized.get("evidence_digest") != expected_evidence_digest:
                self.error(f"{case}:normalized_evidence_digest_mismatch")
            evidence_refs.add(ref)
            crop_path = f"{run_root}/client/ocr-{sequence}.png"
            self.check_manifest_entry(crop_path)
            if type(ocr.get("exit")) is not int or ocr.get("exit") != 0:
                self.error(f"{case}:ocr_failed")
            if item.get("state") == "filled":
                token_observations += 1
                if ocr.get("stdout", "").strip() != expected_token or predicates.get("exact_token_visible") is not True:
                    self.error(f"{case}:field_token_observation_mismatch")
            elif predicates.get("exact_token_visible") is not False:
                self.error(f"{case}:token_predicate_state_mismatch")
            if predicates.get("exact_saved_title") is True:
                saved_title_observations += 1
            if predicates.get("exact_saved_title") is not (item.get("state") == "submitted"):
                self.error(f"{case}:saved_title_predicate_state_mismatch")

        if (observation_states != ["empty", "filled", "submitted"]
                or token_observations != 1 or saved_title_observations != 1):
            self.error(f"{case}:semantic_observation_count_mismatch")
        observation_sequences = list(observations_by_sequence)
        if not isinstance(transitions, list):
            transitions = []
        program_rows = result.get("programs", [])
        if not isinstance(program_rows, list):
            program_rows = []
        labels = {label: [index for index, row in enumerate(program_rows)
                          if isinstance(row, dict) and row.get("label") == label]
                  for label in ("compiled-check-field", "compiled-enter",
                                "compiled-check-submit", "compiled-submit")}
        if any(len(indices) != 1 for indices in labels.values()):
            self.error(f"{case}:compiled_program_labels_mismatch")
        else:
            indices = [labels[label][0] for label in
                       ("compiled-check-field", "compiled-enter", "compiled-check-submit", "compiled-submit")]
            if indices != sorted(indices):
                self.error(f"{case}:target_check_action_order_mismatch")
            for label, state_index in (("compiled-check-field", 0), ("compiled-check-submit", 1)):
                check_program = program_rows[labels[label][0]]
                checks = check_program.get("target_checks", [])
                expected_sequence = observation_sequences[state_index] if len(observation_sequences) > state_index else None
                if (not isinstance(checks, list) or len(checks) != 1 or not isinstance(checks[0], dict)
                        or checks[0].get("eligible") is not True or checks[0].get("status") != "VALID"
                        or checks[0].get("observation_sequence") != expected_sequence):
                    self.error(f"{case}:target_check_sequence_mismatch")
        for transition, action in zip(transitions, ("enter", "submit")):
            if not isinstance(transition, dict):
                self.error(f"{case}:transition_malformed")
                continue
            action_id = transition.get("action_id")
            expected_observation_sequence = observation_sequences[0 if action == "enter" else 1] if len(observation_sequences) > 1 else None
            if (transition.get("action") != action or transition.get("release_verified") is not True
                    or transition.get("effect_ref") != f"terminal:{action_id}"
                    or transition.get("evidence_ref") not in evidence_refs
                    or transition.get("observation_sequence") != expected_observation_sequence):
                self.error(f"{case}:transition_receipt_mismatch")
            if transition.get("observation_sequence") != expected_observation_sequence:
                self.error(f"{case}:transition_observation_sequence_mismatch")
            program = next((row for row in program_rows
                            if isinstance(row, dict) and row.get("label") == f"compiled-{action}"), None)
            terminal = program.get("terminal") if isinstance(program, dict) else None
            release = terminal.get("release") if isinstance(terminal, dict) else None
            if (not isinstance(terminal, dict) or terminal.get("id") != action_id
                    or terminal.get("status") != "completed" or not isinstance(release, dict)
                    or release.get("verified") is not True or release.get("keys_down") != []
                    or release.get("buttons_down") != [] or not program.get("pointer_admissions")):
                self.error(f"{case}:program_terminal_release_mismatch")
        latest_ref = receipt.get("latest_evidence_ref")
        if latest_ref not in evidence_refs:
            self.error(f"{case}:latest_evidence_reference_missing")

        evaluation = result.get("independent_evaluation")
        expected_counts = {task: int(task == "task-1") for task in TASKS}
        exact_counts = evaluation.get("exact_counts") if isinstance(evaluation, dict) else None
        if (not isinstance(evaluation, dict) or evaluation.get("success") is not False
                or type(evaluation.get("record_count")) is not int or evaluation.get("record_count") != 1
                or not isinstance(exact_counts, dict)
                or any(type(exact_counts.get(task)) is not int for task in TASKS)
                or exact_counts != expected_counts
                or evaluation.get("missing") != list(TASKS[1:])
                or evaluation.get("unexpected") != [] or evaluation.get("duplicates") != {}):
            self.error(f"{case}:full_six_status_contradicts_one_task_record")

        history_path = f"{run_root}/client/runtime/submission-history.jsonl"
        history = self.check_manifest_entry(history_path)
        try:
            rows = [_strict_loads(line) for line in history.splitlines()] if history is not None else []
            if (len(rows) != 1 or not isinstance(rows[0], dict) or rows[0].get("task_id") != "task-1"
                    or rows[0].get("expected_token") != expected_token
                    or rows[0].get("submitted_values") != [expected_token]
                    or rows[0].get("exact") is not True):
                self.error(f"{case}:post_token_mismatch")
        except (json.JSONDecodeError, UnicodeDecodeError, DuplicateJSONKey):
            self.error(f"{case}:submission_history_invalid")

        self.audit_journal(run_root, result.get("programs"), result.get("durable_calls"), case)
        if caller_case:
            caller = result.get("caller")
            if (not isinstance(caller, dict) or caller.get("outcome") != "TASK_SUCCEEDED"
                    or caller.get("reason") != "verified_effect" or caller.get("task_effect") != "succeeded"
                    or caller.get("delivery") != "confirmed"
                    or caller.get("route") != "reuse"
                    or not isinstance(caller.get("execution_progress"), dict)
                    or caller["execution_progress"].get("status") != "completed"):
                self.error(f"{case}:caller_result_mismatch")
            if isinstance(caller, dict):
                caller_receipt = caller.get("effect_receipt")
                if not isinstance(caller_receipt, dict) or not all(
                        isinstance(caller_receipt.get(field), str)
                        for field in ("evidence_ref", "evidence_digest", "effect_scope")):
                    self.warnings.add("caller_effect_evidence_receipt_absent")
                comparison = caller.get("comparison")
                if not isinstance(comparison, dict) or comparison.get("class") != "warm_reuse":
                    self.error(f"{case}:caller_comparison_class_mismatch")
                if (caller.get("route") == "reuse" and isinstance(comparison, dict)
                        and comparison.get("class") == "warm_reuse"):
                    if goal.get("phase") == "cold":
                        self.warnings.add("caller_phase_label_conflict")
            setup = result.get("setup")
            if not isinstance(setup, dict) or type(setup.get("elapsed_ns")) is not int or setup.get("elapsed_ns") <= 0:
                self.error(f"{case}:setup_cost_not_recorded")
            if isinstance(setup, dict) and "unavailable" not in str(setup.get("grounding", "")).lower():
                self.warnings.add("prior_human_grounding_cost_not_available")
            accounting = caller.get("accounting", {}) if isinstance(caller, dict) else {}
            if (not isinstance(accounting, dict) or accounting.get("attempted_calls") != 0
                    or caller.get("model_call_ledger") != []):
                self.error(f"{case}:unexpected_model_accounting")
        self.case_reports.append({"run": run_name, "task": "task-1", "token": expected_token,
                                  "independent_full_six": "INCOMPLETE", "frontier_model_resumptions": 0})

    def run(self) -> dict[str, object]:
        self.load_manifest()
        for run_name, token, caller_case in CASES:
            self.audit_case(run_name, token, caller_case)
        unique_errors = sorted(set(self.errors))
        return {
            "integrity": "PASS" if not unique_errors else "FAIL",
            "scope": "two fixed-layout task-1 constructions only",
            "decision": "HOLD_FULL_MATCHED_COMPARISON",
            "errors": unique_errors,
            "warnings": sorted(self.warnings),
            "checked_manifest_files": len(self.checked_manifest_paths),
            "checked_journal_frames": self.checked_journal_frames,
            "cases": self.case_reports,
            "limitations": [
                "the audit verifies consistency and byte hashes, not independent provenance",
                "one task-1 POST per case does not satisfy the six-task evaluator",
                "freshly pre-minted references are not measured cross-task warm reuse",
                "no A/B/C/D efficiency or second-domain claim is made",
            ],
        }


def audit_bundle(bundle: Path, *, verify_all_manifest: bool = True,
                 expected_manifest_entries: int | None = None) -> dict[str, object]:
    """Check the two preregistered task-1 outputs without executing either run."""
    return _Audit(Path(bundle), verify_all_manifest, expected_manifest_entries).run()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="path to chromium_client_57_4d74_20261004")
    args = parser.parse_args()
    report = audit_bundle(args.bundle, verify_all_manifest=True, expected_manifest_entries=360)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["integrity"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
