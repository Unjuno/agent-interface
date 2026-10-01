"""Black-box temporal receipt probe for Issue #5215; stdlib only."""
from __future__ import annotations

import hashlib
import json

from runtime.kernel import (
    Action, ActionKind, AuthorityLease, EffectOccurrence, EffectReceipt,
    EffectStatus, ExecutionReceipt, ExecutionRequest, Observation,
    ReleaseReceipt, RequestLifecycle, TargetBinding,
)


def fixture():
    digest = hashlib.sha256(b"fixture").hexdigest()
    observation = Observation(7, 100, "surface", digest, 10, 10, "rgb24")
    binding = TargetBinding("target", 7, "surface", digest)
    lease = AuthorityLease("lease", 7, "surface", 1000, frozenset({ActionKind.POINTER}))
    request = ExecutionRequest(
        "command", digest, binding, lease,
        (Action("action", ActionKind.POINTER, "click"),),
    )
    flow = RequestLifecycle()
    flow.record_observation(observation)
    flow.bind(binding)
    flow.authorize(lease, now_ns=200)
    flow.begin_execution(request, now_ns=300)
    return flow, request, digest


def try_execution(end_ns: int, command_id: str = "command") -> bool:
    flow, request, _ = fixture()
    receipt = ExecutionReceipt(
        command_id, "backend-receipt", request.invariant_manifest_id,
        request.lease.lease_id, 7, "surface", 500, end_ns, 1,
        EffectOccurrence.POSSIBLE, ReleaseReceipt(800, True),
    )
    try:
        flow.record_execution(receipt)
        return True
    except ValueError:
        return False


def try_effect(observed_ns: int) -> bool:
    flow, request, digest = fixture()
    execution = ExecutionReceipt(
        "command", "backend-receipt", digest, "lease", 7, "surface",
        500, 700, 1, EffectOccurrence.POSSIBLE, ReleaseReceipt(800, True),
    )
    flow.record_execution(execution)
    receipt = EffectReceipt("command", digest, observed_ns, EffectStatus.VERIFIED, digest)
    try:
        flow.record_effect(receipt)
        return True
    except ValueError:
        return False


def main() -> None:
    outcomes = {
        "execution_end_700": try_execution(700),
        "execution_end_999": try_execution(999),
        "execution_end_1000": try_execution(1000),
        "execution_end_1001": try_execution(1001),
        "execution_wrong_command": try_execution(700, "other"),
        "effect_at_499": try_effect(499),
        "effect_at_699": try_effect(699),
        "effect_at_700": try_effect(700),
        "effect_at_701": try_effect(701),
    }
    print(json.dumps(outcomes, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
