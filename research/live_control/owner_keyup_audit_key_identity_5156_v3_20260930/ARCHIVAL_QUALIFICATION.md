# Archival qualification: logical-key audit correction

## Disposition and immutable origin

Preserve all 15 published files from [source PR #5553](https://github.com/Unjuno/agent-interface/pull/5553), head `f58c4169e66b88514f9441648379490405cca0e1`, directory tree `ac90c3166823808aeb1f4371d71ae5c8c90838c6`. Originals total 33,420 bytes and retain exact paths, 100644 modes, blobs, freezes, checksums, source, fixtures, and reports. This is a separate qualification, not a repair or reclassification of the original package.

No archived source, test, candidate, auditor, or mutation control was imported or executed during preservation. The historical result is attributed construction evidence; static byte checks do not independently authenticate the claimed environment, one-shot ordering, source mounting, process separation, or execution.

## What is retained

[REPORT.md](REPORT.md) records `PASS_KEY_IDENTITY_AUDIT_T0_SYNTHETIC_ONLY`: host CPython 3.14.5, eight focused tests, one deterministic runner, a distinct audit process, and ten rejected candidate controls on one three-row synthetic joined trace. [AUDIT.json](AUDIT.json) records PASS/errors=[] and RUN SHA-256 `80f341c9766cabbb1a22f5b2c92c4ce792917d672c58a4373766a5de50a39d3a`.

The package preserves four exact inputs from #5415/#5467. In particular, `upstream/retained_raw.json` is SHA-256 `56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2`. The older completeness-v2 auditor omits logical `key` from its identity tuple. The historical candidate records false acceptance when an explicit key changes and when an autonomous-cleanup null becomes a string; this is an audit-coverage limitation, not evidence that the original pristine producer raw was corrupt.

The added candidate compares keys by exact release ID and preserves null for cleanup. Its reported acceptance/rejection is limited to the frozen trace and ten controls. It neither retroactively repairs the [#5415 original](../owner_keyup_audit_completeness_5156_v2_20260930/ARCHIVAL_QUALIFICATION.md) nor the [#5467 synthetic join](../owner_keyup_audit_interop_5156_v1/ARCHIVAL_QUALIFICATION.md). Existing #5489/#5492 candidates remain separate source/result identities.

## Audit independence boundary

Static reading of `audit_raw_only.py` shows that the mutation schedule is reimplemented in a separate process, but the checker imports the same `audit_key_identity` candidate function and the unchanged upstream auditor. This is a replay/consistency check of those functions, not an independently implemented logical-key oracle or independent human review. Its historical PASS should not be broadened to producer authenticity, independent caller-nesting proof, live completeness, or general malformed-input coverage.

The report's ten-control denominator refers to the exact named schedule in FREEZE/RUN/code. Preserve original prose and its scope; do not infer additional tests from summary bullets or transfer counts from neighboring packages.

## Coverage and static verification

At inspected main `4cf0a3dfde1219671b671bf0a9079a11dcb2e159` on 2026-10-01, this original namespace was absent. Main already retains #5415/#5467 through #6072 and shared inputs in other logical-key packages. Shared input blobs are not complete retention of these 15 original paths.

The complete nontruncated source tree, all 15 reconstructed Git blobs, the four frozen input hashes, five candidate/plan hashes, and all 14 original SHA256SUMS entries matched. Inputs and retained JSON were inspected as data only. No scientific reproduction, host test run, container, X11, model, GPU, game, or input was performed.

## Owner and promotion boundary

This package establishes no owner runtime, exact release time, physical key state/occupancy, application consumption, MAP01/task effect, efficacy, safety, latency distribution, recovery benefit, or transfer claim. The [#5156 owner gate](https://github.com/Unjuno/agent-interface/issues/5156), [latest inspected live-bracket limitation](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5939309038), consumed allocations, and separate successors are unchanged.

Source PR #5553 was open/Draft at inspection. Qualified archival delivery does not dispose of the original PR/ref, clear its review gate, grant execution authority/resources, or authorize any rerun. Recheck live status before later publication or branch cleanup.
