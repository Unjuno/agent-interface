# Issue #8157 A06: independent retained-raw score audit

## Status and boundary

This is a read-only, posthoc diagnostic on the exact A02 public observations, oracle sidecar, and candidate output already reconciled by A04. It is a new independent scoring implementation after A05 stopped before reading input. It is not a retry of the A05 program, not a candidate/generator/auditor rerun, and not a new sample. A02 remains `FAIL_METHOD` with its scientific comparison formally unscorable; A03 STOP and A04 `PASS_RAW_RECONCILIATION_ONLY` remain unchanged.

## H / T / D / C / U

**H.** Independently reconstructing and applying A02's frozen calibration/evaluation score rules to the retained bytes may yield a bounded diagnostic about whether its TTC methods showed an incremental signal.

**T.** Before the single audit invocation, freeze this protocol, a new scorer that does not import any A02/A04/A05 Python source, the exact A02 artifact SHA-256 values from `FREEZE_A04.json`, and the exact A04 report digest. Verify source and artifact hashes. From the public histories, recompute every candidate point estimate and interval one prefix at a time. Independently rebuild each method's largest zero-false-YIELD calibration threshold (using calibration controls only), then compute per-profile evaluation false-YIELD counts, eligible-hazard yields, interval coverage/containment, and paired lead loss. Retain the complete per-profile report. Read only; do not modify inputs or execute any candidate, generator, or prior auditor.

The single scoring process runs once with native macOS CPython standard library (`-I -S -B`), network unused, no container, model, GUI, user data, input authority, or shared runtime. This host-only audit is explicitly not container evidence. It uses the already published immutable bytes and no shared compute service.

**D.** `NO_INCREMENTAL_VALUE_SIGNAL_ON_RETAINED_A02_RAW` only if the A04 prerequisite and all input hashes match; all 2,400 estimates reconstruct exactly within the frozen 1e-10 tolerance; interval coverage is at least 50% in each eligible profile; all eligible oracle TTCs are contained; and the frozen A02 improvement or hazard-yield conditions are not met. Otherwise report `MIXED_OR_INCOMPLETE_DIAGNOSTIC`. Any provenance/reconstruction failure is a diagnostic integrity failure. No A06 outcome changes A02's formal disposition or can be promoted to a method PASS/FAIL.

**C.** The diagnostic reuses A02's finite authored sample and candidate outputs; it is not replication. A04 independently reconciled candidate output bytes but did not score calibration/evaluation decisions. Posthoc scoring can describe these exact retained rows but cannot cure the original formal audit failure.

**U.** Synthetic finite-method evidence only. No real visual pipeline, scene semantics, GUI/game, task effect, runtime policy, or safety inference follows.

## Frozen identities and stop rule

- Base: current `main` at freeze; the original A02/A04 source identities remain as recorded in their frozen manifests.
- Inputs: exact `public.jsonl`, `oracle.jsonl`, and `candidate.jsonl` hashes in `FREEZE_A04.json`; exact `AUDIT_REPORT.json` hash and `PASS_RAW_RECONCILIATION_ONLY` disposition.
- Allocation: `interval-ttc-posthoc-independent-score-a06-20261007`.
- One audit invocation; zero retries. Any nonzero exit, hash mismatch, or interruption is the retained first outcome. No corrected rerun under A06.
- The original A05 STOP and its unverified cleanup state are unchanged. No WSLc/OrbStack/Docker command or inventory is issued by this audit.
