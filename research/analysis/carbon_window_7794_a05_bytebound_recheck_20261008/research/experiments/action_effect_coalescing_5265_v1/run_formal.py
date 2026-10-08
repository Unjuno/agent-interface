"""One frozen host-CPU execution of the Issue #5265 finite state matrix."""
import argparse
import hashlib
import json
from pathlib import Path

from experiment import POLICIES, execute_proposals


HERE = Path(__file__).resolve().parent
WORKLOAD = HERE / "workload.json"
SOURCE_FILES = ("experiment.py", "oracle.py", "audit.py", "run_formal.py",
                "test_coalescing.py", "test_audit.py", "workload.json",
                "README.md", "PLAN.md", "CONSTRUCTION.md")


def materialize(workload, case):
    proposals = []
    for specification in case["proposals"]:
        proposal = dict(workload["defaults"])
        proposal.update(specification["overrides"])
        proposal["proposal_id"] = specification["proposal_id"]
        proposal["producer_id"] = specification["producer_id"]
        proposals.append(proposal)
    return proposals


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--allocation", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    if output.exists():
        raise SystemExit("STOP_OUTPUT_COLLISION")

    workload_bytes = WORKLOAD.read_bytes()
    workload = json.loads(workload_bytes)
    rows = []
    for case in workload["cases"]:
        proposals = materialize(workload, case)
        observed = {}
        for policy in POLICIES:
            observed[policy] = execute_proposals(proposals, policy)
        rows.append({"case_id": case["case_id"], "proposals": proposals,
                     "expected": case["expected"], "observed": observed})

    raw = {
        "schema": "action-effect-coalescing-raw-v1",
        "issue": 5265,
        "allocation": args.allocation,
        "base_sha": args.base_sha,
        "workload_sha256": sha_bytes(workload_bytes),
        "source_sha256": {name: sha_bytes((HERE / name).read_bytes()) for name in SOURCE_FILES},
        "policies": list(POLICIES),
        "case_count": len(rows),
        "cases": rows,
        "resource_scope": {"runtime": "host-cpython", "network": "none-required",
                           "model": False, "gui_or_input": False,
                           "authority_or_effect_claim": False},
    }
    encoded = (json.dumps(raw, sort_keys=True, indent=2) + "\n").encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"status": "RAW_WRITTEN", "cases": len(rows),
                      "raw_sha256": sha_bytes(encoded), "bytes": len(encoded)}, sort_keys=True))


if __name__ == "__main__":
    main()
