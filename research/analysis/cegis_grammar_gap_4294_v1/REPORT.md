# CEGIS grammar-gap detection — Issue #4294 formal result

Allocation: `cegis-grammar-gap-4294-20260923-01`

Disposition: **PASS_CEGIS_GRAMMAR_GAP_DETECTION_SCOPED**

## Result

One prospectively source-frozen formal invocation completed. Formal reruns/replacements/exclusions/tuning = 0.

- incomplete BLIND_BUDGETED_CEGIS: `UNSAT_NO_DIAGNOSIS`, round 2;
- incomplete ALIAS_AWARE_CEGIS: `GRAMMAR_INSUFFICIENT`, round 2;
- exact conflicting retained IDs: `[3,35]`;
- grammar-visible feature vector: `[1,1,0,0,0]`;
- required oracle outputs: `YIELD` versus `ACT_PRIMARY`;
- alias-aware executable candidate after diagnosis: none;
- complete-control BLIND: `COMPLETE`, round 5;
- complete-control ALIAS_AWARE: `COMPLETE`, round 5;
- complete-control nuisance-shift held-out: 64/64 for both;
- independent raw-only audit: 677 checks, errors=[];
- copied-evidence corruption controls: 13/13 rejected;
- authority grants: 0;
- formal raw SHA-256: `198f1df0c6399afb9728051f2d821cdfc299179a03ba1c0f76b14f69dbf4985e`.

The incomplete grammar cannot distinguish states 3 and 35 because they differ only in the oracle-only `approval_token`, which is absent from its declared feature grammar. The alias-aware loop retains both counterexamples and stops fail-closed rather than inventing an exception, dropping evidence, or emitting an executable skill. The matched complete-control grammar adds exactly one preregistered approval-aware PRIMARY template and remains synthesizable, so the detector does not label every hard verifier set as insufficient.

## H/T/D/C/U

- **H:** accumulated counterexamples can expose irreducible observational aliasing under an insufficient grammar; synthesis should stop fail-closed.
- **T:** deterministic stdlib finite fixture, 64 exhaustive semantic verifier states plus 64 nuisance-only held-out copies; incomplete versus matched complete-control grammar; BLIND versus ALIAS_AWARE CEGIS; max 6 rounds/rules; no GUI/model/provider/input.
- **D:** exact alias diagnosed within round 2, no executable post-diagnosis candidate, complete control reaches exact contract in round 5, held-out 64/64, audit and 13/13 corruptions pass.
- **C:** the missing dependency is authored and exact. This detects a representation gap; it does not infer or name a missing predicate automatically.
- **U:** no live skill authority, automatic predicate invention, model-generated code, GUI transfer, token/latency benefit or production synthesis claim.

## Retained construction/publication failures

Construction attempt01 is retained. Its held-out split accidentally introduced new semantic combinations and therefore mixed grammar completeness with generalization. Before source freeze, held-out was changed to nuisance-only duplicates of all 64 verifier semantic states; attempt02 then passed 6/6 plus py_compile.

Issue creation also created an accidental empty branch `research/cegis-grammar-gap-undefined-20260923`; it remains unused and content-identical to its base. A later preformal publication mistake placed #4284 result blobs on `research/cegis-grammar-gap-4294-20260923`; formal invocation was still 0. That branch is retained as `STOP_WRONG_PUBLICATION_PAYLOAD_PRE_FORMAL`. The actual allocation used the clean current-main branch `research/cegis-grammar-gap-4294-clean-20260923`, whose PLAN/FREEZE/source bundle was Git-read back before formal authorization.

The formal runner, independent audit and corruption controls each exited 0. The outer execution environment printed `TERM environment variable not set` after retained outputs were written; this envelope incident did not trigger a scientific rerun.

Postformal result-bundle publication initially contained incorrect `git_blob` metadata because local blob IDs were calculated without each chunk's trailing newline. All chunk SHA-256 content hashes matched; only the manifest metadata was corrected. Formal/raw bytes are unchanged.

## Evidence

Preformal source archive SHA-256:
`a4d1d0ebd35f07cbe947c31ebc190f7003c9dd0c2f0b8ad01bb08c251c6d4eb5`

Lossless result archive SHA-256:
`552da6777eb9864fb86f02f91300814d7de61058fd5958de19206579482866d1`

The result archive contains the exact full report, raw formal JSON, first audit/controls, execution receipt, outer incident and local publication check. `unpack_result.py` validates the archive SHA before extraction.

## Integration meaning

This scoped PASS supports one fail-closed rule for bounded skill synthesis: when retained counterexamples demand different outputs for the same declared feature vector, stop and request a representation/grammar change rather than continuing repair as if the current grammar were adequate. It does not establish how a model should discover the missing semantic predicate.
