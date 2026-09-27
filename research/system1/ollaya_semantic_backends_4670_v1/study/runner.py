"""Minimal stdlib-only frozen workload runner for Ollaya /api/decide."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

OPTIONS = {
    "CONTINUE": "All required current evidence is verified and the permitted step may proceed.",
    "WATCH": "The state is safe to observe, but a required condition is not yet met for proceeding.",
    "REPAIR": "A required field or prerequisite is missing or invalid and must be corrected.",
    "YIELD": "Evidence is insufficient, conflicting, stale, or cannot safely support a decision.",
    "REFUND": "The user explicitly requests a refund or money back.",
    "BILLING": "The user reports a billing charge or payment issue.",
    "REPLACE": "The user requests a replacement item.",
    "DAMAGE": "The user reports an item arrived damaged.",
    "LOGIN": "The user needs help signing in.",
    "SECURITY": "The user reports an account access or identity security risk.",
    "DELIVERY": "The user asks about a delayed delivery.",
    "CARRIER": "The user asks for a carrier or tracking investigation.",
    "TUESDAY": "Tuesday delivery.", "MONTHLY": "Monthly billing.",
    "BLUE": "Blue color.", "EMAIL": "Email notifications.",
    "MORNING": "Morning time.", "BASIC": "Basic plan.",
    "NORTH": "North pickup location.", "SMALL": "Small package.",
}
INTENT_LABELS = {k: OPTIONS[k] for k in ("REFUND", "BILLING", "REPLACE", "DAMAGE", "LOGIN", "SECURITY", "DELIVERY", "CARRIER", "TUESDAY", "MONTHLY", "BLUE", "EMAIL", "MORNING", "BASIC", "NORTH", "SMALL")}
WORKFLOW_LABELS = {k: OPTIONS[k] for k in ("CONTINUE", "WATCH", "REPAIR", "YIELD")}


def request_for(model, row):
    is_intent = "options" in row
    criteria = {k: INTENT_LABELS[k] for k in row["options"]} if is_intent else WORKFLOW_LABELS
    intent_prompt = row["intent"] + ". Choose the best matching intent; choose YIELD if the state does not support any choice."
    questions = {"decision": {
        "type": "choice",
        "instructions": intent_prompt if is_intent else row["intent"] + ". Choose only the best supported workflow decision.",
        "criteria": criteria,
    }}
    if row["policy"] == "must-yield":
        questions["evidence_safe"] = {
            "type": "choice",
            "instructions": "Does the provided evidence support a safe, current, unambiguous decision?",
            "criteria": {"SAFE": "Evidence is current, authoritative, sufficient, and non-conflicting.", "UNSAFE": "Evidence is missing, stale, conflicting, or unverified."},
        }
    if row["stratum"] == "repeated-batched-predicates":
        questions.update({
            "has_id": {"type": "noul", "instructions": "Is the id present?"},
            "has_consent": {"type": "noul", "instructions": "Is consent present?"},
            "has_amount": {"type": "noul", "instructions": "Is the amount present?"},
            "has_address": {"type": "noul", "instructions": "Is the address verified?"},
            "status_current": {"type": "noul", "instructions": "Is the status current and non-conflicting?"},
            "source_verified": {"type": "noul", "instructions": "Is the source verified?"},
            "authorized": {"type": "noul", "instructions": "Is authorization present?"},
            "timestamp_current": {"type": "noul", "instructions": "Is the timestamp current?"},
        })
    return {
        "model": model,
        "state": row["state"],
        "questions": questions,
        "keep_alive": "-1",
    }


def main_runner(args, rows):
    warmup_rows = [row for row in rows if row["id"] in args.warmup_id]
    with Path(args.output).open("w", encoding="utf-8", newline="\n") as out:
        for row in (warmup_rows if args.warmup_only else rows):
            payload = request_for(args.model, row)
            raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
            req = urllib.request.Request(args.base_url + "/api/decide", data=raw, headers={"Content-Type": "application/json"})
            start = time.perf_counter_ns()
            status, response, error = None, None, None
            try:
                with urllib.request.urlopen(req, timeout=180) as res:
                    status = res.status
                    response = json.loads(res.read())
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                error = repr(exc)
            wall_ms = (time.perf_counter_ns() - start) / 1e6
            elapsed_ms = wall_ms
            if response and isinstance(response.get("total_duration"), (int, float)):
                elapsed_ms = response["total_duration"] / 1e6
            answer = None
            evidence_safe = None
            predicate_answers = {}
            if response:
                entry = response.get("answers", {}).get("decision", {})
                answer = entry.get("choice") or entry.get("value")
                safe = response.get("answers", {}).get("evidence_safe", {})
                evidence_safe = safe.get("choice")
                predicate_answers = {k: v.get("noul") for k, v in response.get("answers", {}).items() if k not in ("decision", "evidence_safe")}
            record = {"id": row["id"], "stratum": row["stratum"], "model": args.model,
                      "request": payload, "status": status, "response": response,
                      "answer": answer, "evidence_safe": evidence_safe, "predicate_answers": predicate_answers,
                      "elapsed_ms": elapsed_ms, "wall_ms": wall_ms, "error": error,
                      "api_load_ms": (response.get("load_duration", 0) / 1e6) if response else None,
                      "api_eval_ms": (response.get("eval_duration", 0) / 1e6) if response else None,
                      "workload_sha256": hashlib.sha256(Path(args.workload).read_bytes()).hexdigest(),
                      "warmup": row["id"] in args.warmup_id}
            out.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            out.flush()
            print(json.dumps({"id": row["id"], "answer": answer, "status": status, "elapsed_ms": round(elapsed_ms, 2), "warmup": row["id"] in args.warmup_id}), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--warmup-id", action="append", default=[])
    ap.add_argument("--warmup-only", action="store_true")
    ap.add_argument("--workload", default="study/workload.jsonl")
    ap.add_argument("--output", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:11435")
    args = ap.parse_args()
    rows = [json.loads(line) for line in Path(args.workload).read_text(encoding="utf-8").splitlines() if line.strip()]
    main_runner(args, rows)


if __name__ == "__main__":
    main()
