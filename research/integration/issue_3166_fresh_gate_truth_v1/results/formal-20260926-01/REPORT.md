# Issue #3166 — formal first-rung result

Allocation `issue3166-fresh-gate-truth-rung1-20260926-01` ran exactly once after the frozen
pre-registration was posted to Issue #3166. The frozen source was
`27cb529f694609581c4a5b39e85ac782772e9aab`; source, runner, image, and scenario hashes are in
`../../FREEZE.json` and the adjacent evidence bundle.

## Decision

`PASS_GATE_TRUTH_FIRST_RUNG_SCOPED` — all 25 preregistered rows completed, and the separate
raw-only audit passed all 16 checks with zero errors. This is a policy-model/GTK-fixture result;
it is not a production commit-gate implementation or a completion of Issue #3166.

| Policy | Admitted / 6 | Unsafe-context effects / 5 |
|---|---:|---:|
| `TWO_TIER_FRESH_GATE` | 1 | 0 |
| `DEPENDENCY_ONLY` | 6 | 5 |
| `GATE_ONLY` | 1 | 0 |
| `CACHED_PREPARE_GATE` | 6 | 5 |

The five invalid gate contexts were fresh FALSE, fresh UNKNOWN, stale TRUE, intent mismatch, and
epoch mismatch. The admitted unsafe cases in the dependency-only and cached-prepare models each
produced a retained GTK `effect.json` and save event. The two fail-closed policies had zero native
input emissions for all five invalid contexts. All admitted useful actions recorded completed
native dispatch, verified release, and the exact fixture postcondition.

The separate valid-gate `no_effect` control completed native dispatch with four input emissions,
but had no application effect receipt; it remains `HOLD_POSTCONDITION_UNOBSERVED`, as frozen.

## Interpretation limits and open work

This runner models the admission rules outside the current runtime; the runtime has no general
commit-gate API. Intent and epoch contexts are fixture-bound identity values. This allocation did
not test stale prepared dependencies, malformed evidence, duplicate commit, or the rest of the
Issue's held-out set. It makes no universal GUI, model, cross-platform, integrated-product, or
production-safety claim. Issue #3166 remains open; no predecessor result was modified.

## Reproduction and retained evidence

Formal runner and raw-only scorer ran in separate containers from image
`sha256:69bc215db0514ee1bc4f730cceb296ecef89e4418cea8d4b2fc2ca3101101e27` (`linux/arm64`), both
with network disabled, read-only root filesystem, all capabilities dropped, no-new-privileges,
read-only source/study mounts, and bounded CPU/memory/PIDs. The formal container exited 0 with
25 rows. The independent audit container exited 0. Full inspect JSON, stdout logs, per-row JSON,
fixture events/effects, preflight, raw JSONL, and `AUDIT.json` are retained under `evidence/`.

Raw JSONL SHA-256: `795cf31a651d814b4072553de1c688e5c5f31157f2787c792d2d667b2a7aa759`.
Audit JSON SHA-256: `375f811641ef664a25d9d715fbcb919dc198fa38442c885d204336c5df43b2ac`.

Before formal execution, the pinned container passed the current-main golden-v3 and native-boundary
unit tests (16/16); the separate GTK/X11 startup/teardown construction smoke passed with zero input.
These are construction/CI evidence, distinct from the formal result.
