# PR #7636 baseline release-sink sweep rescue

## H / T / D / C / U

- **H:** A frozen current-main owner backend loses per-position information when the telemetry sink fails before or after acceptance. The original A01 probe reports the exact observed rows for all three positions and both sink behaviors.
- **T:** Preserve the original README, probe, raw output, and checksum manifest byte-for-byte. Re-run only the checksum verification and a new strict parser over the saved raw output; do not rerun the candidate probe. Challenge the auditor with missing-prefix/suffix and duplicate-case mutations.
- **D:** The six retained rows show fail-before-accept positions absent, and accept-then-raise rows visible as complete but without `delivery_unknown`. The new raw-only auditor passes the original six cases and rejects the tested truncation/completeness mutations. All four original manifest entries verify.
- **C:** This is a deterministic stub-sink call-boundary result loaded from frozen commit `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6`; no X server, game, model, GUI, OS input, Docker, or live allocation was involved. Current main also has an Executor-level generic `delivery_unknown` terminal status; this old A01 did not exercise that wrapper and therefore does not contradict it.
- **U:** Durable sink/consumer reconciliation, terminal delivery of per-key custody, physical release, application receipt, and task effect remain untested. Implementation candidates and later repairs are separately reviewed in #7635 and related follow-ups; this archive does not integrate them.

## Auditor correction and provenance

The original `audit.py` is retained unchanged. Its checks were insufficient: a reviewer removed a non-failing suffix tuple from a temporary copy of `RAW_STDOUT.txt`, and the old auditor still returned `PASS_AUDIT`. The additive `audit_v2.py` checks the exact ordered three-position shape for all six cases. `test_audit_v2.py` exercises missing suffix, missing prefix, duplicate case, and wrong completeness controls against saved text only.

Source PR: [#7636](https://github.com/Unjuno/agent-interface/pull/7636), closed without source changes; exact source branch head `912c2bbd67ff7264f40a96b9ca6ebfc11e3a0386`. The predecessor candidate implementation was explicitly superseded by #7635. This rescue keeps the baseline raw evidence and records the auditor limitation without changing or upgrading its original result.
