# #5139 construction-only dataset generation on a fresh sentinel pair

Date: 2026-09-29  
Allocation label: qwen5139-dataset-construction-20260929  
Current GitHub main at intake: 5ad5a9ab465e2b0052aa301b1909b92816e70025  
Exact experiment source branch commit: 21b40837ba5bf69c0cafc0c0c6c66da3abfe301e  

Source-package files were read from the exact branch and matched their Git blob IDs locally. The upstream main delta from the earlier 71f8538 recheck does not touch this sampler experiment directory. This execution is a host-Python construction check; it does not claim to be a current-main formal source freeze.

## H — hypothesis

For a fresh pair of construction-only sentinels, the #5139 dataset builder preserves exact support-arm quotas, independently reconstructable SHA-ranked support selection, and disjoint support/heldout scope/task identity. Changing only the formal/training sentinel should change heldout rows without changing support rows or support selection.

## T — treatment

- Builder source: existing #5139 branch package make_dataset.py, protocol.py, sampler.py, and independent audit_sampler.py.
- Source Git blob IDs: bae077ce166fe0f6415d02eb42196e32c3c462d6, d5073b51d38fb9f649ed799eafcaa5e0eda5fc18, 11286aecaac16ec5effb9b3ed5924f49c0a39d7e, and 06c97ca49c1268967ecb84fe6db0a28ea07719c2.
- Construction-only sentinels: formal 903520260929, alternate formal 903520260931, support 903520260930; GitHub Issue search found no exact-string collisions. They are not formal allocation seeds.
- One saved dataset build; one in-memory alternate formal-sentinel control reuses the support sentinel. No model inference, CUDA, GPU call, Docker, fit, adapter write, or formal output.
- The original execution record says the raw construction was retained losslessly as `dataset.json.gz.b64`, but a later repository-only publication check found that the transport and restore helpers are not present in the current branch tree (details below). Until those exact raw bytes are durably published, the construction/audit result is not independently reproducible from this repository.

## D — first and follow-up outcomes

The builder exited 0 and wrote canonical UTF-8 JSON: 803,928 bytes, SHA-256 d96c4072db2ee3bb1af7503a8ae98e062794072385a15099f32121a7a8caad4b. It contains 128 support rows, 256 heldout-pool rows, 64 selected heldout rows, and 32 examples per support arm. The imbalanced counts are 16/4/4/1/1/1/1/4; balanced counts are 4/class.

The first standalone launch failed before generation because the evidence subdirectory could not import make_dataset; the corrected entrypoint discovers the parent package. That failure is retained in first_invocation.txt.

The first independent audit was STOP_DATASET_CONSTRUCTION_AUDIT: its scope-overlap corruption control changed only the displayed heldout selection, not the underlying heldout pool. The raw data itself passed the other frozen checks. Preserve that first audit byte-for-byte in audit.json; do not promote it to PASS. Separately labelled audit v2 applies the same scope mutation consistently to the pool row and selected row. On the same immutable raw bytes it returned POSTHOC_PASS_DATASET_CONSTRUCTION_AUDIT_V2, errors=[], with four controls detected: changed support seed, missing heldout row, reordered heldout rows, and support/heldout scope overlap.

The alternate-seed check passed: with support sentinel fixed and a new formal sentinel, support pool and both selected arms were identical, while heldout pool and selection changed. Independent support audit errors were empty. This is construction evidence only; the posthoc v2 result does not erase the first audit-control STOP.

## C — controls

The independent support auditor reconstructs SHA-256 rankings without importing the candidate sampler or protocol. The heldout auditor reconstructs per-class first-eight order from the raw heldout pool. Controls mutate support seed, heldout count/order, and support/heldout scope overlap. A separate cross-seed check changes only the formal sentinel.

## U — scope limits and resource disposition

This does not load the Qwen checkpoint, test tokenizer/model behavior, run LoRA, establish action quality or safety, or satisfy #5139's pinned-container/source/data/model/tokenizer formal freeze. It validates a synthetic data-construction boundary on Windows CPython 3.11.9 only.

#5085's previously stated #5134 CPU-slot assignment was corrected and withdrawn: no such assignment or authorization occurred. #5139 has no named GPU/Docker lease. #5085 comment #5864462673 separately records unauthorized Docker starts from this continuing task and directs no further Docker invocation until an exact assignment. No Docker action was taken in this construction check. No GPU or CUDA action is claimed.

## Reproduction

From this directory, with the four frozen package files at the package root:

    python -B .\build_construction.py
    python -B .\audit_construction.py
    python -B .\audit_construction_v2.py
    python -B .\compare_construction_seeds.py
    python -B .\restore_dataset.py       # preserved packaging STOP: strict decoder rejected the final transport newline
    python -B .\restore_dataset_v2.py

The builder exits 0 and original audit exits 1. Audit v2 and the alternate-seed check exit 0. restore_dataset.py retains its packaging STOP; restore_dataset_v2.py restores byte-identical raw data.

## Repository-only publication audit and correction (2026-09-28)

At the first branch readback (`2ffc8f2a`), the evidence directory contained 10 files while `MANIFEST.json` listed 15; `compress_dataset.py`, `dataset.json.gz.b64`, `restore_dataset.py`, `restore_dataset_v2.py`, and `seed_independence.json` were missing. The concern was recorded before claiming repository-only reproducibility. Five subsequent additive commits (`8379af6d` through `36f30da3`) added those exact manifest entries, including the compressed raw payload. At merged branch state `31ef16bf`, all 15 named files are present.

To verify the recovered publication without rerunning the builder or alternate-seed construction, I copied only the committed raw capsule, frozen restore/audit scripts, and independent `audit_sampler.py` to an isolated temporary directory. `restore_dataset_v2.py` exited 0 and verified restored raw size **803,928 bytes** and SHA-256 `d96c4072db2ee3bb1af7503a8ae98e062794072385a15099f32121a7a8caad4b`. From that restored `dataset.json`, a separate `audit_construction_v2.py` process exited 0 with `errors=[]`, status `POSTHOC_PASS_DATASET_CONSTRUCTION_AUDIT_V2`, and an output JSON object exactly equal to the committed `audit_v2.json`. No builder, seed-separation control, model, CUDA/GPU, Docker, or formal run was invoked. This confirms repository-only byte restoration and the post-hoc construction audit; it does not erase the original `STOP_DATASET_CONSTRUCTION_AUDIT` in `audit.json` or promote this synthetic result to model/formal evidence.

The earlier text claiming that #5085 assigned #5134 the CPU slot was erroneous and is withdrawn. The corrected #5085 comment and Issue body explicitly state that no such assignment or authorization occurred. #5139 still has no GPU/Docker lease. The separate unauthorized Docker starts disclosed in #5085 comment #5864462673 remain a governance violation; this audit used no container and creates no permission to do so.


