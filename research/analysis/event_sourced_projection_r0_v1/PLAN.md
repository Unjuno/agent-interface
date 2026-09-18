# #1776 Event-sourced projection and checkpoint equivalence

H: deterministic contiguous event folds equal incremental event-only projections; a trusted checkpoint bound to exact prefix digest + state may resume the suffix exactly, while index-only checkpoints and out-of-band/duplicate/orderless/missing-event shortcuts are unsound in general.
T: exhaust all 6-event sequences length0..6, all prefix checkpoints, independent audit, five negative discriminators, source-first formal1/reruns0.
D: full/incremental mismatch0; checkpoint-resume mismatch0; invalid sequence/checkpoint corruption rejected; all five negative controls non-vacuous; audit/source integrity PASS.
C: checkpoint authenticity and boundary completeness remain separate requirements; static total order may be stronger than necessary.
U: analytical event-store semantics only; no production durability/storage/performance/GUI/model claim.
