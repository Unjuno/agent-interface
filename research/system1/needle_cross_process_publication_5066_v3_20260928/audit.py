"""Independent raw-only auditor; imports neither runner.py nor model.py."""
from __future__ import annotations

import base64
import bisect
import copy
import hashlib
import json
from pathlib import Path

OLD_GENERATION = 3788
PUBLICATIONS = 4096
READERS = 4
INPUT_SHA256 = "2e7bff5a2c6ffd35935c5e3c88d08cb686fb736d332c8d5cdb24bb1b67dc873a"
INPUT_GIT_BLOB = "45b80150dac503f4eb6f3cb5d82f9afa2c587107"
ALLOCATION = "needle-cross-process-publication-overlap-5066-v3-20260928-01"


def _canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _payload_digest(package):
    body = {key: value for key, value in package.items() if key != "payload_sha256"}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _expected_package(seed, sequence):
    value = copy.deepcopy(seed)
    value["generation"] = OLD_GENERATION + sequence
    value["provenance"] = dict(value["provenance"])
    value["provenance"].update({
        "allocation": ALLOCATION,
        "predecessor_issue": 5066,
        "publication_sequence": sequence,
    })
    value["payload_sha256"] = _payload_digest(value)
    return _canonical(value)


def _strict_overlap(a_start, a_end, b_start, b_end):
    return type(a_start) is int and type(a_end) is int and type(b_start) is int and type(b_end) is int and max(a_start, b_start) < min(a_end, b_end)


def _seed():
    encoded = (Path("/src") / "seed_skill.json.b64").read_bytes().strip()
    raw = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA256:
        raise ValueError("seed_sha256")
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if blob != INPUT_GIT_BLOB:
        raise ValueError("seed_git_blob")
    value = json.loads(raw)
    if type(value) is not dict or type(value.get("generation")) is not int or value["generation"] != OLD_GENERATION:
        raise ValueError("seed_generation")
    return raw, value


def _expected_map(seed, sequences):
    result = {}
    for sequence in sequences:
        raw = _expected_package(seed, sequence)
        result[OLD_GENERATION + sequence] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "raw": raw,
        }
    return result


def validate_complete_row(row, expected, pid):
    if not isinstance(row, dict):
        return False
    generation = row.get("generation")
    target = expected.get(generation)
    if target is None:
        return False
    times = ("open_start_ns", "open_end_ns", "read_start_ns", "read_end_ns")
    if any(type(row.get(key)) is not int for key in times):
        return False
    if not (row["open_start_ns"] < row["open_end_ns"] <= row["read_start_ns"] <= row["read_end_ns"]):
        return False
    return (
        row.get("pid") == pid
        and row.get("parse_ok") is True
        and row.get("package_valid") is True
        and row.get("bytes") == target["bytes"]
        and row.get("raw_sha256") == target["sha256"]
        and row.get("phase_before") in (0, 1, 2)
    )


def count_overlapping_publications(row, publications):
    ends = [event["end_ns"] for event in publications]
    starts = [event["start_ns"] for event in publications]
    index = bisect.bisect_right(ends, row["open_start_ns"])
    return int(index < len(ends) and starts[index] < row["open_end_ns"])


def corruption_controls(valid_row, expected, pid):
    cases = {}
    for name, mutate in (
        ("wrong_pid", lambda r: r.update(pid=pid + 100000)),
        ("parse_failure", lambda r: r.update(parse_ok=False)),
        ("invalid_payload_digest", lambda r: r.update(package_valid=False)),
        ("wrong_generation", lambda r: r.update(generation=999999)),
        ("wrong_raw_hash", lambda r: r.update(raw_sha256="0" * 64)),
        ("wrong_byte_count", lambda r: r.update(bytes=r.get("bytes", 0) + 1)),
        ("inverted_open_interval", lambda r: r.update(open_end_ns=r.get("open_start_ns", 0))),
        ("unknown_phase", lambda r: r.update(phase_before=99)),
    ):
        challenge = copy.deepcopy(valid_row)
        mutate(challenge)
        cases[name] = not validate_complete_row(challenge, expected, pid)
    return cases


