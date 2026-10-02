# Issue #4824 successor construction-only probe

This is a new, non-formal diagnostic following Issue #4824's retained `HOLD_CONSTRUCTION_UNINFORMATIVE`. It does not edit or replace #4824's v1 FREEZE, STOP/HOLD history, or formal allocation. It uses three distinct construction seeds, with formal invocation count fixed at zero.

## H — hypothesis

Replacing eight sequential single-row rank-2 LoRA updates with four fixed batch-2 updates over the same eight support examples may produce a measurable bounded B correction while the frozen A behavior remains intact. This probe tests whether the previous recipe's no-learning outcome persists under the batch boundary; it is not evidence for general continual learning.

## T — treatment and provenance

- Allocation: `needle-online-correction-4824-batched-construction-v1`; branch `research/needle-online-correction-4824-batched-20260927`; additive path `research/system1/needle_online_correction_4824_batched_v1/`.
- Construction seeds: `6811701`, `6812701`, `6813701`, independently searched against GitHub Issues before use. These are not #4824 formal seeds `68117`, `68229`, `68341`.
- Same synthetic generator, 8→16→4 architecture, frozen-A 400-step AdamW base, support/data definition and held-out streams as the archived #4824 runner. Matched within each new seed.
- Control: eight one-row updates, one optimizer step per row. Treatment: four batch-2 updates, each using the next two fixed support rows. No tuning or extra update budget.
- Pinned image `needle-pilot05:local`, ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64 CPU; network none, read-only source/root, 1 CPU, 2 GiB, 64 PIDs, no-new-privileges. Dedicated output volume `needle-online-correction-4824-batched-construction-v1`; separate audit container read-only.
- Runner SHA-256 `A2064F69E802D8A3ACE6CEDAD4368EA59CF7AD9926432023298466BB0FDC415D`; auditor SHA-256 `A1843E24B8D538BFA45B78C0C0E62FE8EFA756FCC0B35CC97089F4F2104C85DE`.

## D — construction result

Both treatments retained held-out accuracy A=1.00 and B=0.50 at all 54 curve points. The factor initialized to zero did change after updates; it is incorrect to say the gradient path was inactive. Batch-2 consistently lowered retained B cross-entropy across all three seeds (6.88–6.96 initially to 5.51–5.87 after four updates), while held-out B accuracy did not cross a decision boundary. Single-row B cross-entropy changes were smaller/mixed. Construction disposition: `HOLD_NO_HELDOUT_ACQUISITION_AT_FROZEN_UPDATE_BUDGET`.

The initial audit's `PASS_CONSTRUCTION_AUDIT` label was withdrawn. It recomputed metrics from stored logits and checked regenerated input records and guard outputs, but the runner did not retain frozen base parameters; the auditor did not regenerate model logits from weights or replay optimizer updates. It therefore cannot independently establish prediction provenance or base immutability. Corrected disposition: `STOP_AUDIT_INCOMPLETE`; partial metric/log consistency has zero detected errors, but this is not an independent model-output audit. The missing raw tensors are not backfilled by rerunning consumed construction seeds. Raw JSON: 2,299,063 bytes, SHA-256 `9feb483c29c71191d519eb1be3842de44ead6e4df6c751defabd5fa40795af97`, matched exactly between dedicated Docker volume and local export.

## C — explanation / confounder

The right LoRA factor starts at zero, so its paired factor receives zero first-step gradient, but the right factor itself can still update through the nonzero left factor. It did update in the retained snapshots. Batch-2 reduced logged B cross-entropy without changing held-out argmax accuracy at this small fixed budget. Because model logits were not independently recomputed and base tensors were omitted from raw output, treat this as a trainer-reported construction signal with incomplete audit—not validated evidence of acquisition or retention. The tasks are synthetic and deliberately simple.

## U — limits and next gate

No formal allocation, no population inference, no real-time/live learning, no GUI/task transfer, no validated retention/acquisition or action authority. Preserve this run and #4824 v1 unchanged. A future diagnostic should retain all base/adapter/optimizer tensors, independently regenerate model logits and replay updates, and record each held-out target before any scientific disposition. Do not rerun these construction seeds. Other agents' separate frontier study #4829 uses a distinct opposing-label question and fresh allocation; this log is not pooled with it.

