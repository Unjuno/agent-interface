# Issue #4745 — resident Mitra-v2 local GPU successor

## H / T / D / C / U

**H.** The CPU STOP in #853 is specific to the serialized `TabularPredictor`
prediction path. A single resident `MitraClassifier`/trainer on this PC's RTX
3080 will reuse one in-context support state for 1,024 sequential batch-size-1
queries, avoid checkpoint-scale process reads on each query, retain the frozen
six-class finite probability ABI and repeated-query determinism, and complete
with warm p95 <500 ms. This is runtime/ABI evidence, not a quality hypothesis.

**T.** Allocation `mitra-gpu-rung0-853-successor-local-20260927-01`; issue #4745;
branch `research/mitra853-gpu-resident-20260927`; path
`research/system1/mitra_tabular_rung0_853_gpu_resident_v1/`. Start only after
Issue #4738 and the later-opened Issue #4754 RTX 3080 allocations are complete
and a fresh check finds no active GPU owner/process/container. The predecessor CPU allocation/container is
consumed and must not be rerun. Use the exact #853 support/query CSVs and exact
Mitra-v2 checkpoint/config/model-card hashes. Use local Docker Desktop only.
Packages may be acquired by this PC during preformal construction, but all
distributions are version/hash recorded before formal work. The immutable CUDA
base image is the dependency floor; `requirements.lock` lists the resolved
additional distributions installed from the local wheelhouse, and
`wheelhouse-manifest.json` records every downloaded wheel SHA-256 and byte size.
The construction image is built offline and its resulting image ID is frozen
before formal work. The formal container uses `--pull=never`, `--network none`,
read-only root/source/model/
fixture mounts, bounded CPU/RAM/PIDs and a writable fresh output mount. No
external compute/workflow, model provider, GUI/input, user data or host port.
The frozen container entrypoint launches exactly one formal allocation; only a
typed preflight STOP may precede a model invocation. Construction-only tests
must invoke their test module explicitly and never the image entrypoint.

Use AutoGluon 1.6.3's direct `MitraClassifier`, explicit `device="cuda"`,
`fine_tune=False`, `fine_tune_steps=0`, one estimator and the pinned local model
directory. Call `fit` once to materialize the context, retain its sole trainer,
then call `predict_proba` directly (never `TabularPredictor.predict_proba`).
Instrument all concrete `torch.optim.Optimizer.step` methods and require zero
calls. Record 16 excluded warmups, exactly 1,024 measured single-row queries,
and 16 repeats of query indices 0–15. Per prediction retain wall-clock interval,
wall latency, CUDA event duration, resident parameter device/bytes, CUDA
allocator bytes, `/proc/self/io:rchar` delta and raw probabilities. Also retain
cold model load, context setup, p50/p95/p99, peak RSS/VRAM, exact runtime/model/
source identities, logs, invocation receipt and terminal Docker state.

**D.** `PASS_GPU_RUNTIME_ABI_SCOPED` only if hashes/versions match; fit creates
one CUDA-resident trainer; 1,024/1,024 outputs have six finite nonnegative
probabilities summing to 1 within 1e-4; all measured requests show a resident
CUDA model, positive CUDA event interval and per-request device/memory samples;
all repeated outputs match within 1e-6; no optimizer step or fine-tuning occurs;
the formal network is disabled; no query has a process read-counter delta at
least 80% of the 302,717,904-byte checkpoint; raw evidence is complete and an
independent raw-only auditor reports zero errors; and warm single-query p95 is
<500 ms. p95 <100 ms additionally records `REALTIME_10HZ_CANDIDATE`. If the
complete valid block has p95 >=500 ms or checkpoint-scale reads persist,
record `REJECT_GPU_HIGH_CADENCE_SHAPE`. Any image/provenance/CUDA/ABI/network/
optimizer/audit/incomplete-run defect is a typed STOP/HOLD/FAIL_INTEGRITY, not
a scientific PASS.

**C.** The CPU reread may be an AutoGluon wrapper artifact rather than a Mitra
limitation. Direct estimator semantics could differ from the public predictor
API. CUDA 12.1/Torch 2.5.1 and AutoGluon 1.6.3 may import but fail during CUDA
forward. GPU launch/setup overhead may dominate this small structured input.
No task-specific fine-tuning, quantization, distillation, hyperparameter
tuning, task-quality scoring, or CPU/GPU causal quality/speed comparison.
`pip check`'s known `ninja 1.11.1.1` platform-tag warning is recorded separately
and is not silently treated as a package import result.

**U.** One pinned model, one synthetic 8-feature/6-class fixture, one Windows /
Docker Desktop / RTX 3080 host. No accuracy, calibration, safe-abstention,
transfer, end-to-end interface benefit, frontier-model benefit, GPU-vs-CPU
causal speedup, action authority, GUI effect, fine-tuning efficacy or product
claim. #853's CPU STOP and all its prior evidence remain unchanged.

## Preflight record

Construction-only local probes have confirmed model/config/card SHA-256s, the
Python 3.11 CUDA package-resolution plan, imports of AutoGluon 1.6.3 / Transformers
5.17.0 / the Mitra modules, and the direct estimator signatures. No checkpoint
was loaded and no fit/predict/GPU invocation occurred. Exact CPU Python 3.12
transitive pins do not port to Python 3.11 (`contourpy==1.4.0`); this successor
uses a separately resolved Python 3.11 lock. A pip-check `ninja` metadata warning
was reproduced on the base image; module import passed when that unrelated
diagnostic was not used as a short-circuit. See #4745 construction comments.

## Invocation authorization

The local RTX 3080 is a shared resource. Issue #4738 was open at initial intake;
it has now completed, but the later-opened Issue #4754 remains an active GPU
allocation. The runner/launcher must refuse to launch until every overlapping
GPU allocation, including #4754, is complete and a fresh GitHub + local
process/container collision audit is recorded. This is a
precondition, not an invitation to overlap when `nvidia-smi` happens to show
0 MiB in use.

