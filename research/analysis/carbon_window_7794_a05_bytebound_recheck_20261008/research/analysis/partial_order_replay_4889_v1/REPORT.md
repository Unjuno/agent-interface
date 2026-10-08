# Issue #4889 — finite partial-order replay result

## Overall disposition

**HOLD_AUDIT_CONTROL_HARNESS.** The one frozen candidate invocation reports `PASS_PARTIAL_ORDER_REPLAY_SCOPED`, and the raw-only auditor independently rederived every row and aggregate without semantic discrepancies. However, the preregistered evidence-integrity gate required eight effective copied-record mutations to reject; only seven rejected. The `linearizations` mutation set the OPEN/CLOSE control row's value to 1, which was already the correct value, so it was a no-op. The overall gate is not met. Preserve this first audit and do not repair/re-run this allocation.

This is an audit-control HOLD, not a semantic counterexample to the partial-order candidate. The candidate result is retained exactly as emitted; no formal reruns, replacements, or post-result tuning occurred.

## H / T / D / C / U

- **H:** Global state-and-output commutativity of event pairs is sufficient for every topological ordering that preserves all dependent-pair order to match the full-order reducer result, under this finite model.
- **T:** One local, network-disabled Docker invocation enumerated 2,025 reachable states, 202,500 ordered event-pair/state checks, all 11,111 words of length 0–4, and every one of 87,551 legal topological linearizations. A separate raw-only implementation rederived all rows and counters.
- **D:** Candidate semantic result: 0 word mismatches; 10,828 words strictly reduce constraints; 39,122 total constraints omitted; dropping OPEN-before-CLOSE produces one divergent ordering. Independent row audit: 11,111 rows, errors `[]`. Evidence-control gate: **7/8**, so overall `HOLD_AUDIT_CONTROL_HARNESS`.
- **C:** This was exhaustive only for the declared deterministic reducer, bounded values, event alphabet, and stable per-occurrence output map. It does not model externally observable append order or hidden runtime state.
- **U:** No retained runtime trace, GUI, model/provider, GPU, concurrent backend, external side effect, timing, storage-saving, latency, token, production, authority, task, or product claim. No real trace's ordering requirements are relaxed.

## Execution and provenance

- Allocation: `partial-order-replay-4889-20260927-01`.
- Intake main: `055468a4831960f5647760d4f25c54923526c5a3`.
- Source branch: `research/replay-partial-order-1748-4889-v1`.
- Source image: `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64.
- Host: Docker Desktop/Engine 29.8.0, daemon linux/x86_64. Both containers used network none, read-only root/source, 0.25 CPU, 384 MiB RAM, 64 PIDs, and a separate evidence mount. GPU was not requested.
- Formal runner exit: 0. Independent auditor exit: 1 due to the effective-controls gate. Formal invocations/reruns/replacements/post-result tuning: **1/0/0/0**.
- Frozen runner SHA-256: `6e80cebcea36c76427fad6797a302a2672e965bca280abd4166a3d13872f275c`.
- Frozen auditor SHA-256: `cec0ecb574821887093f3ce5c1583fe35dd5a9096eec38124b8749119086b117`.

Exact retained files and SHA-256:

| File | Bytes | SHA-256 |
|---|---:|---|
| `RESULT.json` | 9,332 | `95d0a5499953c344539b0f64b0925179978cf55806a529c4e89a24074c3f4a0a` |
| `RAW.jsonl` | 3,241,590 | `a25bc4a9e6cf845fb5b446b1d2d5071bd26909679efcc535372fdf77b58b4eb8` |
| `NEGATIVE_CONTROL.json` | 226 | `f3a9f0264d39bb5076fab2a790678235b730ee617736264c8f06f55230b7a7c5` |
| `AUDIT.json` | 207 | `7c6ca7209713294f13f226fae8aac78cd197ad4662cc90f6b1030429e29bda1b` |
| `CONTROLS.json` | 599 | `d9d823f7660f1154d9c3eecedc688daded8720f2b1f5ef81e8644cdc37c89b0e` |

The eight frozen control names were `events`, `edges`, `edge_count`, `linearizations`, `mismatches`, `first_mismatch`, `final_state`, and `event_outputs`. The first audit's exact outcome is retained; the no-op was not replaced and no second audit was run.

## Reproduction commands

The formal invocation mounted frozen source read-only and a fresh evidence directory writable:

```text
docker run --rm --network none --cpus=0.25 --memory=384m --pids-limit=64 --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=16m \
  --mount type=bind,source=<frozen-study-path>,target=/src,readonly \
  --mount type=bind,source=<fresh-evidence-path>,target=/evidence \
  --workdir /src --env OUT=/evidence/formal01 \
  python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9 \
  python -S -B runner.py
```

The auditor used the same image/resource/security bounds with frozen source read-only, the formal evidence mounted writable, `EVIDENCE=/evidence/formal01`, and command `python -S -B audit.py`. Its first output/exit are retained; this report does not claim a successful overall evidence gate.
