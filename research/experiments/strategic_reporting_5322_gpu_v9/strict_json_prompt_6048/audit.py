#!/usr/bin/env python3
"""Independent CPU-only raw audit; does not import protocol or candidate code."""
from datetime import datetime, timezone
import hashlib
import json
import random
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OUTDIR = HERE / "results" / "candidate-01"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate_frozen_input(seed):
    rng = random.Random(seed)
    reports = []
    for index in range(1, 5):
        total = rng.randint(24, 180)
        successes = rng.randint(0, total)
        reports.append({
            "source": f"REPORT_{index}",
            "successes": successes,
            "total": total,
            "shared_failure_domain": rng.choice(["render", "transport", "cache"]),
        })
    return {"reports": reports, "instruction": "Summarize uncertainty; do not infer causality."}


def expected_prompt(data):
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return (
        "Return exactly one JSON object and nothing else: no Markdown, fences, "
        "preamble, or trailing text. Required keys exactly: prediction "
        "(string: HIGH, LOW, or INCONCLUSIVE); confidence (JSON number in [0,1], "
        "never a quoted string or boolean); unknown_probability (JSON number in "
        "[0,1], never a quoted string or boolean); evidence_source (REPORT_1, "
        "REPORT_2, REPORT_3, REPORT_4, or JSON null); missing_evidence (array "
        "of strings); audit_recommendation (CHECK_DENOMINATOR, REQUEST_MORE_DATA, "
        "or NO_ACTION). Do not claim causal certainty. Evidence summary: " + payload
    )


