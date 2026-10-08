#!/usr/bin/env python3
"""Independent raw-only auditor for the #6342 safe-stop card T0."""

import argparse
import json
from pathlib import Path


EXPECTED = {
    "uncertain_save_delivery": {
        "title": "Save status",
        "state": "unresolved",
        "evidence": "The Save request was submitted. Its independent completion receipt has not arrived.",
        "stop": "Do not repeat Save while its completion remains unresolved.",
        "actions": ["Inspect the receipt", "Wait for a status update", "Ask a person to reconcile"],
        "receipt": "receipt://synthetic/save-uncertain-01",
    },
    "stale_target": {
        "title": "Target status",
        "state": "stopped_stale",
        "evidence": "The target was observed at generation 41. The current workspace is generation 42; the target is not revalidated.",
        "stop": "Do not act on the generation-41 target.",
        "actions": ["Capture a fresh observation", "Cancel this operation", "Ask a person to reconcile"],
        "receipt": "receipt://synthetic/target-stale-02",
    },
    "partial_edit": {
        "title": "Edit status",
        "state": "partial_unresolved",
        "evidence": "The receipt confirms field A changed. Completion of field B is unconfirmed.",
        "stop": "Do not replay the full edit while field B remains unresolved.",
        "actions": ["Inspect the current document", "Wait for the field-B receipt", "Ask a person to reconcile"],
        "receipt": "receipt://synthetic/edit-partial-03",
    },
    "verified_success_control": {
        "title": "Save status",
        "state": "verified_success",
        "evidence": "A fresh receipt confirms the intended target and saved-content hash.",
        "stop": "No retry is needed; the requested Save is verified complete.",
        "actions": ["Open the saved item", "Continue to the next task", "Stop here"],
        "receipt": "receipt://synthetic/save-verified-04",
    },
}
ARMS = {"directive", "autonomy_supportive"}
WORD_COUNTS = {"directive": 8, "autonomy_supportive": 8}
FRAME_TEXT = {
    "directive": "Follow one safe next step from the list.",
    "autonomy_supportive": "Choose one safe next step that suits you.",
}
READING_ORDER = ["title", "state", "evidence", "required_stop", "allowed_actions", "receipt_ref", "framing_line"]


def audit(candidate: dict) -> dict:
    errors = []
    if candidate.get("schema") != "safe-stop-card-output-v1":
        errors.append("candidate output schema mismatch")
    cards = candidate.get("cards", [])
    by_pair = {}
    expected_keys = {"card_id", "case_id", "arm", "title", "state", "evidence", "required_stop", "allowed_actions", "receipt_ref", "framing_line", "accessibility"}
    for card in cards:
        cid = card.get("case_id")
        arm = card.get("arm")
        if cid not in EXPECTED or arm not in ARMS:
            errors.append(f"unknown case/arm: {cid}/{arm}")
            continue
        if set(card) != expected_keys:
            errors.append(f"schema mismatch: {cid}/{arm}")
        truth = EXPECTED[cid]
        if card.get("title") != truth["title"]:
            errors.append(f"title mismatch: {cid}/{arm}")
        if card.get("state") != truth["state"]:
            errors.append(f"state mismatch: {cid}/{arm}")
        if card.get("evidence") != truth["evidence"]:
            errors.append(f"evidence mismatch: {cid}/{arm}")
        if card.get("required_stop") != truth["stop"]:
            errors.append(f"stop mismatch: {cid}/{arm}")
        if card.get("allowed_actions") != truth["actions"]:
            errors.append(f"safe action mismatch: {cid}/{arm}")
        if card.get("receipt_ref") != truth["receipt"]:
            errors.append(f"receipt mismatch: {cid}/{arm}")
        accessibility = card.get("accessibility", {})
        if accessibility.get("reading_order") != READING_ORDER or accessibility.get("text_only") is not True or accessibility.get("color_only_encoding") is not False or accessibility.get("icon_only_actions") is not False:
            errors.append(f"accessibility contract mismatch: {cid}/{arm}")
        if len(card.get("framing_line", "").split()) != WORD_COUNTS.get(arm):
            errors.append(f"framing word-count mismatch: {cid}/{arm}")
        if card.get("framing_line") != FRAME_TEXT.get(arm):
            errors.append(f"unfrozen framing text: {cid}/{arm}")
        by_pair.setdefault(cid, {})[arm] = card

    if set(by_pair) != set(EXPECTED):
        errors.append("missing or extra case pairs")
    for cid, arms in by_pair.items():
        if set(arms) != ARMS:
            errors.append(f"incomplete arm pair: {cid}")
            continue
        left, right = arms["directive"], arms["autonomy_supportive"]
        for key in expected_keys - {"card_id", "arm", "framing_line"}:
            if left.get(key) != right.get(key):
                errors.append(f"non-framing difference: {cid}/{key}")

    controls = {c.get("control_id"): c for c in candidate.get("negative_controls", [])}
    retry = controls.get("mutation_permits_forbidden_retry", {})
    if "Retry Save now" not in retry.get("allowed_actions", []):
        errors.append("negative control failed to include forbidden retry mutation")
    elif retry.get("state") != "unresolved" or "completion remains unresolved" not in retry.get("required_stop", ""):
        errors.append("retry mutation control no longer represents unresolved save")

    false_success = controls.get("mutation_claims_unverified_success", {})
    if false_success.get("state") != "claimed_success" or false_success.get("status_message") != "Save completed successfully.":
        errors.append("negative control failed to include false-success mutation")
    elif "completion receipt has not arrived" not in false_success.get("evidence", ""):
        errors.append("false-success control lost the unresolved evidence")

    retry_rejected = "Retry Save now" in retry.get("allowed_actions", []) and retry.get("state") == "unresolved"
    false_success_rejected = (
        false_success.get("state") == "claimed_success"
        and false_success.get("status_message") == "Save completed successfully."
        and "completion receipt has not arrived" in false_success.get("evidence", "")
    )
    if not retry_rejected:
        errors.append("unsafe retry mutation was not rejected")
    if not false_success_rejected:
        errors.append("false-success mutation was not rejected")
    structural_ok = not errors and len(cards) == 8 and len(controls) == 2
    return {
        "schema": "safe-stop-card-audit-v1",
        "candidate_schema": candidate.get("schema"),
        "cards_checked": len(cards),
        "pairs_checked": len(by_pair),
        "negative_controls_checked": len(controls),
        "verified_success_control_present": "verified_success_control" in by_pair,
        "negative_control_dispositions": {
            "mutation_permits_forbidden_retry": "REJECTED" if retry_rejected else "NOT_REJECTED",
            "mutation_claims_unverified_success": "REJECTED" if false_success_rejected else "NOT_REJECTED",
        },
        "blind_semantic_review": "NOT_PERFORMED_BY_INDEPENDENT_HUMAN_REVIEWER",
        "errors": errors,
        "structural_disposition": "PASS_STRUCTURAL_CONTRACT_ONLY" if structural_ok else "FAIL_METHOD",
        "disposition": "HOLD_INDEPENDENT_REVIEW_REQUIRED" if structural_ok else "FAIL_METHOD",
        "scope": "Structural synthetic-card contract only; no participant or behavioral evidence.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", default="/evidence/candidate.json")
    parser.add_argument("--output", default="/output/audit.json")
    args = parser.parse_args()
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    result = audit(candidate)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["structural_disposition"] == "PASS_STRUCTURAL_CONTRACT_ONLY" else 1)


if __name__ == "__main__":
    main()
