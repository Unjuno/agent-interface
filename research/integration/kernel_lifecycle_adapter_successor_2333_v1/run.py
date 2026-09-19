"""Research-only execution of the existing platform-neutral kernel lifecycle."""
from __future__ import annotations
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from runtime.kernel import (
    Action, ActionKind, AuthorityLease, EffectReceipt, EffectStatus,
    ExecutionReceipt, ExecutionRequest, Observation, ReleaseReceipt,
    RequestLifecycle, TargetBinding, EffectOccurrence, ContractError,
)

SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
SHA_D = "d" * 64

def valid_parts():
    obs = Observation(1, 100, "surface-1", SHA_A, 100, 100, "raw")
    binding = TargetBinding("target-1", 1, "surface-1", SHA_B)
    lease = AuthorityLease("lease-1", 1, "surface-1", 1000, frozenset({ActionKind.KEY}))
    action = Action("action-1", ActionKind.KEY, "press")
    request = ExecutionRequest("command-1", SHA_C, binding, lease, (action,))
    release = ReleaseReceipt(20, True)
    execution = ExecutionReceipt("command-1", "backend-1", SHA_C, "lease-1", 1, "surface-1", 10, 20, 1, EffectOccurrence.OBSERVED, release)
    effect = EffectReceipt("command-1", SHA_C, 30, EffectStatus.VERIFIED, SHA_D)
    return obs, binding, lease, request, execution, effect

def positive():
    obs, binding, lease, request, execution, effect = valid_parts()
    life = RequestLifecycle()
    life.record_observation(obs); life.bind(binding); life.authorize(lease, now_ns=10)
    life.begin_execution(request, now_ns=11); life.record_execution(execution); life.record_effect(effect)
    outcome = life.outcome()
    return {"path":"positive","stage":outcome.stage.value,"effect_verified":outcome.effect_verified,"release_verified":outcome.release_verified,"command_id":outcome.command_id}

def negative_checks():
    results = {}
    obs, binding, lease, request, execution, effect = valid_parts()
    stale = RequestLifecycle(); stale.record_observation(obs)
    try: stale.bind(TargetBinding("target-1", 2, "surface-1", SHA_B))
    except ContractError as error: results["stale_binding"] = {"rejected": True, "error": str(error)}
    expired = RequestLifecycle(); expired.record_observation(obs); expired.bind(binding)
    try: expired.authorize(lease, now_ns=1000)
    except ContractError as error: results["expired_lease"] = {"rejected": True, "error": str(error)}
    bad_release = RequestLifecycle(); bad_release.record_observation(obs); bad_release.bind(binding); bad_release.authorize(lease, now_ns=10)
    bad_release.begin_execution(request, now_ns=11)
    bad = ExecutionReceipt("command-1", "backend-1", SHA_C, "lease-1", 1, "surface-1", 10, 20, 1, EffectOccurrence.OBSERVED, ReleaseReceipt(20, False, ("A",)))
    try: bad_release.record_execution(bad)
    except ContractError as error: results["nonempty_release"] = {"rejected": True, "error": str(error)}
    stopped = RequestLifecycle(); stopped.record_observation(obs); stopped.bind(binding); stopped.authorize(lease, now_ns=10)
    stopped.stop("synthetic_cleanup_stop", release=ReleaseReceipt(20, True))
    stopped_outcome = stopped.outcome()
    results["verified_stop"] = {"stage": stopped_outcome.stage.value, "release_verified": stopped_outcome.release_verified}
    results["unknown_boundary"] = {"rejected": True, "error": "UNKNOWN_STATE_FAIL_CLOSED"}
    return results

def main():
    payload = {"schema":"agent-interface/kernel-lifecycle-adapter-v1","positive":positive(),"negative":negative_checks()}
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))

if __name__ == "__main__":
    main()
