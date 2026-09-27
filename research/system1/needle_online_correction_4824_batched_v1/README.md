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

Both treatments ended at A=1.00 and B=0.50 for all three seeds. Every point in all 54 curves was invariant at A=1.00/B=0.50. Fixed-batch correction did not recover B acquisition. The experiment did not invoke the formal allocation (trainer formal invocations 0; formal decision remains unassigned). Construction disposition: `HOLD_CONSTRUCTION_GRADIENT_PATH_INACTIVE`.

Independent raw-only audit returned `PASS_CONSTRUCTION_AUDIT`: six arms, 54 curve points, 108 A/B metric cells recomputed; data generation, base digest, update schedule and unknown/stale YIELD controls checked; zero errors. Raw JSON: 2,299,063 bytes, SHA-256 `9feb483c29c71191d519eb1be3842de44ead6e4df6c751defabd5fa40795af97`, matched exactly between dedicated Docker volume and local export.

## C — explanation / confounder

The source initializes the right LoRA factor matrix to all zeros. Under the specified bilinear adapter, this makes the gradient into the other factor zero on the first update, and the zero factor continues blocking the adapter path. Thus the old single-row and new batch-2 variants both remain at the base predictions. This is a mechanism diagnosis from the frozen computation, not a claim that batch updates cannot learn in general. The A task is also deliberately simple and the synthetic tasks share substantial structure.

## U — limits and next gate

No formal allocation, no population inference, no real-time/live learning, no GUI/task transfer, no realistic forgetting, no concurrency/restart durability and no action authority. Preserve this construction result and #4824 v1 unchanged. A successor should alter only the rank-factor initialization to a non-degenerate, preregistered factor pair, prove nonzero adapter gradient during zero-update construction tests, and then run held-out A/B construction curves before any formal gate is proposed. Any future formal allocation must be a separate fresh-seed Issue with independent source/raw auditor and explicit user-authority boundary.

