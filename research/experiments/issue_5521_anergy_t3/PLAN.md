# Issue #5521 T3 — matched expiry-policy fork

## H/T/D/C/U

- **H:** Under an identical event schedule, clear-on-expiry and tombstone-on-expiry differ in whether the same fingerprint/generation can be rechecked after expiry. Tombstones avoid repeated checks but may suppress candidates indefinitely; clear-on-expiry can re-admit on unchanged evidence.
- **T:** Run both arms over the exact same frozen 11-event schedule, same fingerprints, targets, authority generations, evidence, restart points, and expiry tick. Each arm uses separate short-lived worker processes. State crosses process boundaries only as serialized JSON. Record per-event transitions, state digests, worker PIDs/exit codes, and a shared schedule hash. An independently implemented raw-only auditor checks both arms and fixed mutations.
- **D:** PASS_EXPIRY_POLICY_FORK_SCOPED only if all worker exits are zero; restart state hashes and schedule align; auditor reports zero errors and rejects mutations; arms differ only at the registered expiry event; neither arm emits a generation-1 effect. Clear-arm same-generation recheck at expiry is an explicit policy outcome, not a general safety pass.
- **C:** Small deterministic authored state machine; expiry clears are not proven preferable to tombstones.
- **U:** Host construction only: not a container run, durable-storage/crash-consistency test, GUI safety test, semantic-fingerprint validation, or product recommendation.

## Freeze

- Issue #5521 T3 proposal comment 5913200316.
- Base: ddd2a4b473f7418665619cdacff60cc2b306ad95.
- Output: research/experiments/issue_5521_anergy_t3/.
- No Docker/OrbStack invocation: #5085 prioritizes the outstanding #5156 lane; no #5521 lease is assigned.
- Network/model/GPU/GUI/input: none.
