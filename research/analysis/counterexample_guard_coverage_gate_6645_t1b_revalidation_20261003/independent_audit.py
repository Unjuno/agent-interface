"""Read-only independent audit of the retained #6645 T1b evidence."""
import argparse
import ast
import copy
import hashlib
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath

EXPECTED_IDS = [
    "valid_complete_coverage", "known_stale_complete_coverage",
    "hidden_modal_harmful_incomplete_coverage",
    "hidden_modal_safe_incomplete_coverage", "unregistered_surface_family",
]
MANIFEST_SHA = "95aa99fcc37f0d6bf4ccdd3f2a0a515b0ef0977a937bfef6c312befbb64fd5b8"
CANDIDATE_SHA = "cfd64f422302d85ccaeb4798a5ba720a87187b3c497c375bdd1287f3c7357c3a"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key:" + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique)


def strings(value):
    return type(value) is list and all(type(item) is str for item in value)


def exact_keys(value, keys):
    return type(value) is dict and set(value) == set(keys)


def validate_records(fixture, contract, oracle, raw):
    errors = []
    if not exact_keys(fixture, ("fixture_id", "rows")):
        return ["fixture_schema"]
    if type(fixture["fixture_id"]) is not str or type(fixture["rows"]) is not list:
        return ["fixture_field_types"]
    for index, row in enumerate(fixture["rows"]):
        if not exact_keys(row, ("id", "surface_family", "covered_predicates", "observations")):
            errors.append(f"fixture_row_schema:{index}")
            continue
        covered, observations = row["covered_predicates"], row["observations"]
        if (type(row["id"]) is not str or type(row["surface_family"]) is not str
                or not strings(covered) or len(covered) != len(set(covered))
                or type(observations) is not dict
                or any(type(k) is not str or type(v) is not str for k, v in observations.items())
                or set(observations) != set(covered)):
            errors.append(f"fixture_row_field_types_or_coverage:{index}")
    if not exact_keys(contract, ("contract_id", "required_predicates", "safe_values",
                                 "contract_complete_for_fixture", "supported_surface_families")):
        errors.append("contract_schema")
    else:
        required, safe, supported = (contract["required_predicates"], contract["safe_values"],
                                    contract["supported_surface_families"])
        if (type(contract["contract_id"]) is not str
                or contract["contract_complete_for_fixture"] is not True
                or not strings(required) or len(required) != len(set(required))
                or not strings(supported) or len(supported) != len(set(supported))
                or type(safe) is not dict
                or any(type(k) is not str or type(v) is not str for k, v in safe.items())
                or (strings(required) and set(safe) != set(required))):
            errors.append("contract_field_types_or_vocabulary")
    if not exact_keys(oracle, ("oracle_id", "labels")) or type(oracle.get("labels")) is not list:
        errors.append("oracle_schema")
    else:
        if type(oracle["oracle_id"]) is not str:
            errors.append("oracle_identity_type")
        for index, label in enumerate(oracle["labels"]):
            if (not exact_keys(label, ("id", "effect")) or type(label.get("id")) is not str
                    or type(label.get("effect")) is not str
                    or label["effect"] not in ("safe", "harmful", "unknown")):
                errors.append(f"oracle_label_schema:{index}")
    if (not exact_keys(raw, ("fixture_id", "contract_id", "rows"))
            or type(raw.get("rows")) is not list):
        errors.append("raw_schema")
    else:
        if type(raw["fixture_id"]) is not str or type(raw["contract_id"]) is not str:
            errors.append("raw_identity_type")
        for index, row in enumerate(raw["rows"]):
            if (not exact_keys(row, ("id", "gate_disabled", "gate_enabled"))
                    or type(row.get("id")) is not str
                    or any(type(row.get(field)) is not str
                           or row.get(field) not in ("ADMIT", "REFUSE", "UNKNOWN")
                           for field in ("gate_disabled", "gate_enabled"))):
                errors.append(f"raw_row_schema:{index}")
    return errors


def reconstruct(row, contract, enabled):
    if enabled and (row["surface_family"] not in contract["supported_surface_families"]
                    or not set(contract["required_predicates"]).issubset(row["covered_predicates"])):
        return "UNKNOWN"
    return ("REFUSE" if any(row["observations"][predicate] != contract["safe_values"][predicate]
                           for predicate in row["covered_predicates"]) else "ADMIT")


