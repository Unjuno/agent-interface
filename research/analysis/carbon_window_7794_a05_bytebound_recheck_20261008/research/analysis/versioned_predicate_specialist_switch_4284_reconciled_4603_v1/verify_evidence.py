#!/usr/bin/env python3
"""Independent, read-only reconciliation for Issue #4603.

This verifier deliberately does not import or execute the frozen formal runner
or auditor. It validates publication bytes, source identities, and retained
raw/result structure only; it never creates or changes formal rows.
"""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import lzma
import re
import tarfile
import zlib
from pathlib import Path, PurePosixPath


EXPECTED_RAW_SHA256 = "711f67b0e615ec6b4fc58dddedd490724369b6476ff6036f52e34536e72114e9"
EXPECTED_XZ_SHA256 = "a35457c72f7dffed7351e2f6b9590744e3ab323418a462f413d7ea4f85a6711d"
EXPECTED_CONTROL24_SHA256 = "dbf74500b348c9a3503e0dd489bb04d9d00f5d6a47a0c9163d4cc615ea90bb31"
EXPECTED_CONTROL24_BLOB = "92a32126cc76e4e663d7604ba454b666ec95b356"
EXPECTED_SOURCE_SHA256 = {
    "CONSTRUCTION_AUDIT.json": "3f14cb6f2889fa6cb5e5bee7d05eac9424e8bebe4b9aa6795a977f3ae3278029",
    "CONSTRUCTION_CONTROLS.json": "244e107badae96f0b1749be9979a9858ec60abfab1541149d7fd215321805b2f",
    "CONSTRUCTION_RESULT.json": "67ed3a1d9daaf14a6d5c87db3a08c69ea0e60d69cc2c6c8f9fca6b1648d12bf5",
    "ENVIRONMENT.json": "31c84808308ba5f6f85fcd0d2bed328a182bd26ecbddf2f72924cf11fe194810",
    "PLAN.md": "da6403b62955ec593de36d49ad23a1cd35d3577c223cde9c65c275a9b8e99537",
    "audit.py": "dcaf26b5b711f380a71a4ee7556c1e714c22d5a3875befc71082b7368f13f7d1",
    "runner.py": "dfe52337877ac556aa5f2c16aa8b728bb7022d0f310936c0864889c20715ffb8",
    "test_audit.py": "309c582a806ec903649609f0cdfb263f941f37b9abc660d33a946606ffcd44f2",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def load_json(data: bytes, label: str):
    try:
        return json.loads(data)
    except Exception as exc:  # pragma: no cover - diagnostic surface
        raise ValueError(f"invalid_json:{label}:{exc}") from exc


def raw_violations(data: dict) -> list[str]:
    """Independent semantic checks over a raw formal document."""
    errors = []
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list) or len(cases) != 60:
        errors.append("case_denominator")
        cases = cases if isinstance(cases, list) else []
    ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if len(ids) != 60 or len(set(ids)) != len(ids):
        errors.append("case_id_denominator_or_duplicate")
    if data.get("decision_pre_audit") != "PASS_VERSIONED_PREDICATE_SPECIALIST_SWITCH_SCOPED" or data.get("decision_errors") != []:
        errors.append("formal_decision")
    graph = {"TRUE": "SUBMIT_READY", "FALSE": "YIELD_TARGET", "UNKNOWN": "YIELD_UNKNOWN"}
    for case in cases:
        if case.get("authority") is not False:
            errors.append("case_authority")
        rows = case.get("rows", [])
        general = specialist = 0
        for row in rows:
            inputs = row.get("input", {})
            pos, neg = inputs.get("pos"), inputs.get("neg")
            oracle = "TRUE" if isinstance(pos, int) and isinstance(neg, int) and pos > neg else "FALSE" if isinstance(pos, int) and isinstance(neg, int) and pos < neg else "UNKNOWN" if pos == neg else None
            if oracle is None or row.get("truth") != oracle:
                errors.append("oracle_label")
            if case.get("policy") != "UNGUARDED_SPECIALIST_SWITCH" and row.get("output") != oracle:
                errors.append("candidate_semantic")
            if row.get("graph_truth") != graph.get(oracle) or row.get("graph_output") != graph.get(row.get("output")):
                errors.append("graph")
            if row.get("authority") is not False:
                errors.append("row_authority")
            used = row.get("used", "")
            if used.startswith("GENERAL"):
                general += 1
            elif "SPECIALIST" in used:
                specialist += 1
            else:
                errors.append("execution_path")
        if case.get("general_calls") != general or case.get("specialist_calls") != specialist:
            errors.append("call_count")
        if case.get("policy") == "SHADOW_VALIDATED_VERSIONED_SWITCH":
            activations = case.get("activations", [])
            activation_ids = [a.get("activation_id") for a in activations]
            if len(activation_ids) != len(set(activation_ids)) or any(a.get("validated_count", 0) < 4 or a.get("authority") is not False or a.get("i", -1) < a.get("validated_count", 4) - 1 for a in activations):
                errors.append("activation_integrity")
            by_id = {a.get("activation_id"): a for a in activations}
            for row in rows:
                if "SPECIALIST" in row.get("used", ""):
                    active = by_id.get(row.get("active_activation_id"))
                    inputs = row.get("input", {})
                    identity = [inputs.get("specialist_version"), inputs.get("support"), inputs.get("generation"), inputs.get("schema")]
                    if active is None or active.get("tuple") != identity:
                        errors.append("specialist_identity_unbound")
            if case.get("schedule") == "CANDIDATE_REGRESSION" and case.get("activations"):
                errors.append("regression_activation")
            if case.get("schedule") == "NOVEL_TARGET_ENCODING" and not any(f.get("reason") == "NOVEL_KEY" for f in case.get("fallbacks", [])):
                errors.append("novel_fallback")
            if case.get("schedule") in {"STALE_ACTIVATION_RECEIPT", "SUPPORT_VERSION_CHANGE", "PRODUCER_GENERATION_CHANGE"} and not any(i.get("reason") == "IDENTITY_CHANGED" for i in case.get("invalidations", [])):
                errors.append("missing_invalidation")
            if case.get("schedule") == "REQUIRED_UNKNOWN" and any(r.get("truth") == "UNKNOWN" and r.get("output") != "UNKNOWN" for r in rows):
                errors.append("unknown_collapse")
            if case.get("schedule") == "RECOVER_WITH_NEW_VERSION" and len(activation_ids) >= 2 and activation_ids[0] == activation_ids[1]:
                errors.append("activation_identity_reused")
    stable = {p: [c for c in cases if c.get("policy") == p and c.get("schedule") == "STABLE_ACTIVE"] for p in ("ALWAYS_GENERAL", "SHADOW_VALIDATED_VERSIONED_SWITCH")}
    baseline = sum(c.get("general_calls", 0) for c in stable["ALWAYS_GENERAL"])
    candidate = sum(c.get("general_calls", 0) for c in stable["SHADOW_VALIDATED_VERSIONED_SWITCH"])
    if baseline != 32 or candidate / baseline > 0.30:
        errors.append("stable_general_call_gate")
    return errors


