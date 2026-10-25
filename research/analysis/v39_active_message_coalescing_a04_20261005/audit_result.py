"""Independently reconstruct the retained A04 loopback result."""

from __future__ import annotations

import base64
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _function_outputs(request):
    return [
        row for row in request.get("input", [])
        if isinstance(row, dict) and row.get("type") == "function_call_output"
    ]


def _reconstruct_delivery(requests, texts, frame_data):
    observations = []
    for text, image_data in zip(texts, frame_data, strict=True):
        occurrences = []
        text_seen = False
        image_seen = False
        for request_index, request in enumerate(requests):
            serialized_request = json.dumps(request, separators=(",", ":"))
            text_position = serialized_request.find(text)
            image_position = serialized_request.find(image_data)
            text_seen |= text_position >= 0
            image_seen |= image_position >= 0
            paired = [
                row for row in _function_outputs(request)
                if text in json.dumps(row, separators=(",", ":"))
                and image_data in json.dumps(row, separators=(",", ":"))
            ]
            if text_position >= 0 or image_position >= 0:
                occurrences.append({
                    "request_index": request_index,
                    "paired": bool(paired),
                    "text_position": text_position,
                    "image_position": image_position,
                })
        if len(occurrences) == 1:
            occurrence = occurrences[0]
            occurrence.update({"text_seen": text_seen, "image_seen": image_seen})
        elif not occurrences:
            occurrence = {
                "request_index": -1, "paired": False,
                "text_seen": False, "image_seen": False,
                "text_position": -1, "image_position": -1,
            }
        else:
            occurrence = {
                "request_index": -1, "paired": False,
                "text_seen": text_seen, "image_seen": image_seen,
                "text_position": -1, "image_position": -1,
            }
        observations.append(occurrence)

    if observations[0]["paired"] and observations[1]["paired"]:
        first, second = observations
        if first["request_index"] > second["request_index"]:
            label = "BOTH_REVERSED"
        elif first["request_index"] == second["request_index"]:
            if (first["text_position"] < first["image_position"]
                    < second["text_position"] < second["image_position"]):
                label = "BOTH_IN_ONE_FOLLOWUP_ORDERED"
            else:
                label = "BOTH_UNORDERED"
        elif (first["text_position"] < first["image_position"]
              and second["text_position"] < second["image_position"]):
            label = "BOTH_ACROSS_FOLLOWUPS_ORDERED"
        else:
            label = "BOTH_UNORDERED"
    elif not observations[0]["paired"] and observations[1]["paired"]:
        label = "LATEST_ONLY"
    elif observations[0]["paired"] and not observations[1]["paired"]:
        label = "FIRST_ONLY"
    elif any(row["text_seen"] or row["image_seen"] for row in observations):
        label = "PARTIAL_OR_UNVERIFIABLE"
    else:
        label = "NEITHER_OBSERVED"
    return label, observations



def _rpc_gate_label(replies, same_turn: bool, statuses) -> str | None:
    """Return only an RPC-level override; otherwise leave delivery classification intact."""
    if not isinstance(replies, list) or len(replies) != 2 or any(not isinstance(reply, dict) for reply in replies):
        return "UNVERIFIABLE"
    if any(isinstance(reply.get("error"), dict) for reply in replies):
        return "RPC_REJECTED"
    if (not same_turn or statuses != ["inProgress", "inProgress"]
            or any(not isinstance(reply.get("result"), dict) for reply in replies)):
        return "UNVERIFIABLE"
    return None