def audit_records(fixture, contract, oracle, raw):
    errors = validate_records(fixture, contract, oracle, raw)
    if errors:
        return errors, 0
    ids = [row["id"] for row in fixture["rows"]]
    if ids != EXPECTED_IDS:
        errors.append("fixture_row_identity_or_order")
    if [row["id"] for row in raw["rows"]] != ids:
        errors.append("raw_row_identity_or_order")
    if raw["fixture_id"] != fixture["fixture_id"] or raw["contract_id"] != contract["contract_id"]:
        errors.append("raw_identity_mismatch")
    labels = {label["id"]: label["effect"] for label in oracle["labels"]}
    expected_labels = dict(zip(EXPECTED_IDS, ("safe", "harmful", "harmful", "safe", "unknown")))
    if len(labels) != len(oracle["labels"]) or labels != expected_labels:
        errors.append("oracle_labels_or_duplicates")
    if errors:
        return errors, 0
    raw_by_id = {row["id"]: row for row in raw["rows"]}
    deltas = 0
    for row in fixture["rows"]:
        actual = raw_by_id[row["id"]]
        for field, enabled in (("gate_disabled", False), ("gate_enabled", True)):
            if actual[field] != reconstruct(row, contract, enabled):
                errors.append(f"raw_decision_mismatch:{row['id']}:{field}")
        deltas += actual["gate_disabled"] != actual["gate_enabled"]
    harm, safe = fixture["rows"][2:4]
    if {k: v for k, v in harm.items() if k != "id"} != {k: v for k, v in safe.items() if k != "id"}:
        errors.append("hidden_pair_observations_differ")
    if "modal_occlusion" in harm["covered_predicates"]:
        errors.append("hidden_predicate_marked_covered")
    for row_id, field, expected in (
        (EXPECTED_IDS[2], "gate_disabled", "ADMIT"),
        (EXPECTED_IDS[2], "gate_enabled", "UNKNOWN"),
        (EXPECTED_IDS[3], "gate_enabled", "UNKNOWN"),
    ):
        if raw_by_id[row_id][field] != expected:
            errors.append("hidden_pair_required_control")
    return errors, deltas


def verify_manifest(package):
    package = Path(package).resolve()
    errors, entries, verified = [], {}, 0
    manifest = package / "SHA256SUMS"
    if digest(manifest) != MANIFEST_SHA:
        errors.append("manifest_identity_mismatch")
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        parts = line.split("  ", 1)
        if len(parts) != 2 or re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]) is None:
            errors.append(f"manifest_line_malformed:{number}")
            continue
        expected, relative = parts[0].lower(), parts[1].removeprefix("./")
        posix, windows = PurePosixPath(relative), PureWindowsPath(relative)
        target = package / relative
        if (posix.is_absolute() or windows.is_absolute() or windows.drive
                or ".." in posix.parts or ".." in windows.parts
                or not target.resolve().is_relative_to(package)):
            errors.append(f"manifest_path_unsafe:{number}")
            continue
        if relative in entries:
            errors.append("manifest_path_duplicate:" + relative)
            continue
        entries[relative] = expected
        if not target.is_file() or target.is_symlink():
            errors.append("manifest_file_missing_or_symlink:" + relative)
        elif digest(target) != expected:
            errors.append("manifest_hash_mismatch:" + relative)
        else:
            verified += 1
    if len(entries) != 30:
        errors.append(f"manifest_entry_count:{len(entries)}")
    freeze = read_json(package / "FREEZE.json")
    for name, expected in freeze["frozen_input_sha256"].items():
        normalized = name.split("/counterexample_guard_coverage_gate_6645_t1b_v1/", 1)[-1]
        if entries.get(normalized) != expected.lower():
            errors.append("freeze_manifest_mismatch:" + normalized)
    return verified, errors


def inspect_boundary(package, freeze):
    errors = []
    for role in ("candidate", "auditor"):
        root = Path(package) / "results" / "formal_01" / role
        pre, post = (read_json(root / f"container_inspect_{stage}.json") for stage in ("pre", "post"))
        if len(pre) != 1 or len(post) != 1:
            errors.append(role + "_inspect_cardinality")
            continue
        pre, post = pre[0], post[0]
        config = pre["HostConfig"]
        if pre["Image"] != freeze["image"]["image_id"] or post["Image"] != pre["Image"]:
            errors.append(role + "_image_mismatch")
        if (config.get("NetworkMode") != "none" or config.get("ReadonlyRootfs") is not True
                or config.get("CapDrop") != ["ALL"] or pre["Config"].get("User") != "65534:65534"):
            errors.append(role + "_isolation_configuration")
        for field in ("NetworkMode", "ReadonlyRootfs", "CapDrop", "Mounts"):
            if post["HostConfig"].get(field) != config.get(field):
                errors.append(role + "_post_configuration_changed:" + field)
        for field in ("User", "Cmd"):
            if post["Config"].get(field) != pre["Config"].get(field):
                errors.append(role + "_post_command_changed:" + field)
        state = post["State"]
        if (state.get("Status") != "exited" or type(state.get("ExitCode")) is not int
                or state["ExitCode"] != 0 or state.get("OOMKilled") is not False
                or type(post.get("RestartCount")) is not int or post["RestartCount"] != 0):
            errors.append(role + "_exit_receipt")
        mounts = config.get("Mounts", [])
        if role == "candidate":
            if (len(mounts) != 1 or mounts[0].get("ReadOnly") is not True
                    or not mounts[0].get("Source", "").replace("\\", "/").endswith("/candidate_input")):
                errors.append("candidate_mount_boundary")
            if any("oracle" in item.lower() for item in pre["Config"].get("Cmd", [])):
                errors.append("candidate_command_references_oracle")
        elif not mounts or any(mount.get("ReadOnly") is not True for mount in mounts):
            errors.append("auditor_mount_boundary")
    return errors


