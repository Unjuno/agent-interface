"""Minimal stdlib-only frozen workload runner for Ollaya /api/decide."""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

OPTIONS = {
    "CONTINUE": "All required current evidence is verified and the permitted step may proceed.",
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
CHOICE = {k: OPTIONS[k] for k in OPTIONS}


def request_for(model, row):
    labels = list(CHOICE)
    return {
        "model": model,
        "state": row["state"],
        "questions": {"decision": {
            "type": "choice",
            "instructions": row["intent"] + ". Select the best label; if evidence is insufficient, conflicting, or stale, choose YIELD.",
            "criteria": {label: CHOICE[label] for label in labels},
        }},
        "keep_alive": "0",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--workload", default="study/workload.jsonl")
    ap.add_argument("--output", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:11435")
    args = ap.parse_args()
    rows = [json.loads(line) for line in Path(args.workload).read_text(encoding="utf-8").splitlines() if line.strip()]
    with Path(args.output).open("w", encoding="utf-8", newline="\n") as out:
        for row in rows:
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
            elapsed_ms = (time.perf_counter_ns() - start) / 1e6
            answer = None
            if response:
                entry = response.get("answers", {}).get("decision", {})
                answer = entry.get("choice") or entry.get("value")
            record = {"id": row["id"], "stratum": row["stratum"], "model": args.model,
                      "request": payload, "status": status, "response": response,
                      "answer": answer, "elapsed_ms": elapsed_ms, "error": error}
            out.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            out.flush()
            print(json.dumps({"id": row["id"], "answer": answer, "status": status, "elapsed_ms": round(elapsed_ms, 2)}), flush=True)


if __name__ == "__main__":
    main()
