"""Input-free, sequential API composition matrix; no backend methods emit input."""
import argparse
import itertools
import json
import platform
import sys
from pathlib import Path
from types import SimpleNamespace


def collect(root):
    sys.path.insert(0, str(root))
    from runtime.kernel import (
        Action, ActionKind, AuthorityLease, BackendInfo, BackendRegistry,
        ContractError, EffectOccurrence, ExecutionReceipt, ExecutionRequest,
        Observation, ReleaseReceipt, RequestLifecycle, SupportLevel, TargetBinding,
    )
    rows = []
    for states, bad_first, duplicate, release_tick, verified in itertools.product(
        itertools.product(range(3), repeat=4), (False, True),
        ("none", "same", "different"), (499, 500, 800), (False, True),
    ):
        calls = dict(probe=0, observe=0, execute=0, release_all=0)
        info = BackendInfo("inert", "fixture", SupportLevel.EXPERIMENTAL, frozenset())

        def method(name):
            def called(*args):
                calls[name] += 1
                if name != "probe":
                    raise RuntimeError("unexpected inert method dispatch")
                return info
            return called

        backend = SimpleNamespace()
        for name, state in zip(calls, states):
            if state:
                setattr(backend, name, method(name) if state == 2 else None)
        registry = BackendRegistry()
        registry.register("fixture", lambda: backend)
        row = dict(states=list(states), bad_first=bad_first, duplicate=duplicate,
                   release_tick=release_tick, verified=verified,
                   backend="unreached", first_bad="unreached", duplicate_result="unreached",
                   first_preserved=None, representation="unreached", terminal="unreached",
                   final_stage=None, command_id=None, error=None, calls=calls)
        try:
            try:
                registry.create("fixture")
                row["backend"] = "accepted"
            except ContractError:
                row["backend"] = "refused"
                rows.append(row)
                continue
            flow = RequestLifecycle()
            obs = Observation(1, 100, "surface", "0" * 64, 1, 1, "rgb24")
            bind = TargetBinding("target", 1, "surface", "2" * 64)
            lease = AuthorityLease("lease", 1, "surface", 1000, frozenset({ActionKind.KEY}))
            req = ExecutionRequest("first", "1" * 64, bind, lease,
                                   (Action("one", ActionKind.KEY, "press"),))
            flow.record_observation(obs)
            flow.bind(bind)
            flow.authorize(lease, now_ns=200)
            if bad_first:
                wrong_bind = TargetBinding("target", 1, "other", "2" * 64)
                wrong_lease = AuthorityLease("lease", 1, "other", 1000, lease.allowed_actions)
                wrong = ExecutionRequest("bad", "1" * 64, wrong_bind, wrong_lease, req.actions)
                try:
                    flow.begin_execution(wrong, now_ns=300)
                    row["first_bad"] = "accepted"
                except ContractError:
                    row["first_bad"] = "refused"
            else:
                row["first_bad"] = "not_requested"
            flow.begin_execution(req, now_ns=300)
            if duplicate != "none":
                second = req if duplicate == "same" else ExecutionRequest(
                    "second", req.invariant_manifest_id, bind, lease, req.actions)
                try:
                    flow.begin_execution(second, now_ns=400)
                    row["duplicate_result"] = "accepted"
                except ContractError:
                    row["duplicate_result"] = "refused"
            else:
                row["duplicate_result"] = "not_requested"
            row["first_preserved"] = flow.request is req
            try:
                release = ReleaseReceipt(release_tick, verified, () if verified else ("A",))
                receipt = ExecutionReceipt("first", "inert", "1" * 64, "lease", 1,
                    "surface", 500, 700, 1, EffectOccurrence.POSSIBLE, release)
                row["representation"] = "accepted"
                try:
                    flow.record_execution(receipt)
                    row["terminal"] = "accepted"
                except ContractError:
                    row["terminal"] = "refused"
            except ContractError:
                row["representation"] = "refused"
            row["final_stage"] = flow.stage.value
            row["command_id"] = flow.request.command_id
        except Exception as exc:
            row["error"] = type(exc).__name__
        rows.append(row)
    return rows


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("revision", choices=("baseline", "combined"))
    p.add_argument("output", type=Path)
    args = p.parse_args()
    data = dict(schema="kernel-three-boundaries-v1", revision=args.revision,
                environment=dict(python=sys.version, platform=platform.system(), machine=platform.machine()),
                rows=collect(args.root))
    with args.output.open("x") as f:
        json.dump(data, f, separators=(",", ":"), sort_keys=True)
        f.write("\n")
    print(json.dumps(dict(revision=args.revision, rows=len(data["rows"]))))