def decision_field_reads(candidate_path):
    tree = ast.parse(Path(candidate_path).read_text(encoding="utf-8"))
    decision = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "decide")
    fields = set()
    for node in ast.walk(decision):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == "row":
            if isinstance(node.slice, ast.Constant) and type(node.slice.value) is str:
                fields.add(node.slice.value)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
              and isinstance(node.func.value, ast.Name) and node.func.value.id == "row"
              and node.func.attr == "get" and node.args
              and isinstance(node.args[0], ast.Constant) and type(node.args[0].value) is str):
            fields.add(node.args[0].value)
    return sorted(fields)


def audit_label_records(fixture, retained_raw, relabelled, probe_raw):
    expected_fixture, expected_raw = copy.deepcopy(fixture), copy.deepcopy(retained_raw)
    for index, (row, output) in enumerate(zip(expected_fixture["rows"], expected_raw["rows"]), 1):
        row["id"] = output["id"] = f"case_{index:02d}"
    errors = []
    if relabelled != expected_fixture:
        errors.append("label_input_not_exact_id_only_transform")
    if probe_raw != expected_raw:
        errors.append("label_output_not_exact_expected_decisions")
    return {"status": "PASS_LABEL_RECORDS_SCOPED" if not errors else "FAIL_LABEL_RECORDS",
            "rows_compared": len(expected_raw["rows"]), "errors": errors}


def audit_package(package):
    package = Path(package).resolve()
    verified, errors = verify_manifest(package)
    fixture = read_json(package / "candidate_input/candidate_fixture.json")
    contract = read_json(package / "candidate_input/contract.json")
    oracle = read_json(package / "oracle.json")
    raw = read_json(package / "results/formal_01/candidate/raw.json")
    record_errors, deltas = audit_records(fixture, contract, oracle, raw)
    errors.extend(record_errors)
    errors.extend(inspect_boundary(package, read_json(package / "FREEZE.json")))
    candidate = package / "candidate_input/candidate.py"
    if digest(candidate) != CANDIDATE_SHA:
        errors.append("candidate_source_identity_mismatch")
    fields = decision_field_reads(candidate)
    if fields != ["covered_predicates", "observations", "surface_family"]:
        errors.append("candidate_decision_fields_changed")
    return {
        "status": "PASS_INDEPENDENT_REVALIDATION" if not errors else "FAIL_INDEPENDENT_REVALIDATION",
        "parent_manifest_sha256": digest(package / "SHA256SUMS"),
        "candidate_source_sha256": digest(candidate),
        "manifest_files_verified": verified, "rows_reconstructed": len(fixture["rows"]),
        "gate_delta_rows": deltas, "candidate_decision_fields": fields,
        "candidate_visible_ids_contain_outcome_terms": any(
            word in row["id"] for row in fixture["rows"] for word in ("safe", "harmful")),
        "candidate_decision_reads_id": "id" in fields,
        "candidate_invocations": 0,
        "source_inspection_scope": "Direct accesses in decide() of the hash-pinned source.",
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--label-fixture", type=Path)
    parser.add_argument("--label-raw", type=Path)
    args = parser.parse_args()
    if bool(args.label_fixture) != bool(args.label_raw):
        parser.error("--label-fixture and --label-raw must be supplied together")
    try:
        result = audit_package(args.package)
        if args.label_raw and not result["errors"]:
            result["label_records"] = audit_label_records(
                read_json(args.package / "candidate_input/candidate_fixture.json"),
                read_json(args.package / "results/formal_01/candidate/raw.json"),
                read_json(args.label_fixture), read_json(args.label_raw))
        success = not result["errors"] and not result.get("label_records", {}).get("errors")
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        result = {"status": "FAIL_INDEPENDENT_REVALIDATION", "candidate_invocations": 0,
                  "errors": [f"{type(error).__name__}:{error}"]}
        success = False
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

