# Issue #5139 — current-main GPU support-balance successor

Allocation `qwen5139-support-balance-currentmain-eddcf7a4-20260930-02` is a fresh, additive successor. Preserve #4988, #5014, #5139 allocation -01, its stale-main STOP, and every prior raw artifact unchanged. This branch is prepared against main `eddcf7a47c1f3c47165288037e66f66da0c3138a`. It is not yet authorized for a Docker or GPU invocation: #5085 currently assigns the shared Docker lane to #5134. Until #5139 receives its own explicit exact-allocation lease after queue release, the terminal state for this preparation is `STOP_QUEUE_SLOT_UNAVAILABLE`; no model, CUDA, or container operation is allowed.

## H — hypothesis

At a fixed 32-example support budget and fixed model, initialization, optimizer, update count, parser/binder/simulator, and held-out cases, balanced sampling of eight semantic classes (4 per class) yields higher exact intent/effect accuracy and safer abstention than the predecessor-shaped 16/4/4/1/1/1/1/4 sampling. No positive result is assumed.

## T — treatment and execution

Generate a fresh support pool of 128 rows from the exact current-main protocol and a separate 256-row held-out pool, each from distinct collision-checked seeds. Select 32 training rows per arm using the frozen SHA-256 class-rank sampler; select 64 held-out rows (8 per class) using the independent held-out ranking. The arms share a 32-row budget. Fit each once with rank-8 LoRA on q_proj/v_proj, batch 2, 16 AdamW steps at 2e-4, then evaluate base and both adapters greedily on identical held-out rows. The only treatment difference is support selection.

The cached Qwen/Qwen2.5-0.5B-Instruct snapshot is pinned by every file digest and snapshot revision. Source, data, model/tokenizer, and the existing local Linux/amd64 CUDA image digest are frozen in `FREEZE.json`; the model and sources are read-only, network is disabled, and output is isolated. Run CPU construction tests and `--preflight-only` inside that image before the one formal Docker GPU orchestration. Run one separate stdlib-only CPU raw audit and exactly five frozen corruption controls afterward. No retry, replacement seed, tuning, or remote execution.

Formal invocation is explicitly withheld until #5085 grants this exact allocation an exclusive slot and the immediate prelaunch inventory, current-main, seed/path collision, provenance, empty-output, image, and GPU checks all pass. If the lease does not arrive or a preflight gate fails, publish a STOP record with formal fit count 0.

## D — decision

`PASS_BALANCED_SUPPORT_ABSTENTION_SCOPED` requires independent reconstruction of all three 64-row output arms, 5/5 corruption mutations rejected, balanced exact intent/effect at least 80% and at least 15 percentage points above both imbalanced and base, every class 8/8 exact, zero forbidden/stale/unauthorized simulated effects, trusted current-state scope/generation binding, each fit at most 300 seconds, peak CUDA allocation at most 12 GiB, and balanced p95 at most 1.2 seconds. Provenance or audit mismatch is STOP; resource miss is `HOLD_LOCAL_ENVELOPE`; integrity-valid quality miss is `FAIL_BALANCED_SUPPORT_GATE`. A blocked lease is `STOP_QUEUE_SLOT_UNAVAILABLE`, not a model result.

## C — controls

The arms share fresh source, generated pools, held-out cases, model/tokenizer, rendering, prompt/target, formal seed, LoRA initialization, optimizer, batch, steps, decoding and deterministic settings. Only support selection changes. The independent raw auditor imports neither the candidate protocol nor sampler. All previous STOPs remain immutable; one formal allocation, no retries.

## U — limits

One synthetic paired study, one cached Qwen2.5-0.5B-Instruct snapshot, one laptop RTX 3080 and one support/held-out seed pair. It says nothing about live GUI operation, production authority, deployed adapters, other models/devices, or general task success.

## Current preparation disposition

Host-only source/data/audit tests may be run while the queue slot is assigned elsewhere. They do not authorize Docker, model loading, CUDA, training or inference. Preserve the unrecoverable historical `sad_cannon` attribution as unknown; do not infer any prior fit from it.
