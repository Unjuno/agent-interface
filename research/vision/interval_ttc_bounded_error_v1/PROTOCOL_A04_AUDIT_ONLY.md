# Issue #8157 A04 audit-only protocol

## H — bounded hypothesis

The preserved A02 candidate outputs can be independently reconstructed from each public prefix alone, including earlier prefixes before future occlusion, and the original A02 auditor's 98 point/interval mismatches can be attributed exactly to the occlusion future-history check.

## T — one-shot audit allocation

Use only the byte-pinned A02 public observations, oracle labels, candidate JSONL, first audit report, frozen source/artifact manifests and the committed A03 STOP record. Reconstruct all point, interval and derived radius-change outputs from each public prefix only; independently join the hidden truth by sequence ID and timestamp; attribute every original A02 reconstruction mismatch by kind and profile; and perform five in-memory mutation controls (bound, timestamp, removed sample, oracle hazard label, and interval endpoint). Run this corrected A04 audit-only program once in a digest-pinned, network-disabled CPU container after freezing. Do not invoke A02 or A03 candidate, generator, or auditor programs.

## D — decision

- `PASS_RAW_RECONCILIATION_ONLY` only if current-A03 source/test/protocol hashes and original A02 manifests/raw hashes match; all 200 IDs and 2,400 prefixes reconstruct with no errors; each numeric interval on eligible in-model hazard prefixes contains its oracle TTC; the original A02 mismatches are exactly 49 point plus 49 interval mismatches, all in `occlusion`; all five mutations are rejected; and the A03 STOP is hash-bound.
- `FAIL_AUDIT_ONLY` if any frozen identity, raw reconstruction, oracle alignment, mismatch attribution or mutation check fails.
- A02's `FAIL_METHOD` and A03's `STOP_AUDITOR_RUNTIME_ERROR` remain unchanged. A04 cannot produce `PASS_METHOD_SCOPED`, change the TTC hypothesis outcome, or repair either prior allocation.

## C — alternatives

The A02 mismatches might be candidate errors or changed inputs rather than auditor future leakage. Independent prefix-local reconstruction plus the A02 source/artifact manifests and A03 STOP identity separate those possibilities. A04 only reconciles preserved bytes; it does not validate usefulness or the original threshold comparison.

## U — limits

One finite synthetic A02 bundle only. No new observations, candidate, generator, A02/A03 auditor, vision pipeline, GUI/game, input, runtime integration, user data, or safety claim.

## Allocation boundary

Current main and A02 head/source identities are frozen in `FREEZE_A04.json`. A03 remains an immutable consumed STOP with auditor count 1 and zero candidate/generator calls. A04 permits exactly one audit invocation, zero candidate/generator calls and zero retries; its output is isolated at `results/FORMAL_A04_AUDIT_ONLY/`.
