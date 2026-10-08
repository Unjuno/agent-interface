# Online streamed LoRA role-skill update — first outcome

Issue: [#3769](https://github.com/Unjuno/agent-interface/issues/3769)  
Allocation: `needle-lora-3441-online-stream-v1`  
Frozen runner SHA-256: `62c74d80aed3c0932967fa42bdf9eda00aea64d33a3bb7c6066ed903bb3d61d6`  
Independent auditor SHA-256: `a1a7147a59845137080af113b06621c429ebbaab3a46902c4f565ed4c62436af`  
Raw canonical result SHA-256: `27f4e4d3f88bfce89528688be07080ec0776ddab887bf91e12d7434363c09101` (51,168 bytes; losslessly retained in RESULT.json gzip envelope)

## Formal disposition

**`FAIL_ONLINE_ADAPTATION_QUALITY`** under the predeclared gate. Exactly one formal runner invocation; no retry, replacement, or tuning.

| Measure | Result | Gate |
|---|---:|---|
| Frozen base role A held-out | 0.9465 (3,877/4,096) | >=0.90 PASS |
| Online role B after 16 streamed examples | 0.8877 (3,636/4,096) | >=0.90 FAIL |
| Matched batch-replay role B | 0.8069 (3,305/4,096) | >=0.90 FAIL |
| Online minus batch role B | +0.0808 | >=-0.03 PASS |
| Online update p50 / p95 / max | 2.605 / 3.205 / 3.205 ms | p95 <=60 PASS |
| Four malformed/stale route controls | 4/4 YIELD | all YIELD PASS |
| Complete adapter state round-trip / rollback | exact / exact | PASS |
| Base state immutability | exact | PASS |

Online held-out trajectory after 1, 2, 4, 8, 12, 16 feedback rows was respectively 0.0315, 0.0542, 0.5522, 0.8804, 0.8809, 0.8877. It improved rapidly but plateaued below the absolute threshold. Batch arm also missed the threshold; this result does not show online competence or an online advantage over a capable batch learner. It only establishes the observed outcome for these frozen procedures.

The online arm used 8 AdamW steps after each incoming row over the seen-row replay buffer (128 total). The batch arm used the same support set and 128 steps after all feedback arrived. CPU p95 update timing is local schedule timing, not a real Astra feedback round trip.

## Execution and audit

- Windows host CPU, Python 3.11.9, PyTorch 2.5.1+cu121, one thread, deterministic algorithms enabled.
- Docker Desktop Linux-engine pipe was unavailable. This is explicitly **not** container evidence. No service restart/repair, image pull, or disk cleanup.
- No GUI/input/provider/network task action, shared runtime change, or disk checkpoint.
- Independent auditor re-opened RESULT.json from the branch, verified compressed payload/raw SHA, recomputed all three accuracies from all 12,288 retained expected/prediction rows, recomputed online p95, and confirmed route/state controls. Auditor disposition agrees: `FAIL_ONLINE_ADAPTATION_QUALITY`.
- Raw rowwise expected labels and predictions are preserved in RESULT.json for recomputation.

## Interpretation and next discriminator

This does not justify promotion as a System-1 skill. Because both online and batch B missed 0.90, the next useful question is whether this stream/update budget is intrinsically insufficient or whether the synthetic task/support budget is the bottleneck; do not rerun this seed or retune this allocation. Any continuation must be a new, preregistered successor that changes one factor and preserves this failure unchanged. Real-world skill transfer, durable role-network behavior, online safety, and product/latency benefit remain untested.
