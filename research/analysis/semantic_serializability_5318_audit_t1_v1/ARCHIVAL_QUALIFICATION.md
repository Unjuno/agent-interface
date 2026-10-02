# Archival qualification: auditor STOP and post-STOP construction

This is additive source-chain preservation for Issue #5957 and PR #5967. The three published head files remain byte-identical to `4acf5905222453b1b65990de3260382dd90eba22`; original attempted T1 source is preserved separately in its ancestor history.

## Two source phases, one unchanged T1 STOP

The original T1 attempted-source commit is `e49853b647e0f266b817908e160cf726af7adf8d`. The retained record says a single constrained Docker request returned no output for 25 seconds and the attached CLI was interrupted. No container exit code, output, or daemon-side execution state was confirmed. The disposition remains `STOP_DOCKER_CLI_UNRESPONSIVE`; do not infer that the container definitely did or did not start.

The next commits, `d681f5da587d25ac56c854ee3ca7a3f4b9daa89d` and `4acf5905222453b1b65990de3260382dd90eba22`, add post-STOP construction-only unknown-label rejection, mutation controls, malformed-input handling, tests, and explicit chronology. Their reported 9/9 host tests, 30-row host audit, and 5/5 rejected controls are historical construction evidence. They were not part of the interrupted T1 Docker request and do not constitute a T1 container PASS. This preservation review did not rerun those checks or import their source.

## Exact custody and ancestry

All three original head files were fetched as exact Git blob bytes and independently checked: 15,199 bytes total. Head `audit.py` has Git blob `e2cfe6ac0ecbab844bc130ecfebae73b0e651cea` and SHA-256 `479e1a365c94f6fd36963f2afcc633b9c26d9fc18b39f4183ee7a6b51817cda6`, matching the later T3 source identity.

The three distinct original T1 ancestor files were also independently byte-hashed: 9,127 bytes total. Original `audit.py` has Git blob `ab635af2aec05b1ba1b0c2ded902af4385bd5738` and SHA-256 `fbbeac100c7fea18d182b91514dfb626db11832861e705c57481bdf6d972da91`. [ORIGINAL_CUSTODY.json](ORIGINAL_CUSTODY.json) records both phases with explicit source commits. It inventories original evidence only; the manifest and this qualification are additive review material.

This existing PR must be integrated by a normal merge preserving `e49853b647e0f266b817908e160cf726af7adf8d` and both successor commits in main ancestry. A squash of only the published head would not preserve the attempted T1 source in main ancestry. Before calling integration complete, verify the actual main ancestry and read back every head and ancestor blob. This note itself makes no advance claim that a merge has happened.

The verification establishes present byte custody and source-phase separation. It does not add historical process attestation, independently reproduce host results, or determine the interrupted container's execution state.

## Chain and scope

- Parent [PR #5952](https://github.com/Unjuno/agent-interface/pull/5952), head `d356ed65ff9d16978caea56c1ddaf4008a7d171a`, retains the immutable 30-row raw and `STOP_INDEPENDENT_AUDITOR_ORACLE_MISMATCH`.
- Its raw SHA-256 is `26fa7c694fd0f3a35bc5085b6145af639e88c8dd79666c3284db12f11df9ed90`, Git blob `2725e3be1de2805787f1b384d1051111a69c9c91`. The recorded predecessor base `3d6ffc76d535309cf3820ed33cb9327354f03648` does not contain that path.
- T2 `STOP_INVOCATION_ENTRYPOINT` remains separate. T3 `PASS_RAW_AUDIT_T3_SCOPED` is retained by [PR #6292](https://github.com/Unjuno/agent-interface/pull/6292), merged at `1fe36fc1e7aa4c9f11db91570270a5b09e494b23`, with an additive [source-locator qualification](https://github.com/Unjuno/agent-interface/blob/1fe36fc1e7aa4c9f11db91570270a5b09e494b23/research/analysis/semantic_serializability_5318_audit_t3_20261002/PROVENANCE_QUALIFICATION.md). That later finite raw audit does not replace T0, T1, or T2 STOPs.

Only qualification, custody metadata, and navigation are added here. No candidate/auditor import or execution, Docker allocation, model, GUI, GPU, external effect, or raw #5618 access occurred. No original T1 or post-STOP head bytes were edited. Issues #5318, #5957, and #6290 remain open. Archive integration makes no runtime, real-effect, safety, Needle, GPU-benefit, or product claim.
