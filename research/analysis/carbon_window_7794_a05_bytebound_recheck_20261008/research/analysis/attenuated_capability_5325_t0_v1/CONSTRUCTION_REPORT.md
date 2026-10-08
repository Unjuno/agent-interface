# Issue #5325 — attenuated capability chain construction T0

## Status

`PASS_CONSTRUCTION_ONLY`; **formal container allocation pending**. This is a deterministic, hand-authored, no-effect host construction replay, not a capability-security result. Formal runner/auditor invocations: 0/0.

## H/T/D/C/U

- **H:** Explicit attenuated capability checks can reject more unauthorized proposals than actor/context and lease-only baselines; a revocation-aware confined chain must fail closed when the backend cannot enforce the capability.
- **T:** Eleven finite synthetic traces × five policies: `CONTEXT_POLICY`, `LEASE_ONLY`, `ATTENUATED_CHAIN`, `CONFINED_CHANNEL`, `REVOCATION_STRESS`. Traces cover valid minimum rights, confused deputy, rights amplification, forgery, cross-task reuse, expiry, duplicate single-use use, revoked descendant, ambient global handle, unconfined channel, and backend non-enforcement.
- **D:** Source/input freeze, simulator, separate raw auditor, 55-row construction raw, audit result, corruption controls, hashes, and scope notes. Formal PASS gate remains the frozen condition in `FREEZE.json`; construction pass is only harness/accounting readiness.
- **C:** Finite binary fields and exact rules are authored, not inferred from real adapters. The toy case distribution omits concurrency, key leakage, partial effects, revocation latency, and backend-specific semantics. No runtime/CPU/latency overhead measured.
- **U:** Which real tool boundaries enforce capabilities? How are ambient handles confined? What is revocation semantics for in-flight effects? Can model-visible representations leak or amplify tokens? What overhead/false rejection appears in actual adapters?

## Construction replay

Host: Windows x64, CPython 3.12.10. Docker Desktop `desktop-linux`, Engine 28.5.1 is responsive. Cached image identity/platform readback: `python@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`, `linux/amd64`. No container was started: an exact exclusive shared-lane assignment has not been granted.

Commands, each invoked once after the source/input/gate freeze:

```powershell
python .cache-memory-lab/5325-construction/simulate.py > .cache-memory-lab/5325-construction/construction_raw.json
python .cache-memory-lab/5325-construction/independent_audit.py .cache-memory-lab/5325-construction/construction_raw.json > .cache-memory-lab/5325-construction/construction_audit.json
```

Audit: 55 rows, 0 disagreements; 4/4 mutation controls rejected. Synthetic unauthorized proposal admissions: context policy 10, lease-only 8, attenuated chain 1, confined channel 1, revocation-stress 0. The remaining attenuated-chain/confined-channel admissions correspond to omitted channel/revocation controls in those respective arms. The backend-nonenforcement trace returns `UNKNOWN_ENFORCEMENT` with no dispatch for all capability-chain arms. The clean minimum-rights trace produces an enforced dispatch under the capability policies.

These figures are exact only for the embedded finite oracle. They do not estimate field rates, predict actual security, or establish the cost/acceptability half of H.

## Formal start gates

Do not start the pinned container until Issue #5085 records an exclusive named CPU lane for `attcap-chain-5325-t0-20260930-01`, with exact owner, source/main binding, image/platform/runtime readback, start/end, and release rule. At formal start, re-read latest main and all source/gate blobs; if stale, prepare a successor freeze instead of silently rebasing. If granted: one network-disabled, source-read-only bounded runner; only on exit 0, one separate raw-only auditor. No retry, model, GPU, GUI, action, or external effect.
