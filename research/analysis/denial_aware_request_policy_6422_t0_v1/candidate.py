"""Deterministic finite T0 policy comparison; stdlib only."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def effect_key(effect):
    fields = ("task_id", "task_version", "target", "recipient", "resource", "consequence_ids")
    if any(effect.get(k) is None for k in fields):
        return None
    return {k: sorted(effect[k]) if k == "consequence_ids" else effect[k] for k in fields}


def decide(case, fixture, used_tokens):
    base = fixture["base_denial_effect"]
    proposed = dict(base)
    proposed.update(case.get("effect", {}))
    before = effect_key(base)
    after = effect_key(proposed)
    eq = "UNKNOWN" if after is None else ("SAME" if after == before else "DIFFERENT")
    required = fixture["required_principals"]
    if case["action_kind"] == "emergency_release":
        outcome = "ALLOW_SAFETY_RELEASE"
    elif case.get("claimed_required_principals") != required:
        outcome = "HOLD_REQUIRED_PRINCIPAL_MAPPING"
    elif case.get("approval_recipient") not in required:
        outcome = "HOLD_APPROVAL_RECIPIENT_NOT_REQUIRED"
    elif case["prior_outcome"] == "NO_RESPONSE":
        outcome = "ALLOW_BOUNDED_NEUTRAL_FOLLOWUP" if case["prompts_before"] < fixture["prompt_cap"] else "HOLD_PROMPT_CAP"
        eq = "NO_DENIAL"
    elif eq == "UNKNOWN":
        outcome = "HOLD_UNKNOWN_EQUIVALENCE"
    elif eq == "DIFFERENT":
        outcome = "ALLOW_FRESH_APPROVAL_REQUEST"
    elif case["prior_outcome"] == "DEFER_UNTIL":
        condition = case.get("defer_condition", {})
        evidence = case.get("condition_evidence", {})
        verified = (condition.get("source_stated") is True and condition.get("source_principal") in required
                    and evidence.get("condition_id") == condition.get("condition_id")
                    and evidence.get("evidence_type") == condition.get("required_evidence")
                    and evidence.get("verified") is True and evidence.get("independent") is True
                    and evidence.get("signed_by") == condition.get("source_principal"))
        outcome = "ALLOW_CONDITION_SATISFIED_FRESH_REQUEST" if verified else "YIELD_CONDITION_NOT_VERIFIED"
    else:
        reopen = case.get("reopen", {})
        valid = (reopen.get("authenticated") is True and reopen.get("user_initiated") is True
                 and reopen.get("actor") in required and reopen.get("effect_matches_denial") is True)
        token = reopen.get("token")
        if valid and token:
            if token in used_tokens:
                outcome = "YIELD_REOPEN_TOKEN_ALREADY_USED"
            else:
                used_tokens.add(token)
                outcome = "ALLOW_REOPENED_FRESH_REQUEST"
        else:
            outcome = "YIELD_DENIED_EFFECT"
    return eq, outcome, hashlib.sha256(json.dumps(after, sort_keys=True, separators=(",", ":")).encode()).hexdigest() if after is not None else None


def run(fixture):
    rows = []
    used = set()
    for case in fixture["cases"]:
        eq, outcome, digest = decide(case, fixture, used)
        new_id = case["request_id"] not in case["prior_request_ids"]
        rows.extend([
            {"case_id": case["case_id"], "arm": "id_only", "equivalence": eq, "required_principals": fixture["required_principals"], "outcome": "ALLOW_REASK_UNSAFE" if new_id else "HOLD_DUPLICATE_ID", "effect_digest": digest, "request_id": case["request_id"], "approval_authority_granted": False},
            {"case_id": case["case_id"], "arm": "prompt_cap", "equivalence": eq, "required_principals": fixture["required_principals"], "outcome": "ALLOW_PROMPT" if case["prompts_before"] < fixture["prompt_cap"] or case["action_kind"] == "emergency_release" else "HOLD_PROMPT_CAP", "effect_digest": digest, "request_id": case["request_id"], "approval_authority_granted": False},
            {"case_id": case["case_id"], "arm": "ledger", "equivalence": eq, "required_principals": fixture["required_principals"], "outcome": outcome, "effect_digest": digest, "request_id": case["request_id"], "approval_authority_granted": False},
        ])
    return rows


if __name__ == "__main__":
    fixture = json.loads((HERE / "fixture.json").read_text())
    out = Path(sys.argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in run(fixture)))
    print(f"rows={len(run(fixture))} output={out}")
