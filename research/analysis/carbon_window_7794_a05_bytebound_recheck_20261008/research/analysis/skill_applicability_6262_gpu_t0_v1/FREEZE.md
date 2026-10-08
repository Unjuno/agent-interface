# Issue #6262 — frozen T0 method test

Experiment: `AI-6262-T0-GPU-20261002-01`  
Frozen main: `389b109629ca0c8baf7a9daf725eded76c358162`  
Decision freeze: 2026-10-02 07:13 JST, before formal candidate execution.

## H / T / D / C / U

**H.** For this preregistered synthetic reusable-skill example, a claim-to-cell certificate will detect unsupported scope expansion that flat-success and factorwise-success summaries miss, while preserving a truly tested, exact, narrow claim. If the certificate promotes an untested/failed/unknown interaction, or cannot distinguish an exact qualified narrow pass, the method fails this fixture.

**T0.** The frozen fixture has four binary applicability factors (`backend`, `mode`, `evidence`, `target`). One dialog × alternate-target combination is structurally infeasible by stipulation, leaving 12 feasible full cells and 23 feasible two-way projections. There are 10 qualified exact-effect PASS rows, one exact-effect FAIL predecessor, and one apparent effect PASS whose route is not independently qualified; its authority grant must not substitute for capability, so its effective state is UNKNOWN. The flat comparison promotes at an 80% threshold; factorwise coverage requires a PASS for each level; the certificate supports the wide claim only when every feasible pair projection is represented exclusively by qualified PASS rows. The exact `t01` claim is separately eligible only when that exact trial is present and qualified. Enumerate all `2^12 = 4,096` evidence subsets with the CUDA candidate and independently reconstruct every gate using a pure-Python CPU auditor. No generated case is selected or dropped after outcome.

**D.** `PASS_METHOD_SCOPED` only if the auditor exactly reconstructs every candidate subset and projection; the full ledger rejects the wide claim; `t01` retains the exact narrow claim; at least one subset demonstrates simultaneous naive flat/factorwise promotion while the certificate refuses; and four frozen mutations (fabricated infeasible edge, hidden offered trial, grant-as-capability, unsupported narrow promotion) are all rejected. Any discrepancy is `FAIL_AUDIT`/`STOP`; no repair or rerun under this allocation.

**C.** A transparent per-condition ledger may already be enough. Pairwise coverage can miss higher-order and history-dependent failures. The certificate may add bookkeeping without improving decisions.

**U.** This is a constructed truth fixture, not a real retained skill, application, GUI, or user task. Feasibility is stipulated, not empirically established. A finite t-way certificate cannot prove universal applicability or safety. The 4,096-subset workload is small; CUDA is used as the requested local compute path, not to claim GPU necessity or speedup.

## Frozen implementation and inputs

Source path in the repository: `research/analysis/skill_applicability_6262_gpu_t0_v1/`.

| File | SHA-256 |
|---|---|
| `FIXTURE.json` | `adc342e1416ed13d1cd38a9e881cf1b5163548a8ce83f02670ffef3f91964715` |
| `candidate.py` | `2dfdcd061e845f7bbf9e68aba72e2675a2c8b2cf91f62b81bca876b1b568f157` |
| `auditor.py` | `f9aa23b1da71051ea1fd83dbc374234782e837856b0e99c0ba4c025f4aa5c901` |
| `test_construction.py` | `061075caaed2384eab704d2bcff96a3984e0f169ef3dc9096f90c075f9a6d81a` |

Candidate: Python 3.12 + PyTorch 2.5.1+cu121, `cuda:0`, NVIDIA GeForce RTX 3080 Laptop GPU. Auditor: Python standard library only; no candidate imports. Docker Engine service was stopped and Docker CLI integration was unavailable in the active Arch WSL distro; `docker-desktop` itself showed Running, so it was not inspected or modified. This bounded host-local synthetic run has no network, model, GUI, container, physical input, or external effect.

## Frozen commands and invocation limits

Construction only (before freeze):

```text
python -m unittest research_6262_gpu_t0_v1.test_construction -v
python -m py_compile research_6262_gpu_t0_v1/candidate.py research_6262_gpu_t0_v1/auditor.py
```

Formal candidate: exactly one invocation after the source/fixture freeze:

```text
python research_6262_gpu_t0_v1/candidate.py research_6262_gpu_t0_v1/CANDIDATE_RAW.json
```

Independent audit: exactly one invocation after candidate completion:

```text
python research_6262_gpu_t0_v1/auditor.py research_6262_gpu_t0_v1/CANDIDATE_RAW.json
```

Retries, source changes, candidate reruns, and outcome-based fixture edits are prohibited for this allocation. Preserve a STOP or mismatch as-is.
