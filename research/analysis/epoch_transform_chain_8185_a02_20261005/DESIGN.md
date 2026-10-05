# A02 construction design (not frozen; no allocation authorized)

Issue: [#8201](https://github.com/Unjuno/agent-interface/issues/8201), successor to [#8185](https://github.com/Unjuno/agent-interface/issues/8185).

This file is a design artifact only. It does not authorize WSLc, Docker/OrbStack, a candidate invocation, or an auditor invocation. The shared-runtime ownership/exclusive-lane gate recorded in #6389/#7970 is unresolved. Do not label any construction calculation here as a formal result.

## Preserved A01 audit findings

A01 remains unchanged on `research/8185-transform-graph-t0-20261005`, with its frozen raw files and reported `PASS_METHOD_SCOPED`. This successor addresses the following evidence gaps without rewriting A01:

- Its baseline returns REFUSE whenever a case has more than one edge, including five of eight valid-affine rows.
- Its `two_epoch_composition` edges all carry epoch 1.
- Its oracle truth file retains expected output points, not the hidden edge matrices; the formal auditor compares against authored point labels rather than independently composing the hidden transforms.
- Its formal run was host-only after the container image-inventory error, although project direction requires the host-designated isolated container rung and does not permit silent host substitution.

These are protocol/validity limitations, not evidence of a live GUI coordinate defect.

## H / T / D / C / U

**H.** On a frozen finite set of affine coordinate chains and bounded uncertainty regions, a typed, epoch-bound candidate will match an independent exact oracle with zero false admissions, refuse every stale/unmodeled control, and reduce false UNKNOWNs by at least 20% relative to a fair frozen last-known similarity baseline on valid composed-affine cases where the chain carries information the single similarity cannot represent.

**T.** Use three strictly separated inputs/roles:

1. **Candidate input:** public frame IDs, directed affine edges, source/target units, edge validity epochs, declared residual intervals/correlation IDs, presented point/uncertainty, intended input-frame hit region, forbidden regions, and target identity metadata. No oracle matrices, expected output, or truth labels.
2. **Oracle truth:** hidden exact edge matrices, validity transitions, true target/input-frame geometry, semantic target identity, and exact expected decision. An independent auditor composes the hidden affine matrices itself and maps the original point and original uncertainty-set vertices through the composite map. It must not import candidate code, call candidate helpers, or propagate a lossy intermediate AABB. Include an inverse-shear pair whose composite is identity; use literal rational/integer fixtures and hand-check expected points.
3. **Baseline state:** one last-known uniform scale plus x/y offset for each declared calibration epoch, with provenance, observation time/epoch, and explicit refresh events. A baseline refresh must be constructed from public calibration observations (for example, a frozen set of calibration anchors), never copied or derived per row from hidden oracle transforms. Between refreshes it carries the last-known mapping and refuses if invalidated/stale. It must be able to map a point through a multi-edge candidate case using its single similarity; it must not REFUSE solely because the candidate graph has multiple edges.

Define cases as a sequence, not disconnected rows, so the epoch test really traverses 7→8→9: an epoch-7 capture/presentation observation; a declared update to epoch 8; a second declared update to epoch 9; and admission at epoch 9. Include stable, translation, uniform-DPI, valid mixed-monitor update, the two-epoch composition, shared/common-mode error with same and different correlation identities, independent-error boundary, stale epoch, missing/reversed/duplicate edge, unit mismatch, DPI-context mismatch, target swap, non-affine reflow, hit-boundary crossing, and forbidden-region overlap.

Freeze the false-UNKNOWN denominator as the count of oracle-valid composed-affine cases, including any valid rows the baseline refuses. Report raw counts and rates for each stratum; do not cherry-pick a subset after seeing outputs. The baseline refresh rule and calibration-anchor values must be reviewed before input freeze.

**D.** PASS_METHOD_SCOPED only when each candidate decision and mapped value matches the independent oracle, false admissions are zero, all invalid controls are UNKNOWN/REFUSE, and false-UNKNOWN reduction is at least 20% on the frozen valid composed-affine denominator. Wrong-target/forbidden admission or stale-chain reuse is FAIL_UNSOUND. No reduction is FAIL_NO_INCREMENTAL_VALUE. Missing independent truth, incomplete epoch transitions, oracle/baseline leakage, or a runtime-gate failure before candidate invocation is HOLD/STOP (with candidate/auditor counts stated); never convert these to PASS. Preserve candidate/auditor first outputs; no retries or post-result repairs.

**C.** A simpler authoritative current mapping plus epoch invalidation may be sufficient. If the last-known similarity baseline matches the chain after legitimate updates, the graph adds no incremental value. Semantic grounding or application hit testing may dominate coordinate conversion.

**U.** Finite authored affine arithmetic only. No Windows DPI virtualization, OS/backend API, real hit testing, calibration distribution, latency, semantic effect, safety, or product-readiness claim.

## Execution and publication gate

Before freezing: reconcile current main, inspect all A02 branch/PR/issue collisions, obtain independent review of the baseline refresh and oracle construction, and document the exact current-host container plus resource/ownership checks. Windows uses the project-directed WSLc container; macOS uses the project-directed OrbStack container. If the shared lane is not explicitly released or the designated container cannot start, record a pre-candidate STOP and do not substitute host execution.

After a valid freeze: run construction tests first; then exactly one candidate command and one independent auditor command in the designated container with no network and only the intended read/write mounts. Preserve stdout/stderr/exit status, inputs, outputs, hashes, cgroup/swap caveats, and an independent post-run audit. Publish only by PR from this additive branch to then-current main.