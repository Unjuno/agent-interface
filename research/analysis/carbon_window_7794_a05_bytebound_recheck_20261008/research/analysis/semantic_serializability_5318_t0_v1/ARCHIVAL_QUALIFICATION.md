# Archival qualification: parent semantic-serializability STOP

This is additive source-chain preservation for Issue #5318 and PR #5952. It does not edit, rerun, or promote the historical allocation. The nine original files remain byte-identical to published head `d356ed65ff9d16978caea56c1ddaf4008a7d171a`.

## Retained disposition and verification boundary

The original result remains `STOP_INDEPENDENT_AUDITOR_ORACLE_MISMATCH`. Its retained record reports one candidate Docker invocation, exit 0, followed by one independent-auditor invocation with five `unknown_overlap` reconstruction errors. The original auditor's omission of the `left-zero` guard explains the recorded discrepancy, but that diagnosis does not adjudicate the parent hypothesis or convert its STOP into a PASS.

Read-only custody verification fetched all nine original Git blobs, independently reconstructed each Git blob ID, and computed SHA-256 over the exact bytes. Total: 40,893 bytes. All four `FREEZE.json` source hashes match their retained files. `RAW.jsonl` is 19,391 bytes with 30 JSON lines and 30 distinct scenario/policy pairs; its SHA-256 is `26fa7c694fd0f3a35bc5085b6145af639e88c8dd79666c3284db12f11df9ed90`. `AUDIT.json` retains the five failed reconstruction entries and the same raw digest. These checks establish present byte custody and declared-hash consistency, not independent reproduction of historical Docker execution, process exit status, resource isolation, or the construction-test claim.

[ORIGINAL_CUSTODY.json](ORIGINAL_CUSTODY.json) records the current preservation manifest: source commit, original paths, byte counts, Git blobs, and independent SHA-256 values. It inventories original evidence only; this qualification and the manifest itself are additive review material.

## Source-chain distinction

- Parent T0: this unchanged nine-file record and its consumed allocation remain STOP.
- Original audit-only T1: [PR #5967](https://github.com/Unjuno/agent-interface/pull/5967), attempted-source commit `e49853b647e0f266b817908e160cf726af7adf8d`, remains `STOP_DOCKER_CLI_UNRESPONSIVE`. No definite daemon/container start or exit can be inferred from the interrupted CLI.
- Later #5967 head `4acf5905222453b1b65990de3260382dd90eba22` contains explicitly post-STOP host construction controls, separate from the attempted T1 source.
- T2 remains `STOP_INVOCATION_ENTRYPOINT`. Qualified T3 was preserved separately by [PR #6292](https://github.com/Unjuno/agent-interface/pull/6292), merged at `1fe36fc1e7aa4c9f11db91570270a5b09e494b23`; its `PASS_RAW_AUDIT_T3_SCOPED` does not replace any predecessor STOP.

The T3 [source-locator qualification](https://github.com/Unjuno/agent-interface/blob/1fe36fc1e7aa4c9f11db91570270a5b09e494b23/research/analysis/semantic_serializability_5318_audit_t3_20261002/PROVENANCE_QUALIFICATION.md) distinguishes predecessor frozen base `3d6ffc76d535309cf3820ed33cb9327354f03648`, which lacks the raw path, from the actual raw-containing published head above. The raw Git blob is `2725e3be1de2805787f1b384d1051111a69c9c91`. The original base field remains unchanged.

## Preservation boundary

Only this qualification, its custody manifest, and a navigation entry are added. The candidate, original auditor, raw, failed audit, freeze, plan, tests, and attempt history remain unchanged. No candidate/auditor import or execution, Docker allocation, model, GUI, GPU, external effect, or raw #5618 access was performed for this preservation. Archive integration is not scientific promotion. Issues #5318, #5957, and #6290 remain open. No runtime, real-effect, safety, Needle, GPU-benefit, or product claim follows from this finite synthetic record.
