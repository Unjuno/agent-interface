# Issue #5442 — current runtime semantic-receipt boundary probe

Status: `PASS_SCOPED_MECHANICAL_BOUNDARY`; not an end-to-end semantic-success
result and not a formal T4 completion.

## H / T / D / C / U

**H.** The current `runtime/kernel` lifecycle may mechanically accept an
`EffectStatus.VERIFIED` receipt without a contract-level binding to the intended
goal, semantic target namespace, pre/post state versions, or observer provenance.
If so, `effect_verified` is a mechanical receipt state and must not be read as
end-to-end semantic success.

**T.** Deterministic, host-only construction probe against exact current-main
source at freeze commit `d00ffdd74cde6c7f113cb03382be853879d5cb65`. It uses the
public `runtime.kernel` types to record a current observation, target binding,
lease, one pointer action, a completed execution with verified release, and an
effect receipt whose opaque evidence digest is not linked to intent/state
fields. It reports actual dataclass fields and lifecycle outcome. The probe was
first run ad hoc, then packaged and rerun to retain its JSON; the second raw is
at `raw/probe.json`. The raw-only schema/outcome auditor is `audit.py`, with
four mutation-rejection controls in `test_audit.py`. The kernel's existing
unit suite was run unchanged after the probe.

Frozen source identities:

| File | Git blob |
|---|---|
| `runtime/kernel/contracts.py` | `3d24fb5b28ae7812c71c6c1fedd3439d1473f0b8` |
| `runtime/kernel/lifecycle.py` | `0735f1b2bc4f8c8c66a16cd0687a8b631c99f0b3` |
| `runtime/kernel/README.md` | `fbb730d11d226f6553a39bc7ded1a65d40765e94` |

**D.** Both invocations produced `stage=verified`, `effect_verified=true`, and
`release_verified=true`. `ExecutionRequest` fields are `command_id`,
`invariant_manifest_id`, `binding`, `lease`, `actions`; `EffectReceipt` fields
are `command_id`, `invariant_manifest_id`, `observed_ns`, `status`,
`evidence_digest`. The following contract-level fields are absent:
`intent_hash`, `goal_predicate_hash`, `target_namespace`, `pre_state_version`,
`post_state_version`, `observer_id`, `dependency_provenance`, `freshness`, and
`execution_receipt_ref`. The raw-only audit returned
`PASS_SCOPED_MECHANICAL_BOUNDARY`; raw-auditor tests passed 2/2, including
4/4 mutated-output rejection; unchanged kernel tests passed 18/18. The kernel
README intentionally limits this package to mechanical evidence and disclaims
semantic authority, so this is a boundary characterization, not a kernel bug
claim.

**C.** CPython 3.14.5, Darwin arm64; host-only. The first packaged-runner
attempt stopped before executing the probe with `ModuleNotFoundError: No module
named 'runtime'` because Python's script path did not include the repository
root. The runner was corrected to resolve that root; the subsequent packaged
run and tests passed. This packaging STOP is retained and is not counted as a
candidate semantic failure. A later kernel-test invocation from the artifact
subdirectory also stopped on repository-root import resolution; the corrected
repository-root run passed 18/18. The first checksum invocation from repository
root could not resolve artifact-relative manifest entries; rerunning from the
artifact directory verified every checksum. These are invocation-location
errors, not evidence mismatches. No GUI, model, application effect, live
allocation, or source backend dispatch occurred. Docker was not started: read-only process
inventory showed many unrelated Docker clients already blocked for 57 minutes
to over four hours; no exclusive container slot/owner could be established.
No such process was signalled or modified. Therefore the containerized
simulator rung in #5442 remains unrun.

**U.** This does not authenticate evidence digests, assess observer fidelity,
or prove end-to-end task correctness. Next empirical gate: bind a real
application intent/goal predicate and target namespace to an authoritative,
fresh pre/post-state observation, then challenge it with stale, wrong-target,
no-op, partial, and observer-common-mode controls through the integrated path.
Keep `UNKNOWN` distinct from mechanical `VERIFIED`. This scoped probe does not
close #5442 or satisfy #57/#2789's matched six-task desktop integration spine.
Prior #5442 T0–T3 and the merged T3 result are unchanged.

## Reproduction

From repository root:

```sh
python3 -B research/analysis/semantic_receipt_runtime_boundary_5442_t4/probe.py \
  > research/analysis/semantic_receipt_runtime_boundary_5442_t4/raw/probe.json
python3 -B research/analysis/semantic_receipt_runtime_boundary_5442_t4/audit.py \
  research/analysis/semantic_receipt_runtime_boundary_5442_t4/raw/probe.json \
  > research/analysis/semantic_receipt_runtime_boundary_5442_t4/raw/audit.json
python3 -m unittest discover \
  -s research/analysis/semantic_receipt_runtime_boundary_5442_t4 -p 'test_*.py' -v
python3 -m unittest discover -s runtime/kernel -p 'test_*.py' -v
```

Retained raw hashes:

- `raw/probe.json`: `83c0c06458a6f25ebec09eb07b89576b23ce2bd645cca9d60373142e81836b8e`
- `raw/audit.json`: `ce0c09ca6eb1652f2b7300e46671505265917e188e690824a80405bbc81a8603`
