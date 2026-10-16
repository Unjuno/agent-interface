"""Independently reduce retained scorer history; never execute producer code.

This is a post-hoc saved-file auditor for one pinned synthetic fixture. Accepted
and gap metadata come from a statically parsed, byte-pinned fixture source;
they were not separately recorded as runtime observations in followup_raw.json.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_HEAD = "c87812a4a2d41f65127bb3a72fdceea390f63dc7"
POSITIVE = "ADMISSION_BRACKETED_PROGRESS"
REJECTED = "POST_CANCELLATION_COOCCURRENCE"
PINS = {
    "followup_raw.json": ("fcc04774cb1f892f3190c10944bf60e82190cf08", "2533079effb83bf83f32e54ee573a02679481d24df62afa29d26b3000078f827"),
    "followup_run.py": ("34ff7c21754be2cd81e122e94e28e10661c07a93", "ab61b298fc6028c06afb5339b93569c529785715ea109b05429b8aed7a569b5f"),
    "FOLLOWUP.json": ("b671d50b35b08808d80a389f369bf638b064df5c", "c0f994ae541103b3c9fa425a8c362ea1109f5dd53f11b67b41c8572e5858b09a"),
    "candidate.py": ("2f032bd5c06160193df3b34ab1bf3741e79b400f", "23727e925c3e27a171592b0a831ab29572647bc0309cb6f10b8d81c8104aa049"),
    "../scorer_admission_attribution_t0_v1/candidate.py": ("3a097172115b6d8c2cd482c37c80388b86404b25", "fecf7be7abe7a36111ec2df171461eb225d5c951b37c8d979d0a2ce2d0e7f4b9"),
    "followup_audit.py": ("306985ffb2ce00de8d0de622e41d8726b009dda6", "d1792b471344f70ade1117ab8fb24d920a187754a1090bd783607623a2cf1e83"),
}


def _reject(reason, **details):
    return {"decision": REJECTED, "reason": reason, **details}


def recompute_history(history, accepted_ns, first_input_ns, *, max_gap_ns,
                      missed_periods=0, baseline_rule="latest"):
    """Reduce a counter history without consulting any expected/observed label.

    earliest exists only to reconstruct the preserved prior policy's defect.
    latest is the corrected policy. This reducer does not authenticate runtime
    clocks, source epochs, actual game events, physical input or causation.
    """
    if (type(accepted_ns) is not int or type(first_input_ns) is not int
            or accepted_ns >= first_input_ns):
        return _reject("invalid_admission_bracket")
    if type(max_gap_ns) is not int or max_gap_ns <= 0:
        return _reject("invalid_max_gap")
    if type(missed_periods) is not int or missed_periods < 0:
        return _reject("invalid_missed_periods")
    if baseline_rule not in ("latest", "earliest"):
        return _reject("invalid_baseline_rule")
    if not isinstance(history, list) or not history:
        return _reject("invalid_history")
    for row in history:
        if (not isinstance(row, (list, tuple)) or len(row) != 2
                or type(row[0]) is not int or type(row[1]) is not int or row[1] < 0):
            return _reject("invalid_sample")
    if any(right[0] <= left[0] for left, right in zip(history, history[1:])):
        return _reject("sample_clock_not_strictly_increasing")
    baselines = [list(row) for row in history if accepted_ns < row[0] < first_input_ns]
    if not baselines:
        return _reject("no_post_acceptance_pre_input_baseline")
    baseline = baselines[-1] if baseline_rule == "latest" else baselines[0]
    deltas = [[ns, score - baseline[1]] for ns, score in history if ns > first_input_ns]
    details = {"baseline": baseline, "post_input_deltas": deltas}
    if missed_periods:
        return _reject("missed_scorer_period", **details)
    for ns, score in history:
        if ns <= first_input_ns:
            continue
        gap = ns - baseline[0]
        if gap > max_gap_ns:
            return _reject("positive_sample_gap_exceeded", **details)
        if score > baseline[1]:
            return {"decision": POSITIVE, "reason": "bounded_post_input_counter_increase",
                    "positive_sample": [ns, score], "gap_ns": gap, **details}
    return _reject("no_bounded_post_input_progress", **details)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key:" + key)
        result[key] = value
    return result


def _read_json(data):
    def invalid_constant(value):
        raise ValueError("nonfinite_json:" + value)
    return json.loads(data, object_pairs_hook=_unique_object, parse_constant=invalid_constant)


def fixture_metadata(source):
    """Read literal fixture arguments through AST; no import, eval or exec."""
    tree = ast.parse(source)
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    assignments = {target.id: node.value for node in main.body if isinstance(node, ast.Assign)
                   for target in node.targets if isinstance(target, ast.Name)}
    pairs = [list(row) for row in ast.literal_eval(assignments["sample_pairs"])]
    events = ast.literal_eval(assignments["events"])
    successor = assignments["successor_result"]
    prior = assignments["prior_result"]
    if not isinstance(successor, ast.Call) or not isinstance(prior, ast.Call):
        raise ValueError("fixture_call_shape")
    intent_id = ast.literal_eval(successor.args[2])
    acceptance = [row for row in events if row.get("event") == "accepted" and row.get("id") == intent_id]
    admissions = [row for row in events if row.get("event") == "input_admission" and row.get("id") == intent_id]
    if len(acceptance) != 1 or not admissions:
        raise ValueError("fixture_identity")
    accepted = acceptance[0]["accepted_ns"]
    first_input = min(row["admitted_ns"] for row in admissions)
    successor_gap = next(ast.literal_eval(kw.value) for kw in successor.keywords if kw.arg == "max_gap_ns")
    prior_gap = next(ast.literal_eval(kw.value) for kw in prior.keywords if kw.arg == "max_gap_ns")
    if (ast.literal_eval(prior.args[1]), ast.literal_eval(prior.args[2]), prior_gap) != (accepted, first_input, successor_gap):
        raise ValueError("prior_successor_fixture_disagreement")
    sample = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "sample")
    returned = next(node.value for node in sample.body if isinstance(node, ast.Return))
    fields = {ast.literal_eval(key): value for key, value in zip(returned.keys, returned.values)}
    missed = ast.literal_eval(fields["missed_periods_before"])
    payload = fields["payload"]
    payload_fields = {ast.literal_eval(key): value for key, value in zip(payload.keys, payload.values)}
    if ast.literal_eval(payload_fields["map_exit"]) is not False:
        raise ValueError("fixture_not_counter_only")
    return {"accepted_ns": accepted, "first_input_ns": first_input, "max_gap_ns": successor_gap,
            "missed_periods": missed, "intent_id": intent_id, "sample_history": pairs,
            "provenance": "static literals in byte-pinned followup_run.py; not new runtime observations"}


def audit(root=None):
    root = Path(ROOT if root is None else root)
    errors = []
    result = {"schema": "scorer-eventlog-saved-history-audit-v2", "source_head": SOURCE_HEAD,
              "pass": False, "errors": errors,
              "scope": "post-hoc one-fixture saved-history plus pinned-source-metadata audit; no producer execution",
              "seven_case_raw_audit_repaired": False, "runtime_or_causal_claim": False}
    try:
        data = {}
        identities = {}
        for name, (git_blob, sha256) in PINS.items():
            content = (root / name).read_bytes()
            actual_blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
            actual_sha = hashlib.sha256(content).hexdigest()
            identities[name] = {"git_blob": actual_blob, "sha256": actual_sha}
            if actual_blob != git_blob or actual_sha != sha256:
                errors.append("input_identity:" + name)
            data[name] = content
        result["inputs"] = identities
        # Never interpret changed fixture code as authority for the saved record.
        if errors:
            return result
        raw = _read_json(data["followup_raw.json"])
        freeze = _read_json(data["FOLLOWUP.json"])
        metadata = fixture_metadata(data["followup_run.py"])
        result["fixture_metadata"] = metadata
        if raw.get("schema") != "scorer-eventlog-prior-policy-regression-raw-v1":
            errors.append("raw_schema")
        if raw.get("sample_history") != metadata["sample_history"]:
            errors.append("fixture_history_disagreement")
        if raw.get("first_input_ns") != metadata["first_input_ns"]:
            errors.append("fixture_first_input_disagreement")
        if raw.get("causal_attribution") is not False or raw.get("candidate_started_in_container") is not False:
            errors.append("scope")
        for field in ("base_main", "prior_candidate_git_blob", "prior_candidate_sha256", "successor_candidate_sha256"):
            if raw.get(field) != freeze.get(field):
                errors.append("freeze_join:" + field)
        for prefix, path in (("prior", "../scorer_admission_attribution_t0_v1/candidate.py"), ("successor", "candidate.py")):
            if raw.get(prefix + "_candidate_sha256") != identities[path]["sha256"]:
                errors.append("source_identity:" + prefix)
        if raw.get("prior_candidate_git_blob") != identities["../scorer_admission_attribution_t0_v1/candidate.py"]["git_blob"]:
            errors.append("prior_blob_identity")
        args = (raw.get("sample_history"), metadata["accepted_ns"], metadata["first_input_ns"])
        kwargs = {"max_gap_ns": metadata["max_gap_ns"], "missed_periods": metadata["missed_periods"]}
        prior = recompute_history(*args, **kwargs, baseline_rule="earliest")
        successor = recompute_history(*args, **kwargs)
        result["derived"] = {
            "prior_baseline": prior.get("baseline"), "prior_decision": prior["decision"],
            "prior_positive_sample": prior.get("positive_sample"),
            "successor_baseline": successor.get("baseline"), "successor_decision": successor["decision"],
            "successor_reason": successor["reason"], "post_input_deltas": successor.get("post_input_deltas", []),
        }
        comparisons = {"prior_decision": prior["decision"],
                       "prior_baseline_ns": prior.get("baseline", [None])[0],
                       "successor_decision": successor["decision"], "successor_reason": successor["reason"]}
        for field, derived in comparisons.items():
            if raw.get(field) != derived:
                errors.append("derived_mismatch:" + field)
        history = raw["sample_history"]
        pre_input_increases = [right[0] for left, right in zip(history, history[1:])
                               if right[0] < metadata["first_input_ns"] and right[1] > left[1]]
        claimed_pre_input = raw.get("pre_input_progress_observed_ns")
        if claimed_pre_input not in pre_input_increases:
            errors.append("pre_input_progress_not_in_history")
        claimed_post_input = raw.get("unchanged_post_input_sample_ns")
        if [claimed_post_input, 0] not in successor.get("post_input_deltas", []):
            errors.append("unchanged_post_input_not_in_history")
        if prior["decision"] == successor["decision"]:
            errors.append("claimed_policy_difference_not_recomputed")
        result["pass"] = not errors
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, IndexError, AttributeError, StopIteration, SyntaxError) as exc:
        errors.append("audit_input:" + type(exc).__name__ + ":" + str(exc))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
