# Run record — A03

- Allocation: `MODEL-INTERFACE-CROSSOVER-6035-T0-A03-20261002`
- Owner task: `01a0b990-3d17-72f1-a908-9a2072104ce5`
- Frozen base and launch main: `3c23531a65ff9534f73267845c818f441d73c1bc`; launch diff paths: none.
- Source/freeze commit: `2836fa7667306d0b4d58bf836b5907e4270e5359`.
- Runtime: Windows CPython 3.11.9, standard library only. Formal execution: 2026-10-02 18:14:27–18:14:30 UTC.
- Preflight: relevant base-to-main paths unchanged; source hashes matched; output paths absent; C: free 31,560,945,664 bytes. Existing Ollama/WSL-related host processes were observed but not inspected, stopped, or invoked. Candidate and auditor did not use them.
- Candidate: 1 invocation, exit 0, emitted 64 assigned rows in four synthetic scenarios.
- Independent raw-only auditor: 1 invocation after candidate, exit 0, reconstructed 64 rows, errors=0, disposition `PASS_METHOD_SCOPED`.
- Retries: 0. Formal outputs were captured once and have not been regenerated.

## Reconstructed scenario results

| Scenario | Profile A route effect | Profile B route effect | Difference-in-differences | Disposition |
| --- | ---: | ---: | ---: | --- |
| additive control | 0.25 | 0.25 | 0.00 | `NO_MATERIAL_INTERACTION` |
| planted crossover | 0.50 | -0.50 | -1.00 | `INTERACTION_DETECTED` |
| hard safety gate | 0.50 | 0.25 | -0.25 | `FAIL_HARD_SAFETY` |
| non-comparable contract | 0.25 | 0.50 | 0.25 | `HOLD_NO_COMMON_CONTRACT` |

Each of the four cells in every scenario has the same four assigned task IDs. Verified-by-deadline success fraction uses all four assigned attempts as denominator; `VERIFIED_FAILURE`, `TERMINAL_SAFE_STOP`, `NOT_STARTED`, `ADMIN_CENSORED`, and `OUTCOME_MISSING` are retained separately. No success-only latency analysis, standard error, confidence interval, p-value, or empirical model contrast is calculated.

## Artifact hashes

- `results/formal_03/candidate/raw.json` SHA-256: `ae43cda00562dddecf8f05da83907c3ca53efaa00466c94493c63cd967e00a20`.
- `results/formal_03/auditor/audit.json` SHA-256: `084e51c7e8651e66e036a5954d8d65421b6245096836c79e3d130baf9acce85c`.
- Independent construction suite: 6/6 passed before freeze, including 5/5 frozen corruption controls rejected.

This is method-scoped evidence for one authored deterministic fixture only. Profiles/routes are labels. No GPU/CUDA, model/provider, container/WSL, network, GUI, game, task input, actual interface recommendation, model-agnostic effect, safety or product-performance claim is made. A01 and A02 pre-candidate STOP packets remain separate and unchanged.
