# Issue #4957 — exact host-frame CPU vs CUDA benchmark

**Decision: `REJECT_GPU_FOR_HOST_RESIDENT_EXACT_O1_SCOPED`.** All six exactness cases passed on the RTX 3080 Laptop GPU, but the CUDA path was slower than CPU `numpy.array_equal` at both large resolutions after including two host-to-device copies and synchronization. No runtime or correctness gate failed.

This is a performance follow-up to #1564, which established that approximate global aHash cannot suppress tiny local changes safely in its synthetic corpus. The present test asks whether an exact comparison could be offloaded when frames begin in host memory; it does not alter or supersede #1564.

## Frozen execution and evidence

- Allocation: `gpu-exact-frame-gate-1564-20260928-01`.
- Preregistered on Issue #4957 before execution; freeze SHA-256: `1c5c0f74e3fefb7b5a3e1977e2e5f467b2beba9a75fb3b537156cf003a90352c`.
- Latest main before freeze: `58386990aa73f3291556e613a43f50b72a5a6b32`; the experiment branch includes it as a parent.
- Pinned image: `sha256:01ea4e60b03e8a7d48644d0dce596bd2e42ab3815fdc52b0c7a6d4cbcf757dac`, Linux/amd64, Python 3.11.10, NumPy 2.1.2, PyTorch 2.5.1+cu121, CUDA runtime 12.1.
- Device receipt: NVIDIA GeForce RTX 3080 Laptop GPU; host driver 581.57.
- One formal GPU invocation, exit 0, no retries. One separate network-disabled read-only raw audit, exit 0.
- Six case/outcome pairs; 25 CPU and 25 CUDA timed samples per pair (150 per arm, 300 total). Three warm-ups per case/arm are excluded. The raw JSON retains every duration.
- Independent audit: `PASS_RAW_RESULT_AUDIT`, errors `[]`, 6 exactness rows and 6 measurement rows. Audit recomputed the decision from raw samples. Construction tests were 3/3, including rejection of a stale median and wrong CUDA exactness.
- Raw result SHA-256: `682cef531e07d9c7245c566afa1d23f4abfa40f0ab34d1b66bae8c7d8178deee`.

## Results

Medians and p95 are milliseconds; the CUDA column includes host-to-device transfer for both images and synchronization on every call.

| RGBA size | Case | CPU median | CUDA median | CPU p95 | CUDA p95 |
|---|---|---:|---:|---:|---:|
| 64×64 | unchanged | 0.006676 | 0.133940 | 0.014082 | 0.176800 |
| 64×64 | one channel pixel changed | 0.006629 | 0.132135 | 0.015857 | 0.212940 |
| 1920×1080 | unchanged | 1.303252 | 2.166657 | 1.734285 | 3.006867 |
| 1920×1080 | one channel pixel changed | 1.179528 | 2.013726 | 1.286043 | 2.203309 |
| 3840×2160 | unchanged | 5.207981 | 7.131789 | 5.943593 | 8.212493 |
| 3840×2160 | one channel pixel changed | 5.306649 | 7.312367 | 5.814435 | 7.835224 |

CPU and CUDA agreed with the expected exact-equality result in all 6/6 cases. For unchanged 1080p frames, CUDA median was 1.66× CPU; at 4K it was 1.37× CPU. The preregistered break-even condition failed at both sizes, so the hypothesis that this transfer-inclusive CUDA path would not be faster is retained for this host-resident workload.

## Scope

This is one synthetic host-resident workload on one Windows/Docker Desktop Linux container and one RTX 3080 Laptop GPU. Input construction is outside timed intervals; each CUDA timing includes copies of both host arrays and a synchronization. No frames were captured from a GUI, no model was loaded, and no training/inference/task effect was measured.

This does not test frames already resident on the GPU, live capture/copy pipelines, natural frame distributions, energy, observation usefulness, image-token savings, or production O1/O2 integration. It is not a portable GPU/CPU performance claim.