def independent_mutation_controls(raw: dict) -> list[dict]:
    """Recreate the 13 declared tamper classes and test our own raw checks."""
    names = ["authority", "unknown", "premature", "stale", "support", "generation", "regression", "novel", "new_version", "calls", "graph", "duplicate_case", "decision"]
    outcomes = []
    for name in names:
        candidate = copy.deepcopy(raw)
        subject = next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH")
        if name == "authority": subject["rows"][0]["authority"] = True
        elif name == "unknown":
            c = next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and c["schedule"] == "REQUIRED_UNKNOWN")
            next(r for r in c["rows"] if r["truth"] == "UNKNOWN")["output"] = "TRUE"
        elif name == "premature": subject["activations"] = [{"activation_id": "bad", "validated_count": 3, "authority": False}]
        elif name in {"stale", "support", "generation"}:
            schedule = {"stale": "STALE_ACTIVATION_RECEIPT", "support": "SUPPORT_VERSION_CHANGE", "generation": "PRODUCER_GENERATION_CHANGE"}[name]
            next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and c["schedule"] == schedule)["invalidations"] = []
        elif name == "regression":
            next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and c["schedule"] == "CANDIDATE_REGRESSION")["activations"] = [{"activation_id": "bad", "validated_count": 4, "authority": False}]
        elif name == "novel":
            next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and c["schedule"] == "NOVEL_TARGET_ENCODING")["fallbacks"] = []
        elif name == "new_version":
            c = next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and c["schedule"] == "RECOVER_WITH_NEW_VERSION")
            c["activations"][-1]["activation_id"] = c["activations"][0]["activation_id"]
        elif name == "calls":
            next(c for c in candidate["cases"] if c["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and c["schedule"] == "STABLE_ACTIVE")["general_calls"] = 16
        elif name == "graph": subject["rows"][0]["graph_output"] = "YIELD_TARGET"
        elif name == "duplicate_case": candidate["cases"].append(copy.deepcopy(candidate["cases"][0]))
        elif name == "decision": candidate["decision_pre_audit"] = "FAIL_TAMPERED"
        errors = raw_violations(candidate)
        outcomes.append({"name": name, "rejected": bool(errors), "errors": sorted(set(errors))[:5]})
    return outcomes


def reconcile(root: Path, control24_path: Path | None = None) -> dict:
    root = root.resolve(strict=True)
    if (root / "EVIDENCE_MANIFEST.json").is_file():
        pkg = root
    else:
        candidates = (
            root / "research/analysis/versioned_predicate_specialist_switch_4284_reconciled_4603_v1",
            root / "research/analysis/versioned_predicate_specialist_switch_4284_v1",
        )
        pkg = next((candidate for candidate in candidates if (candidate / "EVIDENCE_MANIFEST.json").is_file()), candidates[0])
    manifest = load_json((pkg / "EVIDENCE_MANIFEST.json").read_bytes(), "manifest")

    chunks = []
    for part in manifest["parts"]:
        data = (pkg / part["file"]).read_bytes()
        if len(data) != part["bytes"] or sha256(data) != part["sha256"]:
            raise ValueError(f"part_identity_mismatch:{part['file']}")
        chunks.append(data.strip())
    xz = base64.b64decode(b"".join(chunks), validate=True)
    if len(xz) != manifest["decoded_xz_bytes"] or sha256(xz) != EXPECTED_XZ_SHA256 or manifest.get("decoded_xz_sha256") != EXPECTED_XZ_SHA256:
        raise ValueError("decoded_archive_identity_mismatch")
    if manifest.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("source_manifest_identity_mismatch")
    tar_bytes = lzma.decompress(xz)

    members = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as archive:
        infos = archive.getmembers()
        if len(infos) != manifest["members"] or len({info.name for info in infos}) != len(infos):
            raise ValueError(f"member_count_mismatch:{len(infos)}")
        for info in infos:
            name = PurePosixPath(info.name)
            if not info.isfile() or name.is_absolute() or ".." in name.parts:
                raise ValueError(f"unsafe_or_nonfile_tar_member:{info.name}")
            stream = archive.extractfile(info)
            if stream is None:
                raise ValueError(f"unreadable_member:{info.name}")
            members[info.name] = stream.read()

    for name, expected in EXPECTED_SOURCE_SHA256.items():
        if name not in members or sha256(members[name]) != expected:
            raise ValueError(f"frozen_source_hash_mismatch:{name}")
    raw_bytes = members.get("formal-01/RAW.json")
    if raw_bytes is None or sha256(raw_bytes) != EXPECTED_RAW_SHA256:
        raise ValueError("formal_raw_hash_mismatch")

    raw = load_json(raw_bytes, "formal_raw")
    result = load_json(members["formal-01/RESULT.json"], "formal_result")
    audit = load_json(members["formal-01/AUDIT.json"], "formal_audit")
    controls = load_json(members["formal-01/CONTROLS.json"], "formal_controls")
    freeze = load_json((pkg / "FREEZE.json").read_bytes(), "freeze")
    published_result = load_json((pkg / "FINAL_RESULT.json").read_bytes(), "published_result")

    independent_errors = raw_violations(raw)
    if independent_errors:
        raise ValueError("independent_raw_audit_failed:" + ",".join(sorted(set(independent_errors))))
    mutation_results = independent_mutation_controls(raw)
    if len(mutation_results) != 13 or any(not x["rejected"] for x in mutation_results):
        raise ValueError("independent_mutation_controls_failed")

    if freeze.get("formal", {}).get("cases") != 60:
        raise ValueError("freeze_case_count_not_60")
    if freeze.get("formal", {}).get("reruns") != 0 or freeze.get("formal", {}).get("replacements") != 0:
        raise ValueError("freeze_records_rerun_or_replacement")
    if freeze.get("source_sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("freeze_source_identity_mismatch")

    def count_rows(value):
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            for key in ("rows", "cases", "results", "formal_rows"):
                if isinstance(value.get(key), list):
                    return len(value[key])
        return None

    cases = raw.get("cases") if isinstance(raw, dict) else None
    if not isinstance(cases, list) or len(cases) != 60:
        raise ValueError(f"raw_case_count_not_60:{count_rows(raw)}")
    unique_cases = {case.get("case_id") for case in cases if isinstance(case, dict)}
    if len(unique_cases) != 60 or None in unique_cases:
        raise ValueError(f"unique_case_ids_not_60:{len(unique_cases)}")
    policies = {"ALWAYS_GENERAL", "UNGUARDED_SPECIALIST_SWITCH", "SHADOW_VALIDATED_VERSIONED_SWITCH"}
    schedules = {
        "PREPROMOTION_MATCH", "PROMOTE_AFTER_VALIDATION", "STABLE_ACTIVE",
        "NOVEL_TARGET_ENCODING", "SUPPORT_VERSION_CHANGE",
        "PRODUCER_GENERATION_CHANGE", "STALE_ACTIVATION_RECEIPT",
        "REQUIRED_UNKNOWN", "CANDIDATE_REGRESSION", "RECOVER_WITH_NEW_VERSION",
    }
    combos = {(case.get("policy"), case.get("schedule"), case.get("case_id", "").rsplit("-", 1)[-1]) for case in cases}
    if len(combos) != 60 or {x[0] for x in combos} != policies or {x[1] for x in combos} != schedules or {x[2] for x in combos} != {"0", "1"}:
        raise ValueError("formal_policy_schedule_repetition_matrix_mismatch")

    graph = {"TRUE": "SUBMIT_READY", "FALSE": "YIELD_TARGET", "UNKNOWN": "YIELD_UNKNOWN"}
    row_count = 0
    candidate_specialist_rows = 0
    execution_paths = set()
    unguarded_semantic_mismatches = 0
    for case in cases:
        if case.get("authority") is not False or not isinstance(case.get("rows"), list):
            raise ValueError(f"case_authority_or_rows_invalid:{case.get('case_id')}")
        for row in case["rows"]:
            row_count += 1
            inputs = row.get("input", {})
            pos, neg = inputs.get("pos"), inputs.get("neg")
            truth = "TRUE" if isinstance(pos, int) and isinstance(neg, int) and pos > neg else "FALSE" if isinstance(pos, int) and isinstance(neg, int) and pos < neg else "UNKNOWN" if pos == neg else None
            if truth is None or row.get("truth") != truth:
                raise ValueError(f"oracle_label_mismatch:{case['case_id']}:{row.get('i')}")
            if case["policy"] == "UNGUARDED_SPECIALIST_SWITCH":
                unguarded_semantic_mismatches += row.get("output") != truth
            elif row.get("output") != truth:
                raise ValueError(f"policy_output_mismatch:{case['case_id']}:{row.get('i')}")
            output = row.get("output")
            if output not in graph or row.get("graph_truth") != graph[truth] or row.get("graph_output") != graph[output]:
                raise ValueError(f"guarded_graph_mismatch:{case['case_id']}:{row.get('i')}")
            if row.get("authority") is not False:
                raise ValueError(f"row_authority_not_false:{case['case_id']}:{row.get('i')}")
            used = row.get("used")
            if not isinstance(used, str) or not used:
                raise ValueError(f"unknown_execution_path:{case['case_id']}:{row.get('i')}")
            if not used.startswith("GENERAL") and "SPECIALIST" not in used:
                raise ValueError(f"unknown_execution_path:{case['case_id']}:{row.get('i')}:{used}")
            execution_paths.add(used)
            if case["policy"] == "ALWAYS_GENERAL" and used != "GENERAL":
                raise ValueError(f"baseline_used_specialist:{case['case_id']}:{row.get('i')}")
            if case["policy"] == "SHADOW_VALIDATED_VERSIONED_SWITCH" and "SPECIALIST" in used:
                candidate_specialist_rows += 1
                if not row.get("active_activation_id"):
                    raise ValueError(f"specialist_without_activation:{case['case_id']}:{row.get('i')}")
        raw_general = sum(1 for row in case["rows"] if row["used"].startswith("GENERAL"))
        raw_specialist = sum(1 for row in case["rows"] if "SPECIALIST" in row["used"])
        if case.get("general_calls") != raw_general or case.get("specialist_calls") != raw_specialist:
            raise ValueError(f"case_call_totals_disagree_with_rows:{case['case_id']}")
    if row_count != 462 or raw.get("decision_errors") != []:
        raise ValueError(f"raw_rows_or_decisions_invalid:{row_count}")

    stable = {}
    for policy in policies:
        stable[policy] = [c for c in cases if c["policy"] == policy and c["schedule"] == "STABLE_ACTIVE"]
        if len(stable[policy]) != 2 or any(len(c["rows"]) != 16 for c in stable[policy]):
            raise ValueError(f"stable_active_denominator_invalid:{policy}")
    stable_baseline_calls = sum(sum(1 for row in c["rows"] if row["used"].startswith("GENERAL")) for c in stable["ALWAYS_GENERAL"])
    stable_candidate_calls = sum(sum(1 for row in c["rows"] if row["used"].startswith("GENERAL")) for c in stable["SHADOW_VALIDATED_VERSIONED_SWITCH"])
    stable_ratio = stable_candidate_calls / stable_baseline_calls
    if stable_ratio != 0.25 or any(c["general_calls"] != 4 or c["specialist_calls"] != 12 for c in stable["SHADOW_VALIDATED_VERSIONED_SWITCH"]):
        raise ValueError("stable_active_general_call_gate_mismatch")

    if audit.get("case_count") != 60 or audit.get("decision") != "PASS_VERSIONED_PREDICATE_SPECIALIST_SWITCH_SCOPED":
        raise ValueError("published_audit_summary_mismatch")
    if result.get("row_count") != 462 or result.get("case_count") != 60 or result.get("formal_invocations") != 1 or result.get("reruns") != 0 or result.get("replacements") != 0 or result.get("tuning") != 0:
        raise ValueError("formal_result_summary_mismatch")
    if audit.get("audit_pass") is not True or audit.get("errors") != []:
        raise ValueError("frozen_audit_not_clean")
    if published_result.get("formal_cases") != 60 or published_result.get("lifecycle_rows") != 462 or published_result.get("raw_sha256") != EXPECTED_RAW_SHA256 or published_result.get("evidence_xz_sha256") != EXPECTED_XZ_SHA256 or published_result.get("decision") != audit.get("decision"):
        raise ValueError("published_final_result_does_not_match_retained_raw")
    if published_result.get("result_sha256") != sha256(members["formal-01/RESULT.json"]) or published_result.get("audit_sha256") != sha256(members["formal-01/AUDIT.json"]) or published_result.get("controls_sha256") != sha256(members["formal-01/CONTROLS.json"]):
        raise ValueError("published_final_result_hash_link_mismatch")
    control_list = controls.get("controls") if isinstance(controls, dict) else None
    if not isinstance(control_list, list) or len(control_list) != 13 or controls.get("rejected") != 13 or controls.get("total") != 13 or any(c.get("rejected") is not True for c in control_list):
        raise ValueError("formal_corruption_controls_not_13_of_13")

    control_path = control24_path or root / "control-24/FORMAL_RESULT.json.zlib.b64"
    if control24_path is None and not control_path.is_file():
        candidates = (
            root / "research/analysis/predicate_specialist_switch_4284_v1/FORMAL_RESULT.json.zlib.b64",
            root.parent / "predicate_specialist_switch_4284_v1/FORMAL_RESULT.json.zlib.b64",
        )
        control_path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    control_encoded = control_path.read_bytes()
    if git_blob_sha1(control_encoded) != EXPECTED_CONTROL24_BLOB:
        raise ValueError("control24_current_main_blob_mismatch")
    control_raw = zlib.decompress(base64.b64decode(control_encoded.strip(), validate=True))
    control_data = load_json(control_raw, "control24")
    if sha256(control_raw) != EXPECTED_CONTROL24_SHA256 or len(control_data.get("timeline", [])) != 24 or control_data.get("formal_invocations") != 1:
        raise ValueError("control24_identity_or_denominator_mismatch")
    if not isinstance(audit, dict) or audit.get("errors") not in ([], None):
        raise ValueError("raw_audit_reports_errors")

    return {
        "status": "PASS_READONLY_PUBLICATION_RECONCILIATION",
        "raw_sha256": sha256(raw_bytes),
        "xz_sha256": sha256(xz),
        "xz_bytes": len(xz),
        "archive_members": len(members),
        "frozen_sources_verified": len(EXPECTED_SOURCE_SHA256),
        "formal_case_ids": len(unique_cases),
        "formal_rows": row_count,
        "policy_schedule_repetitions": len(combos),
        "candidate_specialist_rows": candidate_specialist_rows,
        "execution_paths": sorted(execution_paths),
        "unguarded_diagnostic_semantic_mismatches": unguarded_semantic_mismatches,
        "stable_active_candidate_general_ratio": stable_ratio,
        "corruption_controls_rejected": len(control_list),
        "independent_mutation_controls_rejected": sum(x["rejected"] for x in mutation_results),
        "control24_raw_sha256": sha256(control_raw),
        "control24_lifecycle_rows": len(control_data["timeline"]),
        "result_top_level_type": type(result).__name__,
        "audit_top_level_keys": sorted(audit) if isinstance(audit, dict) else [],
        "controls_top_level_type": type(controls).__name__,
        "published_result_top_level_type": type(published_result).__name__,
        "no_formal_runner_executed": True,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("readback_root", type=Path)
    parser.add_argument("--control24", type=Path)
    args = parser.parse_args()
    print(json.dumps(reconcile(args.readback_root, args.control24), sort_keys=True, indent=2))
