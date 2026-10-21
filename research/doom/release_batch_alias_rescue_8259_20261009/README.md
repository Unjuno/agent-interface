# Rescue record — PR #8259 release-batch alias cleanup evidence

## Provenance and extraction

Source PR #8259 was a draft on branch `research/59-release-batch-alias-cleanup-a01-20261007`, head `cf101f8f147d3505acd52597120be1246994f4bd`, against historical base `133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`. Its tree is not based on current main. A direct merge would carry thousands of unrelated historical deletions, so this rescue excludes the branch's broad tree changes and preserves only its 239 added evidence files: nine experiment packages and one measurement-publication custody record. Every rescued source file was byte-compared with the source-branch blob. The PR's old `research/README.md` edit was not copied; current indexes point to this qualification instead.

## H / T / D / C / U

**H.** The branch preserves a chain of candidate-only duplicate-keycode alias tests: a held key can make an alias batch reject, so the executor/owner cleanup path must release the already-held key. Separate first-outcome records include setup STOPs, harness STOPs, failed audit v1s, corrected read-only audits, and scoped fake-X/Xvfb results.

**T.** Preserve the nine package trees and the adjacent measurement-publication custody outputs exactly. Verify package manifests, frozen source/candidate/auditor digests, and the saved audit-to-raw digest bindings. Do not rerun any candidate or rewrite any first outcome.

**D.** Archival rescue is valid only if all 239 source additions are byte-identical, all declared package digests verify, and the saved outcomes retain their original status. This is an evidence-custody gate, not a new scientific experiment.

**C.** A06 reports `PASS_METHOD_SCOPED` for a fake-X executor composition. A10 reports `PASS_METHOD_SCOPED` under its separately frozen read-only audit v2 for one private Xvfb case. J6q8 A03 reports `PASS_METHOD_SCOPED_AUDIT_V2` after an explicit V4/V3/V12 owner close. A04/A05, A07/A08/A09, and J6q8 A01/A02 remain their recorded STOPs; J6q8 A03 audit v1 remains FAIL. The separate measurement-publication custody record preserves RED/interim-repair and mixed-suite limitations; the interim code is not promoted, and its later remediation is PR #8269.

**U.** These are synthetic fake-X/private-Xvfb construction boundaries, not a physical keyboard, application, GUI/game, task-effect, live threat-response, recovery-benefit, latency, or MAP01 result. Candidate runs were consumed and not repeated during rescue. Issue #59's integrated live gate remains unmet.

## Preserved packages

- [Executor fake-X A04/A05 STOPs and A06 scoped pass](../release_batch_alias_executor_cleanup_a06_20261007/REPORT.md), including the two predecessor STOP records.
- [Native-Xvfb executor A07/A08/A09 STOPs and A10 scoped pass](../release_batch_alias_native_executor_cleanup_a10_20261007/REPORT.md); earlier failures remain separate first outcomes.
- [Owner cleanup J6q8 A01/A02/A03 history](../release_batch_alias_owner_cleanup_j6q8_a03_20261007/REPORT.md), including the v1 audit failure and read-only v2 correction.
- [Measurement-publication failure custody A02](../../live_control/results/measurement_publish_custody_59_a02_20261007/REPORT.md), preserved as historical custody, not as the current remediation implementation.

## Rescue verification

The rescue branch reruns only repository-level index/hygiene checks and verifies serialized artifacts and hashes. It does not execute any candidate or mutate saved raw/audit outcomes. All preserved conclusions remain limited to their original snapshots and scopes.
