# Archival qualification: Issue #4658 / source PR #4674

## Preservation disposition

This is a **partial, preservation-only archive** of the 17 files already published under `research/system1/needle_concurrent_online_lora_4658_v3/` at source head `fe5ef0fee432b049fd2b19158ff2a8b5d3f530c2` (51,439 bytes; original subtree `d8a471c74a6ec05aa36bb42c47bb775a7a12f382`). All 17 original blobs, including defective identity statements and the committed audit's trailing CRLF, remain byte-for-byte unchanged. This qualification is the sole new file in the experiment namespace.

The historical disposition remains **`HOLD_LATENCY_BUDGET`**. It is not upgraded to PASS, reproduced, or certified by this archive. Preservation does not resolve the missing raw evidence or the frozen auditor/provenance defects. Source [PR #4674](https://github.com/Unjuno/agent-interface/pull/4674) remains open Draft; its branch `research/needle-concurrent-online-lora-4658-v3-20260927` is retained; owner [Issue #4658](https://github.com/Unjuno/agent-interface/issues/4658) remains open. The original PR body's `Closes #4658` wording is a retained historical statement, not an instruction to close the issue through an archival PR.

This qualification follows the [latest HOLD disposition](https://github.com/Unjuno/agent-interface/pull/4674#issuecomment-5916066986) and the owner's [validation/provenance follow-up](https://github.com/Unjuno/agent-interface/issues/4658#issuecomment-5851757552). This preparation made no remote changes and grants no merge readiness, execution, retraining, rerun, allocation, runtime/action authority, or promotion.

## What the retained report says

The frozen report records one synthetic, three-seed, single-host CPU Docker run, a separate raw-only auditor with zero reported errors, and COW overlaps of 8/120, 9/120, and 8/120. It reports COW inference p95 values of 0.710754, 0.380752, and 0.341823 ms for seeds 99771, 99883, and 99991, respectively. The reported absolute scheduled 60-Hz deadline misses are 3, 0, and 0. Thus its overlap and p95 gates were met, but its zero-deadline-miss gate was not. Shared-live is diagnostic only and cannot qualify; no COW candidate qualified.

These are historical statements copied from the preserved report and audit, not measurements or recomputation performed for this archive. The reported 360 exact COW-logit recomputations and 9/9 pre-freeze construction checks were likewise not reproduced here. Reading bytes, parsing retained JSON, and calculating file identities do not constitute an independent raw-data audit.

## Unresolved identity and implementation defects

1. **Freeze/sidecar mismatch.** The committed `FREEZE.json` is 2,447 bytes with actual SHA-256 `45eb43e04587fa882aef9728e916a8ec43b06f255ede841a4ac1d7e8a32b95ca`. `FREEZE.sha256` instead records `4aca60ffb00fb35b9c64edc04982051d09054ae34fb635ca9a70198f6c53553d`; the latter is also repeated in result/invocation/evidence metadata. Both identities remain recorded as found. The six source-file SHA-256 entries inside the published freeze match those six preserved published files, which does not cure the freeze/sidecar mismatch or prove what bytes were used in the historical run. See [review](https://github.com/Unjuno/agent-interface/pull/4674#discussion_r4113762108).

2. **Committed/local audit difference.** Published `AUDIT.json` is 3,901 bytes with SHA-256 `2380d7f9b6755b952247a8b74d556f6ec3f9927035177e7747b39c9ec035eb23`, including the extra terminal CRLF. The manifest and owner instead identify a local `audit/AUDIT.json` of 3,899 bytes with SHA-256 `2ace9f2033b394e263ddc0df2561f2e489fb588f72bb7702a0add502a3df8085`. The committed copy is preserved exactly; the exact local artifact was not obtained or substituted. See [review](https://github.com/Unjuno/agent-interface/pull/4674#discussion_r4113762115).

3. **Timestamp-derived gates are not enforced by the frozen auditor.** `audit.py` takes supplied `latency_ns` and `deadline_miss` directly into its p95/zero-miss gates rather than validating `end_ns - start_ns` and `end_ns > deadline_ns`. The owner reports that separate local recalculation corroborated all 360 COW latencies and miss counts 3/0/0; that local corroboration is not repository-reproducible from these 17 files and was not repeated here. The preserved zero-error audit therefore does not establish independent timestamp-gate validation. See [review](https://github.com/Unjuno/agent-interface/pull/4674#discussion_r4113762113).

4. **Broken, reportedly unused formal wrapper.** Static source inspection preserves the review's finding that `formal.py --formal` rejects the freeze checksum, and, even if that were corrected, its trainer reuses the `construction_io` mount while the auditor reads the distinct top-level `training` directory. No repair or execution was attempted. `FORMAL_INVOCATION.json` and the owner say the original trainer and auditor used direct separate Docker commands and did not invoke this formal wrapper; that is a retained historical account, not independently verified execution. See [review](https://github.com/Unjuno/agent-interface/pull/4674#discussion_r4113762112).

5. **Additional invocation-record limitation.** The two command arrays in `FORMAL_INVOCATION.json` contain the shorter image token `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e`, while the surrounding metadata declares the full image ID ending `64562a85fd4a10e`. These strings were preserved as found. They are not expanded into a purportedly exact executable command, and no inference about the historical container identity is certified from that textual discrepancy.

## Missing evidence and recovery boundary

The preserved `EVIDENCE_MANIFEST.json` lists nine `training/seed_*.json` files totaling **37,104,581 bytes** and the separate exact local audit described above. Those nine training files and that local audit are not included in this published package or this preservation packet. Declared byte counts and hashes are an inventory, not proof that the absent bytes are available or valid.

The original **16,671,866-byte** `EVIDENCE_BUNDLE.zip` remains described as local-only. Its declared SHA-256 is `ae1c157871731805518a8e72e12d378dfbafb39db8890482f8094125acd7cd0f`, taken from the preserved evidence manifest and report. No ZIP, missing raw file, or exact local audit was fetched, recovered, generated, uploaded, or examined for this archive. Exact recovery is **unresolved**, not established to be impossible. A clean checkout of the published package cannot reproduce the original raw-only result. This partial preservation does not meet the latest HOLD's requested exact-archive recovery and additive independent timestamp-derived audit.

Any separately authorized future recovery must retain the originals, verify exact recovered bytes against their declared identities, and record corrections or additional audits additively. It must not silently normalize line endings, edit the freeze/sidecar, reconstruct raw files, replace the published audit, rerun the frozen experiment, or retune/reinterpret its result. This packet authorizes none of those actions.

## Ownership, lineage, and navigation

Issue #4658's body and [allocation comment](https://github.com/Unjuno/agent-interface/issues/4658#issuecomment-5851716907) own this v3 path and branch. They identify #4658 as the successor to #4653, with #4631 earlier in the lineage. The latest HOLD's phrase “successor Issue #4653” conflicts with that recorded lineage; it is not treated here as an ownership transfer or authorization for a new experiment. Historical predecessor outcomes remain separate and unchanged.

The original PR also changes shared `research/system1/README.md`. That old shared-index edit is excluded from preservation. If an archival integration is independently approved, add only a fresh minimal navigation entry pointing here against the then-current index. Do not import the old shared README, propagate its original “pending” description, or imply that the evidence gap has closed.

Scope remains a tiny synthetic component on three seeds and one host/image. This archive establishes no real Astra-feedback benefit, task utility, GUI semantics, large-model interference result, cross-hardware/production latency guarantee, execution safety, or runtime promotion.
