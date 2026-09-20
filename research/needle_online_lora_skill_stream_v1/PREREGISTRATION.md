# Online LoRA skill snapshot/resume

Tracking Issue: #3911. Predecessors: #3769 and #3890. Allocation: `needle-online-lora-skill-stream-resume-v1`. Branch: `research/needle-online-lora-skill-stream-3911-20260921`. Additive path: `research/needle_online_lora_skill_stream_v1/`.

## H/T/D/C/U

**H:** A live rank-2 online LoRA skill serialized after each feedback arrival with model tensors, AdamW moments/step, immutable-base identity, feedback cursor and version can be resumed in a fresh process and exactly match an uninterrupted in-memory stream. Corrupt/stale/duplicate/skipped/incompatible state must yield before proposal or mutation.

**T:** Three fresh seeds 39111, 39112, 39113. Reuse #3769's synthetic task and exact schedule: A base (8 features, hidden 16, tanh; 512 rows / 400 AdamW updates), B rank-2 output LoRA (16 sequential support rows; 8 AdamW updates per arrival over seen rows, 128 total; 4096 held-out). Paired arms share initialization, data, support order, minibatch-index plan, labels and base. Reference retains live optimizer in-process. Resume arm emits canonical data-only JSON checkpoints and advances one arrival in each fresh worker process. Snapshot after every arrival 1–16; compare exact adapter tensors, AdamW moments/step, cursor, base identity at all stages; compare held-out logits and predictions at 1/2/4/8/12/16. Retain package digests/bytes, worker PIDs, update-only and full fresh-process wall timing, row-level held-out predictions, and independent source/data/reproduction evidence. The auditor independently regenerates and trains the continuous reference without importing runner/worker code, checks checkpoint chains and numerically evaluates retained rows.

**D:** PASS only if all 3 seeds have every resume state exactly equal to independent continuous training, all milestone logits/predictions equal row-for-row, versions/cursors advance once per arrival, all malformed/stale/duplicate/skipped controls yield without mutation, base stays exact, independent audit has zero errors, and update-only p95 <=60 ms. Report absolute B accuracy vs .90 as a separate capability diagnostic; it is not the persistence-equivalence gate. Cold process start and encode/validate/decode time are measured separately and disclosed. Typed FAIL_RESUME_DIVERGENCE, FAIL_SNAPSHOT_INTEGRITY, FAIL_UPDATE_LATENCY, STOP/HOLD; one formal orchestration, no retries/tuning/seed replacement.

**C:** Cached local `needle-pilot05:local` image only, linux/amd64, CPU one thread, network none, source read-only and unique output per seed. Each arrival executes in a distinct new Python process within the isolated container; builder/reference and independent auditor run in separate containers. No pull, repair, prune, GPU, GUI, external inference, user data, runtime authority, or shared runtime edits. SHA256 integrity is not authenticity.

**U:** Three seeds, one small synthetic family. No claim about real Astra feedback, generalized skill transfer, concurrent training/inference, crash-atomic filesystems, hostile authenticity, GUI/action safety, end-to-end model latency, or production promotion.

## Construction vs formal

`test_construction.py` tests only the fixed JSON contract and fail-closed identity/digest/cursor checks; it must not train or score a model. Freeze runner, auditor, construction tests, preregistration, exact Docker image ID and decision gates before formal. Formal evidence is immutable. Auditor/source corrections, if any, must be independently versioned and disclosed without rerunning training.
