# GPU supervisor CUDA parity and non-authority probe

**Disposition: `PASS_CUDA_PARITY_AND_NONAUTHORITY_SCOPED`; GPU cost result is unfavorable on this microbatch.** The CUDA hint exactly matched the independent CPU oracle on all 256 frozen rows, and the separate final gate admitted no stale, ambiguous, or forced-YIELD row. All three mutation controls were rejected. This confirms only the synthetic contract. Warm diagnostic p50 was 16.3 µs for CPU and 41.1 µs for CUDA (2.52× CPU latency); the CUDA timings exclude the one-time host-to-device tensor construction, so this run offers no evidence that a GPU is useful for such small hint batches.

## Frozen experiment

- Issue: [#4972](https://github.com/Unjuno/agent-interface/issues/4972), successor to #2583; preserves #4973 and predecessor outcomes.
- Allocation: `GPU-SUPERVISOR-4972-20261001-01`, one Windows RTX 3080 Laptop GPU host run, 2026-10-01 05:15–05:45 UTC window.
- Base main: `1a43d91e1799752b1f1e58e275b8f4088cc24c1e`.
- Branch: `research/gpu-supervisor-cuda-4972-20261001-01`.
- Candidate command: `python runner.py` (one invocation, exit 0; candidate raw created 05:17:19 UTC).
- Auditor command: `python audit.py` (one invocation after candidate exit 0, exit 0; audit created 05:17:27 UTC).
- Environment: Windows 10 build 26200; CPython 3.11.9; PyTorch 2.5.1+cu121; CUDA runtime 12.1; NVIDIA GeForce RTX 3080 Laptop GPU; driver 581.57.
- The preregistration was committed and all five frozen files were read back from the exact branch before execution. At start gate the host reported 0 MiB / 16,384 MiB, 0% utilization, no GPU processes, and `torch.cuda.is_available() == True`.
- An initial PowerShell start-gate expression misread a multi-line `nvidia-smi` result and stopped before candidate execution. The gate was corrected to normalize stdout as one string, then passed. Candidate count remained zero until the successful invocation.
- No model, GUI, game, user input, network, Docker container, or training was used. The CUDA tensor remained GPU-resident across the timed repetitions; timings do not include tensor construction or transfer.

## Result and audit

The frozen set contains 64 rows each for fresh-valid, stale-high-confidence, ambiguous-high-confidence, and forced-YIELD-high-confidence strata. CPU and CUDA hints agreed 256/256; final admissions agreed 256/256. Admissions by stratum were fresh-valid 16, stale 0, ambiguous 0, forced-YIELD 0. The independent raw-only audit returned `PASS`, `errors=[]`; it rejected a flipped hint, a forced stale admission, and a dataset-hash mutation.

Diagnostic timing used 30 repetitions on the same resident 256-element confidence vector. CPU p50 was 16,300 ns; CUDA p50 was 41,100 ns; GPU/CPU ratio was 2.521. Timing was declared diagnostic only, had no threshold gate, and was not balanced across order. It must not be interpreted as a general GPU/CPU speed benchmark.

Evidence hashes:

- `FREEZE.json`: `fca718280fdfca280d0b42365ea0f404559516c5c629a9676357585b980934af`
- `dataset.json`: `5d1bfa0da1a9f0fe596bbfcacf5e11db161518e7e047fd288cec5cd082cba49c`
- `runner.py`: `835879bf1f767003c973138773ebd048efa438e040b12c8a7bcf77bc2fc7e5cd`
- `audit.py`: `82f85bfa7205cb85ef7778f2f19f5ca9ba9616e0dcaa39f1636ded3f32a99544`
- `candidate_result.json`: `1597939a8ff055d59f677f7c82093688b3553442134634ab65f9db755d15366d`
- `audit_result.json`: `fbc1da7e90ed39de489e452d6b482d8af2a3f5c528c92e8f882cdaccce03bb0e`

## Scope limits

No learned supervisor was evaluated. The confidence threshold is a deterministic fixture rule, not a trained policy or a natural workload distribution. The final gate was a synthetic local function, not Agent Interface runtime admission. This does not establish task quality, model-call savings, production safety, end-to-end latency, or GPU utility for larger batches. The observed 2.52× warm latency disadvantage applies only to this tiny resident-vector probe.

