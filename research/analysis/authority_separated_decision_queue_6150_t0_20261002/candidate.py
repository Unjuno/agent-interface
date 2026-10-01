import json
import sys
from pathlib import Path


def run(fixture):
    events = fixture["events"]
    arrivals = [e for e in events if e["type"] == "arrive"]
    cancels = {(e["id"], e["version"]): e["at"] for e in events if e["type"] == "cancel"}
    rows = {}
    for policy in fixture["policy_names"]:
        clock = 0
        pending = list(arrivals)
        done_release = False
        out = {"policy": policy, "reviews": [], "receipts": [], "expired": [], "cancelled": [], "urgent": [], "effect_attempts": []}
        while pending:
            if not done_release and clock <= fixture["urgent_release"]["at"]:
                u = fixture["urgent_release"]
                out["urgent"].append({"id": u["id"], "start": max(clock, u["at"]), "end": max(clock, u["at"]) + u["duration"], "released": True})
                clock = max(clock, u["at"]) + u["duration"]
                done_release = True
            eligible = [c for c in pending if c["at"] <= clock]
            if not eligible:
                clock = min(c["at"] for c in pending)
                eligible = [c for c in pending if c["at"] <= clock]
            if policy == "BOUNDED_BATCH":
                horizon = clock + fixture["batch_wait"]
                window = [c for c in pending if c["at"] <= horizon]
                clock = max(clock, max(c["at"] for c in window))
                eligible = [c for c in pending if c["at"] <= clock]
                eligible.sort(key=lambda c: (c["deadline"], c["at"], c["id"], c["version"]))
            elif policy == "EARLIEST_DEADLINE":
                eligible.sort(key=lambda c: (c["deadline"], c["at"], c["id"], c["version"]))
            else:
                eligible.sort(key=lambda c: (c["at"], c["id"], c["version"]))
            card = eligible[0]
            pending.remove(card)
            key = (card["id"], card["version"])
            if key in cancels and cancels[key] <= clock:
                out["cancelled"].append({"id": card["id"], "version": card["version"], "at": cancels[key]})
                continue
            start = max(clock, card["at"])
            end = start + card["duration"]
            if end > card["deadline"]:
                out["expired"].append({"id": card["id"], "version": card["version"], "start": start, "end": end})
                clock = end
                continue
            out["reviews"].append({"id": card["id"], "version": card["version"], "start": start, "end": end})
            clock = end
            if card["decision"] == "no_response":
                continue
            receipt = {k: card[k] for k in ("id", "version", "principal", "target", "effect", "decision")}
            receipt["review_end"] = end
            out["receipts"].append(receipt)
            if card["decision"] == "accept":
                out["effect_attempts"].append({"id": card["id"], "version": card["version"], "principal": card["principal"], "target": card["target"], "effect": card["effect"], "receipt_id": f'{card["id"]}:{card["version"]}'})
        rows[policy] = out
    return {"schema": "authority-queue-result-v1", "rows": rows}


if __name__ == "__main__":
    src, dst = map(Path, sys.argv[1:3])
    result = run(json.loads(src.read_text(encoding="utf-8")))
    dst.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")