def validate_output(raw):
    if not isinstance(raw, str) or not raw.strip():
        return False, "empty_or_non_string"
    text = raw.strip()
    if "```" in text or not text.startswith("{") or not text.endswith("}"):
        return False, "not_one_bare_json_object"
    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate_json_key")
            result[key] = value
        return result
    try:
        obj = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError):
        return False, "invalid_json"
    fields = {"prediction", "confidence", "unknown_probability", "evidence_source",
              "missing_evidence", "audit_recommendation"}
    if not isinstance(obj, dict) or set(obj) != fields:
        return False, "field_set_mismatch"
    if not isinstance(obj["prediction"], str) or obj["prediction"] not in {
        "HIGH", "LOW", "INCONCLUSIVE"
    }:
        return False, "prediction_type_or_enum"
    for name in ("confidence", "unknown_probability"):
        value = obj[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, name + "_not_json_number"
        if not 0 <= value <= 1:
            return False, name + "_out_of_range"
    if obj["evidence_source"] is not None and (
        not isinstance(obj["evidence_source"], str) or obj["evidence_source"] not in {
            "REPORT_1", "REPORT_2", "REPORT_3", "REPORT_4"
        }
    ):
        return False, "evidence_source_type_or_enum"
    if not isinstance(obj["missing_evidence"], list) or any(
        not isinstance(item, str) for item in obj["missing_evidence"]
    ):
        return False, "missing_evidence_type"
    if not isinstance(obj["audit_recommendation"], str) or obj["audit_recommendation"] not in {
        "CHECK_DENOMINATOR", "REQUEST_MORE_DATA", "NO_ACTION"
    }:
        return False, "audit_recommendation_type_or_enum"
    return True, "valid"


def gpu_name_ok(value):
    return "RTX 3080" in value


def main():
    errors = []
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    expected_sources = json.loads((HERE / "SOURCE_HASHES.json").read_text(encoding="utf-8"))
    if sha256(HERE / "SOURCE_HASHES.json") != freeze.get("source_manifest_sha256"):
        errors.append("source_manifest_hash_mismatch")
    actual_sources = {name: sha256(HERE / name) for name in expected_sources}
    if actual_sources != expected_sources:
        errors.append("source_hash_mismatch")
    frozen_files = [".gitattributes", "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/FREEZE.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/SOURCE_HASHES.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/INPUT.json",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/protocol.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/test_protocol.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/preflight.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/generate_one.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/audit.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/test_audit_contract.py",
                    "research/experiments/strategic_reporting_5322_gpu_v9/strict_json_prompt_6048/RUNBOOK.md"]
    try:
        subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *frozen_files],
                       cwd=ROOT, check=True, timeout=5)
        subprocess.run(["git", "ls-files", "--error-unmatch", *frozen_files],
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL, timeout=5)
    except Exception:
        errors.append("frozen_source_not_committed_or_worktree_dirty")
    input_bytes = (HERE / "INPUT.json").read_bytes()
    input_data = json.loads(input_bytes.decode("utf-8"))
    if hashlib.sha256(input_bytes).hexdigest() != freeze["input_sha256"]:
        errors.append("input_hash_mismatch")
    if input_data != generate_frozen_input(freeze["data_seed"]):
        errors.append("input_seed_reconstruction_mismatch")
    preflight_path = OUTDIR / "PREFLIGHT.json"
    if not preflight_path.is_file():
        errors.append("missing_preflight")
        preflight = {}
    else:
        preflight_bytes = preflight_path.read_bytes()
        preflight = json.loads(preflight_bytes.decode("utf-8"))
        if not preflight.get("load_authorized") or preflight.get("errors"):
            errors.append("preflight_not_pass")
        if preflight.get("model_sha256") != freeze["model_sha256"]:
            errors.append("preflight_model_hash_mismatch")
        if preflight.get("tokenizer_manifest_sha256") != freeze["tokenizer_manifest_sha256"]:
            errors.append("tokenizer_hash_mismatch")
        if preflight.get("tokenizer_file_hashes") != freeze.get("tokenizer_file_hashes"):
            errors.append("tokenizer_file_inventory_mismatch")
        model_file = Path(preflight.get("model_path", "")) / freeze["model_file"]
        if not model_file.is_file() or sha256(model_file) != freeze["model_sha256"]:
            errors.append("independent_model_weight_hash_mismatch")
    candidate_path = OUTDIR / "candidate.json"
    if not candidate_path.is_file():
        errors.append("missing_candidate_record")
        candidate = {}
    else:
        candidate_bytes = candidate_path.read_bytes()
        candidate = json.loads(candidate_bytes.decode("utf-8"))
        if candidate.get("allocation_id") != freeze["allocation_id"]:
            errors.append("allocation_id_mismatch")
        if candidate.get("main_sha") != freeze["main_sha_at_run"]:
            errors.append("main_sha_mismatch")
        if candidate.get("model_sha256") != freeze["model_sha256"]:
            errors.append("candidate_model_hash_mismatch")
        if candidate.get("input_sha256") != freeze["input_sha256"]:
            errors.append("candidate_input_hash_mismatch")
        if not preflight_path.is_file() or candidate.get("preflight_sha256") != sha256(preflight_path):
            errors.append("candidate_preflight_hash_mismatch")
        if candidate.get("prompt") != expected_prompt(input_data):
            errors.append("prompt_freeze_mismatch")
        if candidate.get("prompt_sha256") != hashlib.sha256(
            expected_prompt(input_data).encode("utf-8")
        ).hexdigest():
            errors.append("prompt_hash_mismatch")
        raw = candidate.get("raw_text", "")
        raw_digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        if candidate.get("raw_text_sha256") != raw_digest:
            errors.append("raw_text_hash_mismatch")
        if candidate.get("model_call_count") != 1 or candidate.get("retry_count") != 0:
            errors.append("call_or_retry_count_mismatch")
        if candidate.get("exit_code") != 0:
            errors.append("candidate_exit_not_zero")
        if candidate.get("model_device") != "cuda:0" or candidate.get("input_device") != "cuda:0":
            errors.append("cuda_device_mismatch")
        if candidate.get("cuda_allocated_after_bytes", 0) <= 0 or candidate.get(
            "cuda_peak_allocated_bytes", 0
        ) <= 0:
            errors.append("zero_cuda_allocation")
        if candidate.get("generation_elapsed_ns", 0) <= 0:
            errors.append("missing_generation_timing")
        for field in ("nvidia_smi_before_model_load", "nvidia_smi_before_generate",
                      "nvidia_smi_after_generate"):
            if not gpu_name_ok(candidate.get(field, "")):
                errors.append("missing_rtx3080_evidence:" + field)
        start = datetime.fromisoformat(freeze["window_start_utc"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(freeze["window_end_utc"].replace("Z", "+00:00"))
        try:
            candidate_started = datetime.fromisoformat(candidate["started_utc"])
            if not start <= candidate_started <= end:
                errors.append("candidate_outside_reserved_window")
        except Exception:
            errors.append("candidate_start_time_invalid")
        valid, reason = validate_output(raw)
        if candidate.get("schema_valid") != valid or candidate.get("schema_reason") != reason:
            errors.append("candidate_schema_claim_mismatch")
    output_pass = candidate.get("status") == "PASS_ONE_CALL_OUTPUT_CONTRACT" and not errors
    report = {
        "status": "AUDIT_PASS_SCOPED_OUTPUT_PASS" if output_pass else
                  ("AUDIT_PASS_SCOPED_OUTPUT_FAIL" if not errors else "AUDIT_FAIL"),
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "allocation_id": freeze["allocation_id"],
        "main_sha": freeze.get("main_sha_at_run"),
        "independent_auditor_sha256": sha256(Path(__file__).resolve()),
        "candidate_blob_sha256": hashlib.sha256(candidate_path.read_bytes()).hexdigest()
        if candidate_path.is_file() else None,
        "raw_output_valid": candidate.get("schema_valid"),
        "raw_output_reason": candidate.get("schema_reason"),
        "errors": errors,
        "retry_count": 0,
        "scope": "one prompt-only synthetic output; not general reliability or semantic quality",
    }
    out = OUTDIR / "INDEPENDENT_AUDIT.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
