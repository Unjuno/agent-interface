# MAP01 recovery reanchor receipt — formal result

Task `MAP01-RECOVERY-REANCHOR-RECEIPT-20260917-001`, Issue #615.

## Decision

**`PASS_REANCHOR_RECEIPT_SCOPED`**.

One source-first frozen formal block ran once: 3 matched pairs / 6 fresh recovery cases. No retry, replacement, extension, threshold tuning, or model/provider call. The old pre-recovery action was baseline `VALID_CURRENT` yet visual-context `REJECT_CONTEXT_CHANGED` in all 6 cases.

The only handoff factor after rejection was:
- `recapture`: exactly one observe-only program; post sequence 21 -> new sequence 22 in 3/3.
- `reanchor_receipt`: zero extra observation programs; the exact post-recovery sequence-21 observation is bound into a new planner-source receipt using capture sequence, RGB hash and pointer binding, with `grants_input_authority=false` and old action authority discarded, 3/3.

Every case retained health 97, ammo 48, completed recovery, verified empty key/button release, 0 kills, 0 deaths and no map exit. Frozen audit, independent raw-command verification and real-formal mutation controls all pass.

## Descriptive timing — not a promotion gate

| pair | recapture ms | reanchor receipt ms |
|---:|---:|---:|
| 1 | 61.099820 | 0.001001 |
| 2 | 57.521650 | 0.002344 |
| 3 | 60.349412 | 0.000691 |

Median recapture handoff was 60.349412 ms; receipt handoff was 0.001001 ms. This is descriptive only. The frozen decision does not depend on timing.

## Interpretation

For this fixed fixture, the exact post-recovery observation that already justified rejecting stale action authority can seed a **new planner decision context** without another capture and without granting input authority. This removes one redundant observation boundary. It does not make the rejected old action valid and does not select a new action.

The next model-in-loop gate may therefore discard the old action, promote the exact current observation as no-authority planner context, and require a fresh planner decision. This result does not authorize stale action reuse or promote full-frame MAE as a universal production semantic.

## Evidence boundary

Exact formal summary SHA-256: `452f515c57f0a29cb520d45b80fb1393fb941003b48ca70aac0c5b183fcb3959`.
Frozen audit SHA-256: `71cab7a7f853cd167066583d993f30c537f01d3037de480d4dc1aac632ba05f1`.
Independent postformal verification SHA-256: `67bbd4867bffb9f029e930676f9b3673632db7d36731d3ff8900b6001cd8afd2`.
Postformal real-raw mutation controls SHA-256: `eb08f8e309cc0d8ffcc54f0e9c2f136d42f0ba2217cbfbf735ce44bdcf6c55ee`.
Compact replay archive: 1,947,676 bytes, SHA-256 `1b882fc172ba0bb77268aadcfefe485f18c1ac2d42235eea522f7498e7e14e87`; retained conversation/container-side, not claimed GitHub-retained.

Source-first package is GitHub-retained byte-exact as `source_bundle.tar.xz`, Git blob `1c6fce0a43225e17df21e60db8eef5b4b4e39a94`, XZ SHA-256 `7d0df05a08ee6c4fff8d193f69dcc7191879812a8e6041327b15749ee0f7300b`.