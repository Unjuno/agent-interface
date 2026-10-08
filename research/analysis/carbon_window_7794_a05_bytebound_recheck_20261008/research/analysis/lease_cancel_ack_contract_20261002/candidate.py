"""One-shot host test of real Lease cancellation acknowledgements."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "frozen_lease_source.py"
ALLOCATION = "LEASE-CANCEL-ACK-CONTRACT-HOST-T0-20261002-01"


def load_lease():
    spec = importlib.util.spec_from_file_location("frozen_lease", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Lease, module.Expired


def run_case(name, start_ns, deadline_ns, cancel_before_wait, cancel_at_boundary=False):
    now = [start_ns]
    Lease, Expired = load_lease()
    lease = Lease(deadline_ns, clock=lambda: now[0])
    rows = [{"event": "case_start", "case": name, "now_ns": now[0], "deadline_ns": deadline_ns}]
    if cancel_before_wait:
        if cancel_at_boundary:
            now[0] = deadline_ns
        lease.set()
        rows.append({"event": "cancel_set", "case": name, "now_ns": now[0]})
    try:
        lease.check()
        result = lease.wait(0)
        rows.append({"event": "wait_return", "case": name, "now_ns": now[0], "cancel_ack": result})
        terminal = "cancelled" if result is True else "continued"
    except Expired:
        rows.append({"event": "wait_expired", "case": name, "now_ns": now[0]})
        terminal = "expired"
    rows.append({"event": "worker_terminal", "case": name, "now_ns": now[0], "status": terminal})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=False)
    rows = [{"event": "fixture", "allocation": ALLOCATION, "scope": "host-real-Lease-synthetic-clock",
             "docker": False, "external_effects": False}]
    rows += run_case("cancel_before_deadline", 100, 1000, True)
    rows += run_case("deadline_without_cancel", 100, 1000, False)
    rows += run_case("cancel_at_deadline", 100, 1000, True, cancel_at_boundary=True)
    out.write_text("".join(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n" for r in rows),
                   encoding="utf-8", newline="\n")
    print(json.dumps({"candidate": "LEASE_CANCEL_ACK_CONTRACT", "rows": len(rows), "output": str(out)},
                     sort_keys=True))


if __name__ == "__main__":
    main()
