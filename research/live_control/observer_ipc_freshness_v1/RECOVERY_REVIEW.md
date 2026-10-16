# #3944 historical construction STOP recovery review (2026-09-28)

This publication preserves the four files from the 2026-09-22 branch byte-for-byte. It is an archival STOP record, not a formal experiment, source-complete publication, or current acceptance of the broader #2117 hypothesis.

## Evidence boundary

- The predecessor records `STOP_PREFORMAL_PUBLICATION_BLOCKED`, scientific outcome NONE, formal invocations 0 and short-pulse cases 0. The retained construction/static IPC and synthetic auditor controls must not be relabeled as formal observations.
- It records four static pixel-count checks, clock-enclosure and static-pipe checks, cleanup, and 11/11 synthetic mutation controls. These are construction evidence only.
- The complete runner/auditor/native binary, local freeze and construction archive are referenced as a conversation artifact (21,678 bytes, SHA-256 `2cc82cd907b4a195a07317a403022c569c00ecf1d6dca3637eed183d36f82419`). They are not present in the predecessor Git branch or current recovery workspace. Therefore this PR does not claim source-complete or independently reproducible delivery.
- The same scientific line later recorded r2 `STOP_OUTER_EXECUTION_TIMEOUT_NO_CHECKPOINT` (formal rows 0/40), then r3 `40/40` with scientific scorer `PASS_CAPTURE_AND_DELIVERY_SCOPED` but overall `HOLD_FROZEN_AUDITOR_CONTROL_GAP` (10/11 frozen mutations; `boolean_block` accepted because `False == 0`). The later posthoc read-only audit rejected 11/11 but did not upgrade the frozen overall HOLD. Those later outcomes remain separate, unchanged Issue records and are not pooled with this construction STOP.

## H/T/D/C/U

**H:** Process separation may change short-capture and IPC-delivery behavior under consumer-thread load. This predecessor contains no formal evidence for that hypothesis.

**T:** Historical construction only: static 0/511/512/1024-pixel cases, static pipe observations, and synthetic auditor controls. Planned 40-case short-pulse allocation was not invoked.

**D:** `STOP_PREFORMAL_PUBLICATION_BLOCKED`; science NONE. Later same-line r3 remains on overall HOLD as described above.

**C:** The actual measured scope is static construction and synthetic checks. No inference about short-pulse capture, useful delivery, model consumption or integrated task effect.

**U:** The missing conversation artifact prevents exact source/freeze reconstruction from this branch. No source hash alone substitutes for bytes; no rerun, pooling, or runtime promotion.

## Integration

This additive recovery exists to preserve chronology and construction provenance on current main. It does not complete Issue #3944/#2117 or repository ROADMAP. Retain the distinction between the predecessor STOP and later r2/r3 allocations.
