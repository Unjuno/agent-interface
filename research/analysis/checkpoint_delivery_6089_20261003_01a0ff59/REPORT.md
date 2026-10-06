# Result: scheduled checkpoint absence is not a fresh delivery

Status: **COUNTEREXAMPLE_DELIVERY_REPRESENTATION_AND_NORMALIZATION_SCOPED**. One new ordinary host-stdlib producer and one separate raw auditor completed; no historical formal runner/allocation was invoked. Three contexts by four encodings by two arms produced exactly24 ordered rows.

| Context | Legacy receipt usable | Legacy C status | Explicit-absence receipt usable | Explicit-absence C status |
|---|---:|---|---:|---|
| k0 | True | NO_LOSS_CONTROL | False | BOUND_EXCEEDED_STOP_AT_FROZEN_DEADLINE |
| k1_boundary | True | NO_LOSS_CONTROL | False | IN_BOUND_ERASURE_PATTERN |
| invalidated | True | YIELD_INVALIDATED_TARGET | False | YIELD_INVALIDATED_TARGET |

The old candidate and old auditor both synthesize a FRESH event for an empty deck. Their separate miss-count loops then record zero misses. The invalidated context still yields, so it is not relabeled as NO_LOSS; its receipt-usable flag nevertheless lacks delivered evidence. The separate raw-only oracle uses Cartesian disturbance paths and all prefixes, compares every output field with typed canonical JSON, and does not import the producer or either retained module.

All24 outputs match the separately reconstructed literal source behavior. Exactly3 legacy empty outputs violate the declared known-checkpoint absence contract and all3 were accepted by the retained auditor. Normalized mismatches are0, nine nonempty pairs are unchanged, and all3 normalized empty outputs equal explicit MISSING outputs after removing only the case ID. Eight copied-raw corruptions reject, including numeric type aliasing and fabricated freshness.

In the k1 boundary fixture the empty-deck fallback also hides the deliberately optimistic comparator's planted negative: A is labeled safe at6 modeled slots, while an explicit missing checkpoint extends A to7 slots and reaches boundary14. This demonstrates the representation blind spot; A remains an unsafe negative comparator and normalization does not certify it as a controller. B/C reachable-path mathematics, action, target, model, boundaries and release dynamics were not changed by the comparator.

## Execution and evidence

Prospective main base: `a3e93e471f065214ed01b050683aaecbe0db3b4d`. Source witness base: `332da58a9b6b825c384a142dfb59d7ed2b8b774e`; all six legacy blobs were byte equal again at the prospective base. The16 frozen source/input/protocol/reference-test files remained unchanged after execution. The original candidate/auditor are called only on these new inputs; historical old fixtures are witness files, never run scripts.
- assay: `python -B assay.py`; UTC `2026-10-03T03:31:28.191838+00:00` to `2026-10-03T03:31:28.361457+00:00`; exit `0`; stdout SHA256 `b4c0f8238be52ffc5e6b014e11227a9fb2d6e74101c83182cdfa5ce6b96d569c` (98055 bytes); stderr 0 bytes.
- audit: `python -B audit.py raw.json`; UTC `2026-10-03T03:31:28.363458+00:00` to `2026-10-03T03:31:28.567793+00:00`; exit `0`; stdout SHA256 `565dc20cacfcf239839154974da1ce4aa5ba044fcca33a0a42a9d26927d68246` (2028 bytes); stderr 0 bytes.

Windows host, CPython3.11.9, stdlib only, one ownership thread, bounded path length8 and raw cap1 MiB; no GUI, container, GPU, model, simulated clock or physical actuator. The5 ordinary reference construction tests passed before freeze. Their tool transcript and exit status are retained, but exact start/end UTC was not recorded. Later delivery checks are separately identified and do not replace this first run.

## Interpretation and limits

At a known scheduled checkpoint, no delivered record is insufficient evidence of a fresh receipt. It may reflect an erasure, capture failure or incomplete logging; their physical causes are not distinguished. If no checkpoint was scheduled, a different schema/contract is needed. The stated count bound is a fixture assumption, not measured live channel-loss authority. All positions and slots are dimensionless model integers, with constant boundaries and one shared transition during hold/release.

No old seven-case PASS is reclassified, and no tube soundness, dynamic boundary, actual input release, application effect, real time performance, useful feedback, human tempo or #59 completion is established. The older T1 lack-of-bound/effect-oracle HOLD remains. The decision changed is the admissibility of implicit freshness at a due checkpoint: retain a first-class absence entry or refuse to infer a fresh delivery before any future live horizon use. A live implementation must establish scheduled deadlines and complete acquisition separately.

This source tree has no content votes or apply certificate; those belong to the PR record outside the tree. Integration requires fixed nonauthor content agreement and a later actual-main combined-tree check under FINAL-v5.

Delivery reader01 stopped before running checks because the existing checkout of the index checker had155 CRLF endings while its Git blob had LF. The normalized contents were identical. The original reader and checkout witness are retained, and reader02 materialized the exact pinned checker before continuing. No scientific source, raw, threshold or matrix was changed or rerun.

Final archive checks: six source/snapshot files compile without execution; pytest9.1.1 collects0 tests (expected exit5, not a test PASS). The existing sparse-aware index checker exits0. A separate complete Git-tree inventory verifies all604 retained directory entries plus this one report, sorted/unique with no missing/stale entries; this avoids interpreting sparse absence as removal. No prior producer/formal allocation or unrelated runtime suite was repeated.

The first staging diff check reported the captured CRLF audit.json lines as whitespace. All43 staged manifest entries already matched original bytes. A parent .gitattributes rule scoped to this archive audit.json preserves those bytes; the frozen local attribute file and other15 freeze pins are unchanged. Raw/audit data were not reformatted. The initial diagnostic and ordinary delivery repair are retained separately.
