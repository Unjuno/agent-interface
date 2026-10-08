# Historical formal result: #2548 v3 (not qualified)

PR review found the v3 audit could pass incomplete/unsafe records and its provenance logic trusted plan booleans. The execution rows below are retained exactly as historical output, but the v3 PASS is withdrawn as a qualified result. The authoritative successor is [RESULT_V4.md](RESULT_V4.md).

Decision: `PASS_BOUNDED_REANCHOR_PRESERVES_SAFETY_SCOPED`.

| case | guard-only | reanchor | MAE used by reanchor |
|---|---|---|---:|
| c01 coast guard-only | ADMIT | no fresh observation | — |
| c02 drift guard-only | REJECT_CONTEXT_CHANGED | no fresh observation | — |
| c03 drift fresh | REJECT_CONTEXT_CHANGED | ADMIT | 0.0000371 |
| c04 coast fresh | ADMIT | ADMIT | 0.0001021 |
| c05 stale | REJECT_CONTEXT_CHANGED | REJECT_NO_FRESH_OBSERVATION | — |
| c06 ambiguous fresh | REJECT_CONTEXT_CHANGED | REJECT_PROVENANCE | 0.0000797 |

The runtime reported `completed` for all six cases; release verification was true for all six, with zero kills, deaths, and map exits. The independent audit reports `PASS` with zero failures. Raw per-case runtime artifacts and `results.json` are retained under `formal_v3/`.
