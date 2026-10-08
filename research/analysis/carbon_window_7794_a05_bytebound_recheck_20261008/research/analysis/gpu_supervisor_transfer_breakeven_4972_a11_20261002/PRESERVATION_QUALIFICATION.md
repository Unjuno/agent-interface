# A11 incomplete-archive preservation qualification

This note accompanies PR #6452 at original head `fff55c6658144ecf65cad62140ccac9f479d29d8`. All 24 original files, manifests, construction FAIL/PASS records and append-only provenance erratum remain unchanged.

## Controlling terminal outcome

A11 remains `STOP_BEFORE_CANDIDATE_FREEZE_PROVENANCE_MISMATCH_AND_MAIN_ADVANCED`, candidate=0, CUDA=0, formal auditor=0, retries=0. Committed/preregistered base `eacb1346866f660d9d34eb36cd9691fd8184e5ff` differs from the locally reported freeze `b0c1f12285fbbd2d4335999e727dc3211b55139d`; gate-observed main `ddc3a7771f409889fbde87d7da01944cd1a08b0f` matches neither. The original [owner erratum](https://github.com/Unjuno/agent-interface/issues/5882#issuecomment-5944800750) and terminal_stop_02/PROVENANCE_ERRATUM.md remain controlling. No timing, crossover or formal audit PASS exists.

## Declared-identity limits

CONSTRUCTION_FAILURES.md records the attempt-01 log digest as `326985c0c3da9e32cc2ab59f466791806c2764e1341327f5697b59beab3342249` (65 hexadecimal characters). The root SHA256SUMS instead records `326985c0c3da9e32cc2ab59f466791806c2764e1341327f5697b59bea3342249` (64). The declarations conflict; neither was recomputed or certified by this review.

The declared full image ID `048a0de5d432205f9d92a9dfd36f4cab1cd82dfbd1042ce2c51bd94f7e45d32` has 63 hexadecimal characters. It appears in FREEZE, construction/result provenance and terminal gate notes. The raw start stdout's abbreviated `048a0de5d432` cannot resolve the full-ID defect. Keep the distinct manifest/image-reference digest and all original declarations unchanged; do not infer a corrected identity.

## Construction and formal coverage

PREREGISTRATION requires six formal result-corruption controls. The frozen audit.py main defines five, omitting wrong_image_ref; only the construction harness includes that sixth control. Its reported construction 6/6 does not establish six-control coverage in the unexecuted formal entrypoint.

The construction source-mutation controls create placeholder `frozen runner` and `frozen prepare` files, then mutate those placeholders. This tests hash-guard behavior, not mutation coverage of the actual frozen program bytes. Original construction FAIL and later PASS remain separately recorded and neither repairs the consumed terminal STOP.

## Incomplete receipts

Attempt 01 includes its combined log but no separate preserved provenance/exit file or original source snapshot in this package; the 1,0,0 exit tuple is prose, whose path points to an outputs directory rather than the committed construction_attempts/01 path. The local b0c1 freeze variant and start-gate script/argv are also absent. Their existence/behavior is described by retained observations and the erratum, not independently reproduced here. The erratum is not listed in either original checksum manifest.

README, WSL runtime notes and run commands retain historical preparation wording. Read them through the terminal erratum; they do not authorize retry, re-freeze, a replacement window or resource actions. This review performed static inspection only: no candidate, auditor, test, container, GPU or hash recomputation. No checksum, image ID, missing receipt or scientific outcome was repaired or fabricated.
