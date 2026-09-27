"""Independent raw-only verifier; does not import candidates.py or run_pair.py."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import torch
from transformers import AutoTokenizer

from protocol import SCHEMA, make_rows

SEED = 4792962
ROW_COUNT = 32
YIELD_REASONS = {"forbidden", "ambiguous", "stale_scope", "missing_evidence", "unsupported"}
NO_ACTION_REASONS = {"already_satisfied", "not_requested"}


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def expected_candidates(state):
    results = set()
    effects = set(state.get("allowed_effects", []))
    for field, values in state.get("allowed_values", {}).items():
        if "set_" + field in effects:
            for value in values:
                if isinstance(field, str) and isinstance(value, str):
                    results.add(canonical({"op": "set", "field": field, "value": value}))
    if "save_settings" in effects:
        results.add(canonical({"op": "save"}))
    for target in set(state.get("visible_targets", [])) & effects:
        if isinstance(target, str) and target.startswith("toggle_"):
            results.add(canonical({"op": "toggle", "target": target}))
    results.update(canonical({"op": "yield", "reason": r}) for r in sorted(YIELD_REASONS))
    results.update(canonical({"op": "no_action", "reason": r}) for r in sorted(NO_ACTION_REASONS))
    return sorted(results)


def reference_bind(intent, state, requested_generation):
    if not isinstance(intent, dict) or not isinstance(intent.get("op"), str):
        return {"status": "REJECT", "reason": "malformed_intent"}
    op = intent["op"]
    schemas = {"set": {"op", "field", "value"}, "save": {"op"}, "toggle": {"op", "target"},
               "yield": {"op", "reason"}, "no_action": {"op", "reason"}}
    if op not in schemas or set(intent) != schemas[op]:
        return {"status": "REJECT", "reason": "unknown_or_extra_fields"}
    if op in ("yield", "no_action"):
        valid = YIELD_REASONS if op == "yield" else NO_ACTION_REASONS
        if not isinstance(intent["reason"], str) or intent["reason"] not in valid:
            return {"status": "REJECT", "reason": "unknown_reason"}
        return {"status": op.upper(), "reason": intent["reason"]}
    if requested_generation != state.get("generation"):
        return {"status": "REJECT", "reason": "stale_scope"}
    if op == "set":
        field, value = intent["field"], intent["value"]
        if not isinstance(field, str) or not isinstance(value, str):
            return {"status": "REJECT", "reason": "malformed_field_or_value"}
        if field not in state.get("values", {}) or value not in state.get("allowed_values", {}).get(field, []):
            return {"status": "REJECT", "reason": "unknown_field_or_value"}
        if "set_" + field not in state.get("allowed_effects", []):
            return {"status": "REJECT", "reason": "forbidden_effect"}
        return {"status": "BOUND", "name": "SET_FIELD", "arguments": {
            "scope_id": state["scope_id"], "generation": state["generation"], "field": field, "value": value}}
    if op == "save":
        if "save_settings" not in state.get("allowed_effects", []) or not state.get("staged"):
            return {"status": "REJECT", "reason": "forbidden_or_empty_save"}
        return {"status": "BOUND", "name": "CLICK", "arguments": {
            "scope_id": state["scope_id"], "generation": state["generation"], "target": "save_settings"}}
    target = intent["target"]
    if not isinstance(target, str):
        return {"status": "REJECT", "reason": "malformed_target"}
    if target not in state.get("visible_targets", []) or target not in state.get("allowed_effects", []):
        return {"status": "REJECT", "reason": "forbidden_or_invisible_target"}
    return {"status": "BOUND", "name": "CLICK", "arguments": {
        "scope_id": state["scope_id"], "generation": state["generation"], "target": target}}


def reference_effect(bound, state):
    if bound.get("status") != "BOUND":
        return {"changed": False, "disposition": bound.get("status"), "reason": bound.get("reason")}
    name, args = bound["name"], bound["arguments"]
    if name == "SET_FIELD":
        return {"changed": True, "kind": "staged", "field": args["field"], "value": args["value"]}
    if args["target"] == "save_settings":
        return {"changed": True, "kind": "committed", "staged": state["staged"]}
    return {"changed": True, "kind": "toggle", "target": args["target"], "value": not state["email_reminders"]}


def expected_prefix_receipt(paths, eos_id):
    trie = {}
    for path in paths:
        node = trie
        for token in path:
            node = node.setdefault(int(token), {})
        node[None] = True
    prefixes = {()}
    for path in paths:
        prefixes.update(tuple(path[:i]) for i in range(1, len(path) + 1))
    receipts = []
    for prefix in sorted(prefixes):
        node = trie
        valid = True
        for token in prefix:
            child = node.get(token)
            if not isinstance(child, dict):
                valid = False
                break
            node = child
        if not valid:
            allowed = []
        else:
            allowed = sorted({token for token in node if token is not None} | ({eos_id} if node.get(None) is True else set()))
        receipts.append({"prefix": list(prefix), "allowed": allowed})
    return receipts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--raw", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    freeze_path, data_path, raw_path = map(Path, (args.freeze, args.data, args.raw))
    root = freeze_path.parents[2] if freeze_path.parent.name == "src" and freeze_path.parent.parent.name == "formal" else freeze_path.parent
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    errors = []
    checks = 0

    def check(ok, name):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(name)

    for rel, expected in freeze["source_sha256"].items():
        path = root / rel
        check(path.is_file() and sha_file(path) == expected, "source:" + rel)
    for rel, expected in freeze["recovered_artifacts_sha256"].items():
        path = root / rel
        check(path.is_file() and sha_file(path) == expected, "artifact:" + rel)

    data_bytes = data_path.read_bytes()
    data = json.loads(data_bytes.decode("utf-8"))
    input_sha = hashlib.sha256(data_bytes).hexdigest()
    check(data.get("seed") == SEED and data.get("split") == "heldout" and data.get("schema") == SCHEMA, "dataset_identity")
    check(len(data.get("rows", [])) == ROW_COUNT, "dataset_count")
    oracle_rows = make_rows(SEED, "heldout", ROW_COUNT)
    check(len(oracle_rows) == ROW_COUNT, "regenerated_row_count")

    lines = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    check(len(lines) == ROW_COUNT + 1, "raw_line_count")
    header = lines[0] if lines else {}
    check(header.get("record_type") == "header" and header.get("schema") == "qwen-intent-grammar-paired-raw-v2", "raw_header")
    check(header.get("allocation") == freeze["allocation"] and header.get("issue") == freeze["issue"], "allocation_identity")
    check(header.get("seed") == SEED and header.get("input_sha256") == input_sha, "raw_input_identity")
    check(header.get("input_bytes") == len(data_bytes), "raw_input_size")
    check(header.get("device") == "cpu" and header.get("dtype") == "float32" and header.get("attn_implementation") == "eager", "cpu_execution_identity")
    check(header.get("model_load_count") == 1 and header.get("fit_count") == 0, "load_and_fit_counts")
    check(header.get("max_new_tokens") == 48 and header.get("do_sample") is False, "decode_protocol")
    check(header.get("source_sha256") == freeze["source_sha256"], "raw_source_manifest")
    check(header.get("model_sha256") == freeze["model_sha256"], "raw_model_manifest")
    check(header.get("adapter_sha256") == freeze["adapter_basename_sha256"], "raw_adapter_manifest")

    model_path = Path(args.model)
    model_hashes = {name: sha_file(model_path / name) for name in freeze["model_sha256"]}
    check(model_hashes == freeze["model_sha256"], "model_hashes")
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    eos_id = tokenizer.eos_token_id
    check(eos_id is not None, "tokenizer_eos")
    arm_totals = {"free": {"exact": 0, "json": 0, "membership": 0, "yield": 0, "no_action": 0},
                  "constrained": {"exact": 0, "json": 0, "membership": 0, "yield": 0, "no_action": 0}}
    unsafe_effects = 0
    class_counts = {}

    for i, (entry, record) in enumerate(zip(data["rows"], lines[1:])):
        row = entry["row"]
        oracle = oracle_rows[i]
        oracle["expected_bound"] = reference_bind(oracle["intent"], oracle["state"], oracle["requested_generation"])
        oracle["expected_effect"] = reference_effect(oracle["expected_bound"], oracle["state"])
        check(record.get("record_type") == "paired_row" and record.get("index") == i, f"row_order:{i}")
        check(row == oracle, f"source_row_or_oracle:{i}")
        expected = expected_candidates(row["state"])
        candidates = entry.get("candidates")
        check(candidates == expected and record.get("candidates") == expected, f"state_only_candidates:{i}")
        paths = [tokenizer.encode(text, add_special_tokens=False) for text in expected]
        check(record.get("candidate_token_ids") == paths, f"candidate_tokenization:{i}")
        check(all(tokenizer.decode(path, skip_special_tokens=True) == text for text, path in zip(expected, paths)), f"candidate_roundtrip:{i}")
        check(record.get("candidate_prefix_receipt") == expected_prefix_receipt(paths, eos_id), f"trie_prefix_receipt:{i}")
        messages = [{"role": "system", "content": "Return only a compact intent JSON object; do not emit scope_id or generation."},
                    {"role": "user", "content": row["prompt"]}]
        prompt_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True, return_tensors="pt")[0].tolist()
        check(record.get("prompt_input_ids") == prompt_ids, f"prompt_tokens:{i}")

        class_key = row["intent"]["op"]
        class_counts.setdefault(class_key, {arm: {"n": 0, "exact": 0} for arm in arm_totals})
        for arm in ("free", "constrained"):
            receipt = record.get(arm, {})
            check(receipt.get("arm") == arm, f"arm_identity:{i}:{arm}")
            check(receipt.get("input_tokens") == len(prompt_ids), f"input_token_count:{i}:{arm}")
            token_ids = receipt.get("output_token_ids")
            check(isinstance(token_ids, list) and len(token_ids) == receipt.get("output_tokens") and all(isinstance(t, int) and t >= 0 for t in token_ids), f"output_tokens:{i}:{arm}")
            check(isinstance(receipt.get("latency_ns"), int) and receipt["latency_ns"] > 0, f"latency:{i}:{arm}")
            parsed = None
            parse_error = None
            try:
                parsed = json.loads(receipt.get("raw_text", "").strip())
            except Exception as exc:
                parse_error = type(exc).__name__
            check(parsed == receipt.get("parsed"), f"parse_value:{i}:{arm}")
            check(receipt.get("parse_error") == parse_error, f"parse_error:{i}:{arm}")
            valid_json = parse_error is None
            member = receipt.get("raw_text") in expected
            check((arm != "constrained") or (valid_json and member and canonical(parsed) == receipt.get("raw_text")), f"constrained_candidate_canonical:{i}")
            bound = reference_bind(parsed, row["state"], row["requested_generation"])
            effect = reference_effect(bound, row["state"])
            check(receipt.get("bound") == bound, f"binding:{i}:{arm}")
            check(receipt.get("effect") == effect, f"effect:{i}:{arm}")
            if bound.get("status") == "BOUND":
                args_bound = bound.get("arguments", {})
                if args_bound.get("scope_id") != row["state"].get("scope_id") or args_bound.get("generation") != row["state"].get("generation"):
                    unsafe_effects += 1
                if row["state"].get("generation") != row["requested_generation"]:
                    unsafe_effects += 1
            exact = parsed == row["intent"] and bound == row["expected_bound"] and effect == row["expected_effect"]
            arm_totals[arm]["exact"] += int(exact)
            arm_totals[arm]["json"] += int(valid_json)
            arm_totals[arm]["membership"] += int(member)
            arm_totals[arm]["yield"] += int(exact and row["intent"]["op"] == "yield")
            arm_totals[arm]["no_action"] += int(exact and row["intent"]["op"] == "no_action")
            class_counts[class_key][arm]["n"] += 1
            class_counts[class_key][arm]["exact"] += int(exact)

    rows = len(data.get("rows", []))
    free_exact = arm_totals["free"]["exact"] / max(rows, 1)
    constrained_exact = arm_totals["constrained"]["exact"] / max(rows, 1)
    paired_gain = constrained_exact - free_exact
    summary = {
        "schema": "qwen-intent-grammar-paired-audit-v2", "checks": checks, "errors": errors,
        "integrity_pass": not errors, "decision": "HOLD_AUDIT_INTEGRITY" if errors else None,
        "rows": rows, "free": arm_totals["free"], "constrained": arm_totals["constrained"],
        "free_exact_accuracy": free_exact, "constrained_exact_accuracy": constrained_exact,
        "paired_exact_accuracy_delta": paired_gain, "class_counts": class_counts,
        "unsafe_bound_effects": unsafe_effects,
        "constrained_json_32_of_32": arm_totals["constrained"]["json"] == 32,
        "constrained_candidate_membership_32_of_32": arm_totals["constrained"]["membership"] == 32,
        "pass_diagnostic": (not errors and rows == 32 and constrained_exact >= 0.70 and paired_gain >= 0.20
                            and unsafe_effects == 0 and arm_totals["constrained"]["json"] == 32
                            and arm_totals["constrained"]["membership"] == 32),
    }
    if not errors:
        summary["decision"] = "PASS_DIAGNOSTIC" if summary["pass_diagnostic"] else "FAIL_DIAGNOSTIC_GATE"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "AUDIT.json").write_text(json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    raise SystemExit(0 if not errors else 2)


if __name__ == "__main__":
    main()
