"""Independent expected-outcome audit of raw fixture and saved probe result."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def expected(sample):
    health, ammo = sample["health"], sample["ammo"]
    paired = all(health.get(key) == ammo.get(key) for key in ("sequence", "capture_ns", "binding"))
    if not paired:
        return True, "PAIR_MISMATCH"
    for signal, signal_id, floor in ((health, "health", 90), (ammo, "ammo", 1)):
        if signal.get("status") != "observed" or signal.get("signal_id") != signal_id:
            return True, "PAIRED"
        if type(signal.get("value")) is not int or signal["value"] < floor:
            return True, "PAIRED"
    return False, "PAIRED"


def main():
    fixture = json.loads((ROOT / "fixture.json").read_text(encoding="utf-8"))
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    actual = {row["name"]: row for row in result["rows"]}
    checks = []
    for sample in fixture["samples"]:
        invalidate, status = expected(sample)
        row = actual[sample["name"]]
        checks.extend((
            row["outcome"]["requires_new_decision"] == invalidate,
            row["outcome"]["status"] == status,
            row["expected"] == invalidate,
            row["outcome"]["grants_input_authority"] is False,
        ))
    checks.extend((len(actual) == len(fixture["samples"]), result["live_allocation_invocations"] == 0))
    audit = {"format": "59-v39-paired-health-ammo-audit-v1", "passed": sum(checks), "total": len(checks), "disposition": "PASS" if all(checks) else "AUDIT_FAILED"}
    (ROOT / "AUDIT.json").write_text(json.dumps(audit, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