def _verify_manifest() -> list[str]:
    errors = []
    manifest = ROOT / "SHA256SUMS"
    if not manifest.is_file():
        return ["SHA256SUMS is missing"]
    expected_paths = set()
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        try:
            expected_hash, relative = line.split("  ", 1)
        except ValueError:
            errors.append(f"malformed SHA256SUMS line {line_number}")
            continue
        path = ROOT / relative
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            errors.append(f"unsafe manifest path on line {line_number}")
            continue
        expected_paths.add(relative)
        if not path.is_file():
            errors.append(f"manifest file is missing: {relative}")
        elif _sha(path) != expected_hash:
            errors.append(f"manifest hash mismatch: {relative}")
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and path != manifest
        and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    if expected_paths != actual_paths:
        errors.append("manifest inventory does not match package files")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-manifest", action="store_true")
    args = parser.parse_args()
    frozen = _load(ROOT / "FROZEN.json")
    candidate_path = ROOT / "results" / "candidate.stdout.json"
    exit_path = ROOT / "results" / "candidate.exit"
    if not candidate_path.is_file() or not exit_path.is_file():
        raise SystemExit("candidate output or exit receipt is missing")
    candidate = _load(candidate_path)
    exit_code = int(exit_path.read_text(encoding="utf-8").strip())
    command_record = _load(ROOT / "results" / "candidate.command.json")
    start_record = _load(ROOT / "results" / "candidate.started.json")
    frames = [
        (ROOT / path).read_bytes()
        for path in frozen["fixture_sha256"]
    ]
    frame_hashes = [hashlib.sha256(frame).hexdigest() for frame in frames]
    texts = frozen["observation_texts"]
    frame_data = ["data:image/png;base64," + base64.b64encode(frame).decode("ascii")
                  for frame in frames]
    requests = candidate["raw_requests"]
    integrity_errors = []
    raw_label, rows = _reconstruct_delivery(requests, texts, frame_data)
    if not requests:
        integrity_errors.append("no raw model requests were retained")
    else:
        first_request_text = json.dumps(requests[0], separators=(",", ":"))
        if any(text in first_request_text for text in texts) or any(
            image in first_request_text for image in frame_data
        ):
            integrity_errors.append("initial request unexpectedly contains a test observation")

    replies = candidate.get("observation_rpc_replies")
    rpc_gate_label = _rpc_gate_label(
        replies, candidate.get("same_turn_ids") is True,
        candidate.get("external_turn_statuses_at_ack"),
    )
    if rpc_gate_label is not None:
        raw_label = rpc_gate_label

    for path, expected in frozen["source_sha256"].items():
        if _sha(ROOT / path) != expected:
            integrity_errors.append(f"frozen source hash mismatch: {path}")
    for path, expected in frozen["construction_evidence_sha256"].items():
        if _sha(ROOT / path) != expected:
            integrity_errors.append(f"construction evidence hash mismatch: {path}")
    if _sha(ROOT / "environment" / "runtime-selection.txt") != frozen["runtime_selection_sha256"]:
        integrity_errors.append("runtime-selection evidence hash mismatch")

    for path, expected in {
        "probe.py": frozen["candidate_sha256"],
        "test_probe.py": frozen["test_sha256"],
        "make_frames.py": frozen["fixture_generator_sha256"],
        "README.md": frozen["readme_sha256"],
        "audit_result.py": frozen["auditor_sha256"],
        "run_candidate.ps1": frozen["runner_sha256"],
        "write_manifest.py": frozen["manifest_generator_sha256"],
    }.items():
        actual = _sha(ROOT / path)
        if actual != expected:
            integrity_errors.append(f"source hash mismatch: {path}")
    for path, expected in frozen["fixture_sha256"].items():
        if _sha(ROOT / path) != expected:
            integrity_errors.append(f"fixture hash mismatch: {path}")
    for path, expected in frozen["environment_preflight_sha256"].items():
        if _sha(ROOT / path) != expected:
            integrity_errors.append(f"environment preflight hash mismatch: {path}")

    if candidate["base_commit"] != frozen["base_commit"]:
        integrity_errors.append("candidate base commit mismatch")
    if candidate["cli_version"] != frozen["cli_version"]:
        integrity_errors.append("CLI version mismatch")
    if candidate["codex_executable_sha256"] != frozen["codex_sha256"]:
        integrity_errors.append("Codex executable hash mismatch")
    if str(candidate.get("codex_executable", "")).lower() != frozen["codex_executable"].lower():
        integrity_errors.append("Codex executable path mismatch")
    if candidate["network_override_keys_removed"] is None:
        integrity_errors.append("network override environment cleanup is unrecorded")
    if not candidate["loopback_only"] or not candidate["temporary_codex_home"]:
        integrity_errors.append("isolation assertion missing")
    if candidate["delivery_class"] != raw_label:
        integrity_errors.append("candidate delivery label disagrees with raw reconstruction")
    if candidate["turn_completed"] is not True or candidate["server_errors"]:
        integrity_errors.append("turn completion or mock server integrity failed")
    if (candidate.get("app_server_stdout_capture_complete") is not True
            or candidate.get("app_server_stderr_capture_complete") is not True):
        integrity_errors.append("App Server stdout/stderr capture did not finish")
    if not isinstance(replies, list) or len(replies) != 2:
        integrity_errors.append("both observation RPC replies were not retained")
    expected_argv = ["-B", "probe.py", "--frame-201", "fixtures/synthetic-seq201.png",
                     "--frame-202", "fixtures/synthetic-seq202.png"]
    for record_name, record in (("candidate.command.json", command_record),
                                ("candidate.started.json", start_record)):
        if record.get("candidate_runs") != 1 or record.get("retries") != 0:
            integrity_errors.append(f"one-shot run count mismatch in {record_name}")
        if record.get("run_id") != command_record.get("run_id"):
            integrity_errors.append(f"run identity mismatch in {record_name}")
        if record.get("argv") != expected_argv:
            integrity_errors.append(f"candidate argv mismatch in {record_name}")
        if record.get("base_commit") != frozen["base_commit"]:
            integrity_errors.append(f"candidate base mismatch in {record_name}")
        if (str(record.get("python_executable", "")).lower() != frozen["python"]["path"].lower()
                or record.get("python_sha256") != frozen["python"]["sha256"]
                or record.get("python_version") != frozen["python"]["version"]):
            integrity_errors.append(f"Python identity mismatch in {record_name}")
        if (str(record.get("codex_executable", "")).lower() != frozen["codex_executable"].lower()
                or record.get("codex_sha256") != frozen["codex_sha256"]):
            integrity_errors.append(f"Codex identity mismatch in {record_name}")
    acks = candidate.get("observation_ack_ns", [])
    if candidate.get("observation_rpc_accepted_count") != sum("result" in reply for reply in replies or []):
        integrity_errors.append("observation RPC accepted-count summary mismatch")
    if len(requests) != candidate["mock_request_count"]:
        integrity_errors.append("raw request count mismatch")
    if len(candidate["request_received_ns"]) != len(requests):
        integrity_errors.append("request receipt timestamp count mismatch")
    elif (candidate["request_received_ns"] != sorted(candidate["request_received_ns"])
          or len(candidate["request_received_ns"]) == 0
          or len(acks) != 2
          or candidate["request_received_ns"][0] > acks[0]):
        integrity_errors.append("initial request/observation timestamp order mismatch")
    response_sent = candidate.get("first_response_sent_ns")
    response_release = candidate.get("first_response_release_ns")
    if (type(response_sent) is not int or type(response_release) is not int
            or response_sent < response_release):
        integrity_errors.append("first mock response preceded the release gate")
    if (len(acks) != 2 or type(acks[-1]) is not int or type(response_release) is not int
            or acks[-1] + 2_000_000_000 > response_release):
        integrity_errors.append("fixed pending window was shorter than 2.0 seconds")
    if (not candidate["app_server_protocol_messages"]
            or not any(message.get("method") == "turn/completed"
                       for message in candidate["app_server_protocol_messages"])):
        integrity_errors.append("terminal App Server notification missing")
    if exit_code != 0:
        integrity_errors.append(f"candidate returned nonzero exit code {exit_code}")
    if args.verify_manifest:
        integrity_errors.extend(_verify_manifest())

    result = {
        "status": "PASS_A04_INDEPENDENT_AUDIT" if not integrity_errors else "FAIL_A04_AUDIT",
        "base_commit": frozen["base_commit"],
        "candidate_exit": exit_code,
        "delivery_class_reconstructed": raw_label,
        "observation_delivery": rows,
        "request_count": len(requests),
        "request_received_ns": candidate["request_received_ns"],
        "pending_window_elapsed_ns": (
            response_release - acks[-1]
            if type(response_release) is int and len(acks) == 2 and type(acks[-1]) is int
            else None
        ),
        "fixture_hashes_verified": frame_hashes == list(frozen["fixture_sha256"].values()),
        "candidate_and_rpc_identity_verified": candidate["same_turn_ids"],
        "mock_errors": candidate["server_errors"],
        "integrity_errors": integrity_errors,
        "scope": "loopback App Server serialization only; no model inference or computer-control effect",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS_A04_INDEPENDENT_AUDIT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