def audit_raw(raw, seed_raw, seed):
    errors = []
    if not isinstance(raw, dict):
        return ["raw_not_object"], {}, {"atomic_overlap_count": 0, "atomic_overlap_pids": []}
    expected_top = {
        "schema": "needle-publication-overlap-raw-v1",
        "allocation": ALLOCATION,
        "issue": 5082,
        "formal_invocations": 1,
        "image_id": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
        "input_git_blob": INPUT_GIT_BLOB,
        "input_sha256": INPUT_SHA256,
        "input_bytes": len(seed_raw),
        "publication_operations_expected": PUBLICATIONS,
        "reader_count_per_arm": READERS,
        "dispatch_count": 0,
        "authority_granted": False,
    }
    for key, value in expected_top.items():
        if raw.get(key) != value:
            errors.append("top_" + key)
    arms = raw.get("arms")
    if not isinstance(arms, list) or len(arms) != 2:
        return errors + ["arm_count"], {}, {"atomic_overlap_count": 0, "atomic_overlap_pids": []}
    by_name = {arm.get("arm"): arm for arm in arms if isinstance(arm, dict)}
    if set(by_name) != {"atomic", "diagnostic"}:
        return errors + ["arm_names"], {}, {"atomic_overlap_count": 0, "atomic_overlap_pids": []}

    atomic_expected = _expected_map(seed, range(1, PUBLICATIONS + 1))
    atomic_expected[OLD_GENERATION] = {
        "sha256": hashlib.sha256(seed_raw).hexdigest(),
        "bytes": len(seed_raw),
        "raw": seed_raw,
    }
    diagnostic_sequence = PUBLICATIONS + 1
    diagnostic_expected = _expected_map(seed, range(1, PUBLICATIONS + 2))
    diagnostic_expected[OLD_GENERATION] = {
        "sha256": hashlib.sha256(seed_raw).hexdigest(),
        "bytes": len(seed_raw),
        "raw": seed_raw,
    }
    overlap_count = 0
    overlap_pids = set()
    observed_denominator = {}
    representatives = {}
    atomic_pids = set()
    diagnostic_pids = set()
    partial_read_count = 0
    partial_read_pids = set()

    for name in ("atomic", "diagnostic"):
        arm = by_name[name]
        expected_publications = PUBLICATIONS if name == "atomic" else 1
        pubs = arm.get("publications")
        if not isinstance(pubs, list) or len(pubs) != expected_publications or arm.get("publication_count") != expected_publications:
            errors.append(name + "_publication_count")
            pubs = pubs if isinstance(pubs, list) else []
        expected_seq = range(1, PUBLICATIONS + 1) if name == "atomic" else (diagnostic_sequence,)
        for index, (event, seq) in enumerate(zip(pubs, expected_seq), start=1):
            if (event.get("sequence") != seq or event.get("generation") != OLD_GENERATION + seq
                    or type(event.get("start_ns")) is not int or type(event.get("end_ns")) is not int
                    or event["start_ns"] >= event["end_ns"]):
                errors.append(name + "_publication_event_" + str(index))
                break
        if arm.get("writer_error") is not None or arm.get("writer_start_ns") is None or arm.get("writer_end_ns") is None:
            errors.append(name + "_writer_receipt")
        if arm.get("reader_initial_samples_ready") != READERS:
            errors.append(name + "_initial_samples_not_ready")
        if name == "diagnostic" and arm.get("reader_partial_barrier_ready") != READERS:
            errors.append("diagnostic_partial_barrier_not_ready")
        readers = arm.get("readers")
        if not isinstance(readers, list) or len(readers) != READERS or arm.get("reader_count") != READERS:
            errors.append(name + "_reader_count")
            readers = readers if isinstance(readers, list) else []
        local_pids = set()
        for reader in readers:
            pid = reader.get("pid")
            if type(pid) is not int or pid <= 0 or pid in local_pids or reader.get("exit_code") != 0:
                errors.append(name + "_reader_identity_or_exit")
                continue
            local_pids.add(pid)
            relative = reader.get("path")
            path = Path("/out") / relative if isinstance(relative, str) else None
            summary = reader.get("summary")
            if not isinstance(summary, dict) or summary.get("pid") != pid or summary.get("error") is not None or summary.get("limit_hit") is not False:
                errors.append(name + "_reader_summary")
            count = 0
            if path is None or not path.is_file():
                errors.append(name + "_reader_log_missing")
                continue
            try:
                with path.open("r", encoding="utf-8") as stream:
                    for line in stream:
                        row = json.loads(line)
                        count += 1
                        if name == "atomic":
                            valid = validate_complete_row(row, atomic_expected, pid)
                            if not valid:
                                errors.append("atomic_invalid_complete_read")
                            else:
                                representatives.setdefault("atomic", row)
                                if count_overlapping_publications(row, pubs):
                                    overlap_count += 1
                                    overlap_pids.add(pid)
                        else:
                            phase = row.get("phase_before")
                            if phase == 1:
                                candidate = diagnostic_expected[OLD_GENERATION + diagnostic_sequence]
                                expected_partial = candidate["raw"][:arm.get("partial_bytes", -1)]
                                partial_ok = (
                                    row.get("pid") == pid
                                    and type(row.get("open_start_ns")) is int
                                    and type(row.get("open_end_ns")) is int
                                    and row["open_start_ns"] < row["open_end_ns"]
                                    and row.get("bytes") == len(expected_partial)
                                    and row.get("raw_sha256") == hashlib.sha256(expected_partial).hexdigest()
                                    and row.get("parse_ok") is False
                                    and row.get("package_valid") is False
                                )
                                complete_ok = validate_complete_row(row, diagnostic_expected, pid)
                                if not (partial_ok or complete_ok):
                                    errors.append("diagnostic_partial_or_complete_read")
                                if partial_ok:
                                    representatives.setdefault("diagnostic_partial", row)
                                    partial_read_count += 1
                                    partial_read_pids.add(pid)
                                else:
                                    old_ok = (
                                        row.get("pid") == pid
                                        and row.get("raw_sha256") == hashlib.sha256(seed_raw).hexdigest()
                                        and row.get("bytes") == len(seed_raw)
                                        and row.get("generation") == OLD_GENERATION
                                        and row.get("package_valid") is True
                                        and row.get("parse_ok") is True
                                    )
                                    if not (old_ok or complete_ok):
                                        errors.append("diagnostic_phase_one_read")
                            elif not validate_complete_row(row, diagnostic_expected, pid):
                                # Before the truncate, only the exact old package is valid.
                                old_ok = (
                                    row.get("phase_before") == 0
                                    and row.get("pid") == pid
                                    and row.get("raw_sha256") == hashlib.sha256(seed_raw).hexdigest()
                                    and row.get("bytes") == len(seed_raw)
                                    and row.get("generation") == OLD_GENERATION
                                    and row.get("package_valid") is True
                                    and row.get("parse_ok") is True
                                )
                                if not old_ok:
                                    errors.append("diagnostic_nonpartial_read")
                if summary.get("rows") != count or count == 0:
                    errors.append(name + "_reader_denominator")
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                errors.append(name + "_reader_log_invalid")
            observed_denominator[name + ":" + str(pid)] = count
        if name == "atomic":
            atomic_pids = local_pids
        else:
            diagnostic_pids = local_pids

    if atomic_pids & diagnostic_pids:
        errors.append("reader_processes_not_fresh")
    diag_rep = representatives.get("diagnostic_partial")
    overlap = {
        "atomic_overlap_count": overlap_count,
        "atomic_overlap_pids": sorted(overlap_pids),
        "partial_read_observed": diag_rep is not None,
        "partial_read_count": partial_read_count,
        "partial_read_pids": sorted(partial_read_pids),
        "reader_log_denominator": observed_denominator,
    }
    return errors, representatives, overlap


