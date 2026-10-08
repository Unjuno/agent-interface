# Issue #853 — Mitra-v2 Rung 0 local CPU feasibility

## H / T / D / C / U

**H.** With a frozen 8-feature / 6-class typed-decision shape and 256 labelled support rows, a pretrained Mitra-v2 classifier running fully locally with no network and no gradient update can reuse one installed support context and produce 1,024 single-state typed decisions at an operationally distinct cadence. Cold model load, support/context setup, and warm per-query latency are reported separately.

**T.** Allocation `mitra-cpu-rung0-853-local-20260927-01`; source branch `research/mitra-rung0-local-feasibility-853-20260927`; path `research/system1/mitra_tabular_rung0_853_v1/`. Local Docker only, fresh container, network `none`, CPU only, read-only model/source/fixture mounts, one CPU thread. Frozen candidate `autogluon/mitra-classifier-2` revision `edada0d20759c58ada8c8605c25f22f6e98ea5f0`; model file 302,717,904 bytes, SHA-256 `5ffab0e2cf52f61c5b7c7eb1e8542996736d1023a0212190cc09abc2119a1e09`; config is 512 hidden dim, 12 layers, 4 heads, 10 output slots. Inference implementation is `autogluon.tabular==1.6.3`, source release tag `v1.6.3` at commit `2d7d603c7c26234f578d3a593cf466165b649fa1`. Explicit `fine_tune=False`, CPU device, one estimator; optimizer steps are instrumented and must remain zero. Fixture is generated deterministically by `make_fixture.py`, seed 853, 256×8 support rows / 1,024×8 queries, labels cycle over all six declared classes. Timed region begins only after the single `TabularPredictor.fit` context setup completes; measure 1,024 individual warm `predict_proba` calls, and separately repeat the first 16 rows for determinism.

**D.** `PASS_GENERAL_LOCAL_SYSTEM1_RUNTIME_SCOPED` only if pins and weight hash verify, the network-disabled CPU runtime completes with zero optimizer steps, 1,024 outputs each have exactly six finite probabilities and map only to the frozen class IDs, repeated-query outputs match within 1e-6, no network is used, all raw outputs and peak RSS are retained, and warm single-query p95 is `<500 ms`. `<100 ms` additionally records `REALTIME_10HZ_CANDIDATE`. `REJECT_CPU_HIGH_CADENCE_SHAPE` if p95 is `>=500 ms` or the measured resource/runtime envelope is incompatible with an ordinary CPU-only local installation. Integrity or provenance failure is `FAIL_INTEGRITY`; pre-measurement source/runtime failure is a typed STOP, not a scientific conclusion. No accuracy, semantic quality, GUI or task-effect gate is evaluated in this rung.

**C.** Same frozen model, source, input shape, labels, support context, CPU thread count, prediction API and class mapping for every query. Only one candidate/backend is measured. Construction checks are excluded from formal rows. No gradient update, external inference, model provider, GUI, user data, action, or live authority. Wall-clock timing is descriptive only and local to this PC.

**U.** One model revision, one synthetic support/query fixture, one Windows+Docker Desktop host, one CPU runtime. This tests cadence and ABI only, not accuracy, calibration, safe abstention, transfer, end-to-end Agent Interface benefit, task quality, or action authority. GPU behavior is deliberately not substituted for the preregistered CPU rung; only a separately frozen successor may test GPU if CPU cadence rejects this path.

## Frozen artifact ledger

The original branch named in the allocation sentence above was found to be 37
commits behind `main` and had no experiment commits. To preserve parallel work,
this additive continuation uses `research/mitra853-rung0-local-20260927`, created
from `main` at `a97996b4811219a9ed09b9ad19ea3ee75955f2d0`. The original branch is
left untouched. This branch/path correction does not alter the CPU allocation,
model, fixture, runtime limits, or decision gates.

- Intake `main`: `38359097c58035b04daf418551cbe331574f7535`.
- Model Hub commit: `edada0d20759c58ada8c8605c25f22f6e98ea5f0`.
- Model SHA-256: `5ffab0e2cf52f61c5b7c7eb1e8542996736d1023a0212190cc09abc2119a1e09` (302,717,904 bytes).
- Model card declares `apache-2.0`; AutoGluon v1.6.3 source declares Apache-2.0. Card/source/license blobs and exact container image digest are recorded in `FREEZE.json` before formal timing.
- No package is installed on the Windows host. Local Docker build/provisioning is separate from the measured run; measured container is network-isolated.
