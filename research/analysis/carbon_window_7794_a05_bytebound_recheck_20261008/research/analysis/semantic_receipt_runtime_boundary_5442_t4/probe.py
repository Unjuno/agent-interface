#!/usr/bin/env python3
"""One deterministic probe of the current mechanical receipt contract."""
from __future__ import annotations

import hashlib
import json
from dataclasses import fields
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from runtime.kernel import (
    Action,
    ActionKind,
    AuthorityLease,
    EffectOccurrence,
    EffectReceipt,
    EffectStatus,
    ExecutionReceipt,
    ExecutionRequest,
    Observation,
    ReleaseReceipt,
    RequestLifecycle,
    TargetBinding,
)


FREEZE_COMMIT = "d00ffdd74cde6c7f113cb03382be853879d5cb65"
SOURCE_BLOBS = {
    "runtime/kernel/contracts.py": "3d24fb5b28ae7812c71c6c1fedd3439d1473f0b8",
    "runtime/kernel/lifecycle.py": "0735f1b2bc4f8c8c66a16cd0687a8b631c99f0b3",
}
SEMANTIC_FIELDS = (
    "intent_hash",
    "goal_predicate_hash",
    "target_namespace",
    "pre_state_version",
    "post_state_version",
    "observer_id",
    "dependency_provenance",
    "freshness",
    "execution_receipt_ref",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    manifest = digest(b"frozen mechanical invariants")
    binding = TargetBinding("save-button", 7, "surface-a", digest(b"binding"))
    lease = AuthorityLease(
        "lease-1", 7, "surface-a", 1000, frozenset({ActionKind.POINTER})
    )
    request = ExecutionRequest(
        "cmd-1", manifest, binding, lease,
        (Action("click-1", ActionKind.POINTER, "click"),),
    )

    flow = RequestLifecycle()
    flow.record_observation(
        Observation(7, 100, "surface-a", digest(b"frame"), 1280, 800, "rgb24")
    )
    flow.bind(binding)
    flow.authorize(lease, now_ns=200)
    flow.begin_execution(request, now_ns=300)
    flow.record_execution(
        ExecutionReceipt(
            "cmd-1", "backend-1", manifest, "lease-1", 7, "surface-a",
            500, 700, 1, EffectOccurrence.OBSERVED,
            ReleaseReceipt(800, True, (), ()),
        )
    )
    # Mechanically valid digest bytes have no contract-level link to intent/state.
    flow.record_effect(
        EffectReceipt(
            "cmd-1", manifest, 900, EffectStatus.VERIFIED,
            digest(b"opaque evidence not bound to declared semantic intent"),
        )
    )
    outcome = flow.outcome()
    request_fields = [field.name for field in fields(ExecutionRequest)]
    effect_fields = [field.name for field in fields(EffectReceipt)]
    result = {
        "schema": "semantic_receipt_runtime_boundary_probe_v1",
        "freeze_commit": FREEZE_COMMIT,
        "source_blobs": SOURCE_BLOBS,
        "outcome": {
            "stage": outcome.stage.value,
            "effect_verified": outcome.effect_verified,
            "release_verified": outcome.release_verified,
        },
        "request_fields": request_fields,
        "effect_receipt_fields": effect_fields,
        "semantic_fields_absent": [
            name for name in SEMANTIC_FIELDS
            if name not in request_fields + effect_fields
        ],
        "scope": "mechanical contract only; no application effect or semantic success asserted",
    }
    assert result["outcome"] == {
        "stage": "verified",
        "effect_verified": True,
        "release_verified": True,
    }
    assert result["semantic_fields_absent"] == list(SEMANTIC_FIELDS)
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
