# Issue #8493 T0 A01 — formal result

## Disposition

**PASS_METHOD_SCOPED.** On this frozen finite model, pooled confirmation accepted both planted harmful temporal-shift cases, while block-conditional confirmation rejected both. Stable controls passed, sparse support and an ambiguous transition returned `UNKNOWN`, and competing fingerprints remained distinct from the target. The independent audit reconstructed all 6,424 rows and rejected all six corruption controls.

This supports only the proposed confirmation-method distinction on the authored deterministic hash-oracle fixture. It is not evidence about real interface drift, live GUI reliability, a model, user outcomes, latency, cost, safety, or product utility.

## H / T / D / C / U

- **H:** The frozen pooled rule can hide harmful within-instance temporal blocks; requiring supported identified blocks to pass avoids that false assurance in the planted cases.
- **T:** The single frozen proposal removed only the optional `warmup` event from the #8152 trace. It retained reset, lease, release, event ordering, target/competitor fingerprints, shared exit code, and paired seed outcomes. Six schedules covered stable behavior, abrupt and gradual masked shifts, sparse support, transition ambiguity, and competing-fingerprint identity. The non-inferiority margin was 0.20, minimum block support 64, and family-wise alpha 0.05 across 20 fixed contrasts.
- **D:** `PASS_METHOD_SCOPED` required exact independent reconstruction, all six corruption rejections, pooled false assurance on at least one planted harmful case, blockwise rejection of that case, stable-control passage, required UNKNOWN dispositions, and competitor/target separation. All gates passed.
- **C:** Finite seed variation remains possible. Other schedules or a different change-point structure could alter these outcomes. The experiment does not compare randomized interleaving or worst-case bounds.
- **U:** The fixture is authored and deterministic. It does not establish that real traces drift, that their regime boundaries are observable, or that block review improves any live task or product measure. The diagnostic removal is not a full search-efficiency benchmark.

## Results

| Case | Pooled | Block conditional | Interpretation |
|---|---|---|---|
| `stable_no_shift` | PASS, delta −0.0313; interval [−0.0643, 0.0023] | PASS all blocks | Negative control passed. |
| `abrupt_shift_masked_pooled` | PASS, n=1,280; delta −0.1258; interval [−0.1582, −0.0919] | FAIL; late block n=256, delta −0.5742; interval [−0.6726, −0.4431] | Pooled false assurance observed. |
| `gradual_shift_masked_pooled` | PASS, n=1,792; delta −0.1016; interval [−0.1265, −0.0758] | FAIL; late block n=256, delta −0.5234; interval [−0.6243, −0.3928] | Pooled false assurance observed. |
| `sparse_late_block` | PASS, n=1,048; delta −0.0315; interval [−0.0528, −0.0098] | UNKNOWN: late block n=24, below support floor | Sparse data did not become a pass. |
| `ambiguous_transition_window` | PASS, n=1,280; delta −0.1008; interval [−0.1306, −0.0698] | UNKNOWN: transition window explicitly ambiguous | Ambiguity blocked blockwise confirmation. |
| `competing_fingerprint_no_shift` | PASS, n=512; delta −0.0332; interval [−0.0669, 0.0010] | PASS all blocks | 500 competitor rows were kept separate from target recurrence. |

The candidate generated 6,424 paired rows. The audit independently reconstructed 6,424/6,424, reported no errors, and rejected 6/6 controls: dropped row, temporal-window relabel, missing mandatory release, forged target fingerprint, accepted sparse block, and erased competing identity.

## Provenance and runtime

- Issue: [#8493](https://github.com/Unjuno/agent-interface/issues/8493), successor to #8152.
- Base main commit at freeze: `6ceb8552df13a188f6aad9cbfed88eba6eb70689`.
- Freeze commit: `6b7be8a8ada5412162d93131491c8748ab6d05db`.
- Freeze SHA-256: `387eba724dfd549dd2d4264ffc2e6add6e4dea6153f458aac68114da2a1ac50a`.
- Fixture SHA-256: `c935dcfb4c8d6d02ce3fa5c1cdfeae0273affa91b039565b20389e32320f5dde`.
- Formal candidate and auditor: one invocation each, zero retries, both exit 0; exact invocation record is in `results/RUN.json`.
- Runtime: host CPython 3.12.13, macOS 27.0.1 arm64. No container was used. OrbStack image inspection had returned a content-store `operation not supported` error before freeze; no pull or daemon restart was attempted. This result makes no container-transfer claim.
- Candidate raw SHA-256: `41590c50e615697f16225296b4234ecfd96d6b05cac4aef4ef1bbf6b192f16dc`.
- Independent audit SHA-256: `fe55490421f802e241269f62ba0f2f63ed7488b2c1a87ec367c0b0413af1a633`.

`results/SHA256SUMS` records the hashes of the retained formal outputs. Construction checks and their scope are recorded in `CONSTRUCTION.stdout.txt`; they are separate from this one-shot formal execution.
