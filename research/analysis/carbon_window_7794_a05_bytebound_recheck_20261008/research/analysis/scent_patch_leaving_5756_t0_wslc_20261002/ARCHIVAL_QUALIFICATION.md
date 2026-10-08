# Archival qualification — PR #6412 patch-leaving STOP

This additive preservation note applies to the 15 original files at PR #6412 head `b837c29a20b5d8f998a6ab387d7a0d11b527ff05`, allocation `SCENT-PATCH-LEAVING-5756-20261002-01`. The originals are retained byte-for-byte, including the historical protocol, source, raw rows, auditor stdout, and `evidence/RESULT.md`. `ORIGINAL_SHA256SUMS` identifies every original file; it does not hash itself or this later qualification.

## Terminal disposition

**FAIL_METHOD / no scientific verdict. The allocation remains terminal, with no retry.** Preservation does not repair the candidate or auditor, endorse the policy comparison, or authorize another invocation. The historical candidate and separate auditor each ran once and exited 0; process exit 0 did not establish method validity. No candidate, auditor, construction test, container, GUI, model, or other research experiment was invoked to prepare this archival qualification.

Static review confirms the already disclosed failures: all three policy arms iterate the same fixed global leaf order; the patch-leave threshold does not change branch choice or stopping; `found` is assigned afterward from an oracle prefix; and policy labels drive arithmetic cost adjustments rather than different navigation actions. The candidate's `unsafe_transition` flag means an unsafe edge was encountered and excluded, while the auditor treats it as traversal. These defects invalidate the method independently of any apparent numerical advantage.

## Correction to the retained prose's held-out count label

The historical `evidence/RESULT.md` describes each policy as `36/60 found`. That label is inaccurate and remains unchanged as part of the original record. Direct parsing of the retained raw JSONL gives, for each of `fixed_depth_2`, `exhaust_branch`, and `patch_leave`:

- 60 held-out rows
- 48 rows with the stored `found=true`
- 36 rows with both `found=true` and `unsafe_transition=false`

The auditor's recorded 36/60 success count and means 117.16666666666667, 109.66666666666667, and 105.66666666666667 respectively are computed on the last, filtered subset. The difference is the 12 held-out unsafe-stratum rows per policy, whose flags the auditor interprets incorrectly. These are reconstructed stored-field counts, not validated target-finding or safety outcomes. Neither the 48/60 raw flag count nor the 36/60 filtered count supports a performance, safety, or hypothesis claim.

## Byte and scope verification

- All 15 original Git blob IDs were verified from exact base64-decoded GitHub bytes, and every original is listed in `ORIGINAL_SHA256SUMS`.
- All three source SHA-256 values in the original `FREEZE.json` match `protocol.md`, `candidate.py`, and `audit.py`.
- The raw artifact contains 360 unique `(graph_id, policy)` rows for 120 graph IDs and three policies. Its SHA-256 is `a6ec1d39254aa0f8a5070f9aeae7da87aa1d2a909d36cb4363ea1bb8fe0f7acc`, matching the retained candidate and auditor stdout.
- JSON parsing, static source inspection, and independent stored-row counting do not validate the defective method. Frozen source files were neither imported nor executed.
- The recorded WSLc memory/swap warning is preserved. A requested 1 GiB limit is not evidence of kernel-enforced isolation or a safety guarantee.

The earlier Issue #5756 / PR #5779 finite T0 is a separate allocation and is unchanged. Issue #5756 remains open. Any valid successor requires fresh authorization and prospective preregistration of genuinely different action policies, online target-observation stopping, explicit attempted/excluded/traversed events, an independent audit, and the applicable source/runtime/resource gates. No successor is created or authorized by this preservation-only change.
