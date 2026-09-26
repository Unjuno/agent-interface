# Preregistration — rank-4 online LoRA capacity
Issue: #3790
Allocation: needle-lora-3441-rank4-online-multiseed-v1
Branch: research/needle-lora-rank4-online-3790-20260921
Path: research/needle_lora_3441_rank4_online_multiseed_v1/
Runner SHA-256: a527c4bc0ab1df832f0873cabf2c7138111859fc0c29fe369e028825b04fddba
Auditor SHA-256: 70fc9168b4ee46fbad112359c77719578c0aad260f6259846905f4a2644a031b

## H/T/D/C/U

**H:** Increasing only output-LoRA rank from 2 to 4 rescues streamed online adaptation across five fresh seeds, with no material miss against matched rank-4 batch replay, while preserving base role A, bounded update latency, fail-closed routing, and exact rollback.

**T:** For seeds 3451–3455, deterministic CPU PyTorch; per seed generate base/support/heldout streams with seeds +1..+4. Train A on 512 examples for 400 AdamW steps. Compare rank-2 online, rank-2 batch, rank-4 online, rank-4 batch with the same 16 B support rows, same 8 updates per arrival / 128 total steps, same learning rates, and 4,096 heldout rows. Rank-specific initialization uses seed+30+rank; online order/update RNGs are seed+20/+21; batch RNG seed+22. Predictions are packed two-bit labels; auditor regenerates expected task labels from frozen row seeds and recomputes each count/accuracy. Retain all per-feedback update timings/curves, routed role/epoch/version identity, four invalid-route probes, rank-4 snapshot roundtrip/rollback and base immutability. Exactly one formal invocation; no tuning/retry.

**D:** PASS_RANK4_ONLINE_RESCUE_SCOPED only if all five A and rank-4 online B accuracies >=0.90; mean rank-4 online exceeds paired rank-2 online by >=0.03; every rank-4 online seed is within 0.03 of its rank-4 batch score; aggregate rank-4 online update p95 <=60 ms; all four invalid routes YIELD; rank-4 online snapshot roundtrip and rollback are exact; base is immutable in every seed; and independent audit recomputes every held-out prediction with zero errors. Quality/retention/latency miss => FAIL_ONLINE_RANK_CAPACITY; route/snapshot/integrity miss => FAIL_ROUTE_OR_SNAPSHOT_INTEGRITY. Capture or environment issue => typed STOP/HOLD, never a quality FAIL.

**C:** Docker Linux engine read-only check unavailable (missing Docker Desktop named pipe); run frozen CPU source on host only, explicitly not container evidence. No restart/repair, image pull, disk cleanup, provider/network action, GUI/input, local checkpoints, or runtime authority.

**U:** Five seeds in one synthetic binary-factor family; no real Astra feedback, realistic transfer, application effects, production safety, concurrent updates/inference, cross-process persistence, or general latency claim.

Construction checks are syntax/packed-label roundtrip/model-shape/dispatch-only. They are not optimizer/evaluation runs and do not consume the formal allocation.