def main():
    out = Path("/out")
    raw_path = out / "raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    seed_raw, seed = _seed()
    errors, reps, overlap = audit_raw(raw, seed_raw, seed)
    controls = {}
    if "atomic" in reps:
        controls = corruption_controls(reps["atomic"], _expected_map(seed, range(1, PUBLICATIONS + 1)), reps["atomic"]["pid"])
    status = "PASS_ATOMIC_REPLACEMENT_OVERLAP_SCOPED"
    if errors:
        status = "FAIL_PARTIAL_OR_INCONSISTENT_READ"
    elif overlap["atomic_overlap_count"] < 32 or len(overlap["atomic_overlap_pids"]) < 2:
        status = "HOLD_NO_OVERLAP_OBSERVED"
    elif not overlap["partial_read_observed"]:
        status = "FAIL_DIAGNOSTIC_SENSITIVITY"
    elif len(controls) != 8 or not all(controls.values()):
        status = "FAIL_AUDIT_CONTROLS"
    report = {
        "schema": "needle-publication-overlap-audit-v1",
        "status": status,
        "audit_errors": errors,
        "atomic_overlap": overlap,
        "corruption_controls_rejected": sum(controls.values()),
        "corruption_controls_total": len(controls),
        "corruption_control_results": controls,
        "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
        "scope": "single-host Linux local-filesystem synthetic package publication",
    }
    (out / "audit.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if status == "PASS_ATOMIC_REPLACEMENT_OVERLAP_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
