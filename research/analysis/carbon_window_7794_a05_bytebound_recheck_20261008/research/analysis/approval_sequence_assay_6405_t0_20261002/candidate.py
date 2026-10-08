"""Render a frozen approval-request sequence for three bounded display arms."""
import argparse
import hashlib
import json
from pathlib import Path


FIELDS = ("principal", "target", "recipient", "effect", "scope", "expiry",
          "consequence")
SEMANTIC = ("target", "recipient", "effect", "scope")


def digest(request):
    encoded = json.dumps(request, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def card(request, changed=()):
    return {
        "request_id": request["request_id"],
        "fields": {name: request[name] for name in FIELDS},
        "visible_fields": list(FIELDS),
        "highlighted_fields": list(changed),
        "request_digest": digest(request),
        "decision_controls": ["approve", "deny", "cancel"],
        "consequence": request["consequence"],
        "scope": request["scope"],
        "expiry": request["expiry"],
    }


def render(requests, responses, receipt, attempt_id):
    previous = None
    static_items, changed_items = [], []
    batches = []
    for request in requests:
        delta = [] if previous is None else [
            name for name in SEMANTIC if request[name] != previous[name]]
        static_items.append(card(request))
        changed_items.append(card(request, delta))
        item = card(request)
        if request["consequence"] == "nonconsequential" and batches and batches[-1]["eligible"]:
            batches[-1]["items"].append(item)
        else:
            batches.append({
                "eligible": request["consequence"] == "nonconsequential",
                "items": [item],
                "decision_controls": ["approve", "deny", "cancel"],
            })
        previous = request

    receipt_request = next(row for row in requests
                           if row["request_id"] == receipt["request_id"])
    attempted = next(row for row in requests if row["request_id"] == attempt_id)
    authority = [{
        "receipt_request_id": receipt["request_id"],
        "attempt_request_id": attempt_id,
        "receipt_digest": digest(receipt_request),
        "attempt_digest": digest(attempted),
        "decision": "AUTHORIZED_ONCE" if digest(receipt_request) == digest(attempted)
                    else "REFUSE_DIGEST_MISMATCH",
    }]
    return {
        "schema": "approval-sequence-assay-render-v1",
        "sequence_id": "assay-6405-sequence-01",
        "requests": requests,
        "arms": {
            "static": {"items": static_items},
            "changed_fields": {"items": changed_items},
            "bounded_batch": {"batches": batches},
        },
        "authority_checks": authority,
        "responses": responses,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.input.read_text(encoding="utf-8"))
    result = render(fixture["requests"], fixture["responses"], fixture["receipt"],
                    fixture["receipt_attempt_request_id"])
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
