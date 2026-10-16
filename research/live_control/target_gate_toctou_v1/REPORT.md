# Target gate TOCTOU v1

Issue: #965  
Publication base: `98c6bece2a46e04c3a872dbd45133afe18cb80a6`  
Decision: **`PASS_TARGET_GATE_TOCTOU_EXPOSED_SCOPED`**

## First outcome

One source-first frozen block ran exactly once: six matched pairs / twelve fresh private Xvfb+Tk sessions, counterbalanced order, reruns/replacements/tuning 0.

| Arm | Fresh gate | Independent clicked semantic role | Final A patch vs gated A |
| --- | ---: | --- | ---: |
| `stable` | 6/6 eligible | `task-target` 6/6 | max RGB error 0 |
| `swap` | 6/6 eligible | `decoy` 6/6 | max RGB error 240 |

All 12 cases ended with Button1 physically up according to the X11 pointer mask. Exactly one task click occurred per case.

In every swap case, the app emitted a mutation receipt strictly after gate completion and before pointer submission. No screenshot or pixel gate was taken between that receipt and the click. Gate-to-mutation delay was median 4.737 ms [1.490, 5.381]; mutation-to-click-start median 2.847 ms [0.330, 5.225]. Gate-to-click-start median was 5.306 ms [5.231, 10.421]. These timings describe synchronization in this fixture; they are not natural mutation-rate evidence or a safety deadline.

## Interpretation

A target patch can be fresh and correct at check time yet become stale before the side effect. The current observation therefore cannot, by itself, be treated as an atomic semantic admission boundary for a later pointer action. The swap stays on the same surface and at the same root coordinate; the target/decoy role and visible color change only after the gate.

This result is distinct from #956. #956 exposed a representation alias where source/current pixels were identical. Here the pre-action pixels are initially correct and visually unambiguous, then become observably different after the gate but before the click. The failure is temporal TOCTOU, not pixel aliasing.

The result does not prescribe a repair. A successor should compare exactly one pre-input current-evidence revalidation step against this retained failure while preserving ordinary authority/release semantics. Do not silently reinterpret historical pixels as authority.

## Integrity / evidence boundary

- formal block invocations: 1
- formal cases: 12/12
- reruns: 0
- audit errors: `[]`
- source-first Git blob readback matched the locally frozen PLAN/app/case/block/auditor bytes 5/5 before formal execution.
- raw PNGs are retained only in the disposable container for this run; Git publication retains decoded-RGB SHA-256, event/timing receipts and the compact per-case result, not the PNG bytes.
- `Xlib.xauth` emitted the known empty-Xauthority warning in cases; Xvfb used `-ac`, all cases completed, and the warning is not scored as evidence.

## Scope

Synthetic same-host Tk semantics on Linux/X11. The mutation is intentionally adversarial and synchronization-driven. No model, token, human-tempo, natural mutation-frequency, cross-backend, production-security or general GUI correctness claim follows.
