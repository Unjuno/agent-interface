"""Ordinary, input-free constructor/lifecycle regression matrix; no formal allocation."""
import argparse
import hashlib
import itertools
import json
import platform
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from runtime.kernel import (
    Action, ActionKind, AuthorityLease, ContractError, EffectOccurrence,
    ExecutionReceipt, ExecutionRequest, Observation, ReleaseReceipt,
    RequestLifecycle, TargetBinding,
)


def collect(revision):
    rows = []
    for start, end, released, verified in itertools.product(range(5), range(5), range(7), (False, True)):
        if end < start:
            continue
        flow = RequestLifecycle()
        obs = Observation(1, 0, "fixture", "0" * 64, 1, 1, "rgb24")
        binding = TargetBinding("fixture-key", 1, "fixture", "2" * 64)
        lease = AuthorityLease("lease", 1, "fixture", 20, frozenset({ActionKind.KEY}))
        request = ExecutionRequest("command", "1" * 64, binding, lease,
                                   (Action("action", ActionKind.KEY, "press"),))
        flow.record_observation(obs)
        flow.bind(binding)
        flow.authorize(lease, now_ns=0)
        flow.begin_execution(request, now_ns=0)
        row = dict(started_ns=start, ended_ns=end, observed_ns=released, verified=verified,
                   representation_accepted=False, terminal_accepted=False)
        try:
            receipt = ExecutionReceipt("command", "receipt", "1" * 64, "lease", 1,
                "fixture", start, end, 1, EffectOccurrence.POSSIBLE, ReleaseReceipt(released, verified))
            row["representation_accepted"] = True
            flow.record_execution(receipt)
            row["terminal_accepted"] = True
        except ContractError:
            pass
        rows.append(row)
    source = ROOT / "runtime/kernel/contracts.py"
    return dict(schema="kernel-release-epoch-matrix-v1", revision=revision,
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                environment=dict(python=sys.version, platform=platform.platform()), rows=rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("revision", choices=("baseline", "fixed"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data = collect(args.revision)
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(data, out, indent=2, sort_keys=True)
        out.write("\n")
    print(f"{args.revision}: {len(data['rows'])} rows retained")
