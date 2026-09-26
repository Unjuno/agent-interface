# #4045 — binary32 observation validity boundary

**PASS_ROUNDING_PREIMAGE_BOUNDARY_SCOPED. Research evidence only.** The two point policies fail the newly specified pre-conversion contract in directed cases. The old binary32 contract and earlier learned-model quality FAILs remain unchanged.

## Method and chronology

See PLAN.md for H/T/D/C/U and PROOF.md for the complete conditional enclosure proof, impossibility argument, Japanese variable meanings, units and limits. Ten construction tests passed. A built-in-module environment collector assumption failed before formal; CONSTRUCTION.md preserves it. No formal data were produced by that failure.

Public hash freeze560304050dfec4acc9ee3ac1f3788eae64a8098a and Issue4045 were created before the sole allocation. Full source files were locally hash-frozen, not all public before measurement. Two fresh CPU subprocesses evaluated the same158 source vectors by direct-to-float32 and float64-then-float32 conversion. One formal orchestration, two zero worker exits, outer exit0, no retries/replacements/tuning. The fixed RIGHT proposal is diagnostic; no learned inference or optimizer ran.

## Result (per conversion path)

| Quantity | Direct32 | Via64 |
|---|---:|---:|
| Source vectors |158|158|
| Originally valid / invalid |81 /77|81 /77|
| Legacy32 permits invalid source |11|11|
| Rounded value promoted to64 permits invalid source |7|7|
| Interval candidate permits invalid source |0|0|
| Interval candidate permits valid source |66|66|
| Interval candidate refuses valid boundary source |15|15|
| Mixed-validity bit patterns |6|6|
| Stable valid/invalid controls correct |8/8|8/8|

Paired outputs were byte-equivalent at row level. These are316 source/mode rows and948 decisions, NOT316 independent processes or sampled reliability trials. The77 invalid values are a deliberately concentrated boundary set, not a deployment distribution.

Example: velocity0.3499999865889549 (valid) and0.3500000014901161 (invalid under exact7/20) both become binary32 bits3eb33333, decoded as0.3499999940395355. The old rounded-threshold predicate and a binary64 comparison of that already rounded number both permit it. No deterministic function of those same bits can separate the two sources. The candidate refuses the ambiguous rounding cell; this also refuses its valid member.

Analogous paired witnesses exist for signed position, signed velocity, age and scope. Full source hex, actual result bits and all witnesses are in INPUT.json and AUDIT.json. Exact rational thresholds are a NEW upstream specification; they are not silently retrofitted into the predecessor.

## Independent verification

The frozen stdlib auditor imports no Torch/candidate/predecessor/study. It decodes binary32 bits as rational values, independently performs rational nearest/ties-even rounding, checks every source against its actual rounding cell, reconstructs the two point predicates, and evaluates all16 box corners for the candidate. It also verifies source/input hashes, complete ordered rows, process exits, diagnostic clock order, authority and no-training flags.

Audit: zero errors; ten semantic corruptions rejected. Raw checksums:
- DIRECT32 stdout:487b0e1f0d643fd50537c0f6b244289b61e7ac75bc2a9f02c18f6d5ea93ef435
- VIA64 stdout:9d069eefb5c143332579851786df9b102de1de578191843628b18c819e43784a
- AUDIT.json:0347d91365a47e4d9d0a805766258ac810e7a471fc15b3ce66930c4cceb5a786

Separate implementation/process by the same author is not independent human review. No claims about independent reconstruction of training trajectories are relevant: there was no training or learned-model evaluation.

## Environment and limits

Provided Linux6.18.44 x86_64 container; CPython3.13.5, PyTorch2.10.0+cpu, guest Intel Xeon Platinum8573C, Torch CPU float32 default, intra/inter-op1 and deterministic algorithms. Full binary hashes/configuration in ENVIRONMENT.json. Docker CLI/image identity unavailable: not Docker/OrbStack replication. No experimental network, installation, GUI/input, provider/model, shared-runtime mutation or performance benchmark. CPU frequency is not controlled; no timing benefit is inferred.

Conditional scope: correctly rounded binary64-to-binary32 under nearest/ties-even, unchanged supported finite values and no prior measurement error. No source authentication, observation freshness, actual sensor calibration, action authority, physical safety or integrated task benefit is established. Earlier data loss cannot be repaired merely by widening storage precision. Complete-cell refusal is conservative, not universally optimal.

## Adoption decision and stop

Do not promote either point predicate as a guard of arbitrary pre-conversion observations. First establish the actual interface's source semantics. If validity is defined after conversion, the earlier binary32 contract remains coherent. If pre-conversion validity is required, preserve source precision/validation evidence or use a correctly derived uncertainty enclosure; do not tune an epsilon after seeing these cases.

This finite contract question is complete. #3442/#3458/global ROADMAP are not closed. No new learned-model allocation or production default is justified by this result. Publication/check/merge state must be verified separately and is not inferred from the scientific PASS. Only candidate source, prior report/proof and relevant provenance are retained from the preceding chat-local study; its full8.5MB ZIP/raw remains a conversation artifact and is not represented as fully uploaded here.
