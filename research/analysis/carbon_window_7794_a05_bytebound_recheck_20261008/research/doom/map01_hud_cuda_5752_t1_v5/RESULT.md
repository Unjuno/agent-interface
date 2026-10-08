# Allocation-05 result

**Disposition: `PASS_CUDA_HUD_EQUIVALENCE_SPEED_SCOPED`.**

- Candidate invocation: 1; exit 0. Independent raw-only CPU audit: 1; exit 0. Retries: 0.
- 23 unique retained screenshots (19 in-envelope + 4 baselines); both health and ammo outputs matched exactly between CPU and CUDA for all 23 frames.
- 690 alternating-order paired single-frame timings. CPU p50: 37,331,150 ns; CUDA p50: 15,916,150 ns; CUDA/CPU median ratio: 0.42635038, about 2.35× faster and below the preregistered 0.5 threshold.
- GPU batch measurements were descriptive only; the per-frame timing gate determined the result.
- Independent auditor: `PASS`, errors=0; dataset-hash, GPU-value, and timing mutations all rejected.
- CUDA cold setup: 1,845.4534 ms under the preregistered definition. Python/Torch imports, WAD parsing, and CPU template extraction are excluded.
- Host: Windows 10 build 26200, CPython 3.11.9, PyTorch 2.5.1+cu121, CUDA runtime 12.1, NVIDIA RTX 3080 Laptop 16 GiB.
- GPU use was directly observed during the candidate (Python PID 16112; 207 MiB / 3%, later 347 MiB). It returned to 0 MiB / 0% after completion.
- One PyTorch warning reported that a read-only NumPy array was passed to `torch.from_numpy`; preserved in `candidate_console.log`. No result mismatch or audit error occurred.

The frozen dataset SHA-256 is `4546d17f230608952e4bf26f2eb7d596c1c7a976090eefc1a4677187b3088e1c`; runner SHA-256 is `c0b32e3c97f68f1fecb624517a7d06660427800e8cabfc2a45cf14904fe2346b`; independent reference SHA-256 is `59f271038f481f81580c3b67367ba633a09797983fc81cfbe50b9f0ef865ffb6`. The start-gate main was `c427c704404fc2b35ea9e06a57e61d239b77b369`; its delta from preparation main touched none of the selected HUD inputs or reader sources.

This is exact HUD state extraction and a narrow fixed-image timing result only. It is not threat recognition, beneficial action attribution, action causality, live control, gameplay, survival, MAP01 exit, integrated #59 success, general latency, or human-tempo evidence. It does not close Issue #59.
