# Issue #6102 — visible modal call/return matching T0

**Disposition: `PASS_METHOD_SCOPED` for the frozen finite trace corpus only.** This tests a specific application-state monitor idea, not a production GUI, safety property, runtime feature or arbitrary-depth theorem. It follows the Issue’s 2026-10-01 method corrections: a depth-matched finite-state machine is expected to match a stack on the declared bounded domain, and finite IDs do not imply support for arbitrary live identity tokens.

## H / T / D / C / U

- **H:** With source-bound nested open/close events and a finite identity/generation alphabet, a stack monitor and depth-3 finite-state encoding should preserve exact parent context equally. A flat `modal_open` bit should lose parent matching. Missing, stale, duplicate, wrong-parent, non-LIFO, interleaved-window, unknown-ID and over-depth evidence must yield `UNKNOWN_NESTING`.
- **T:** Fourteen deterministic cases, four valid traces at depths 0–3 and ten invalid controls, with three candidate policies: flat flag, explicit stack, and finite-state monitor encoding the bounded stack tuple. The independent auditor consumes raw event/output rows and does not import candidate code. One frozen candidate run, one audit, one identical-source repeat; no RNG or network.
- **D:** Stack and depth-3 FSM matched the independent oracle on 14/14 cases; all 10 invalid controls were rejected by both; the flat flag falsely accepted 6/10 invalid traces, including the explicit wrong-parent close followed by an unauthorized root-context action. The independent audit reports zero errors and `PASS_METHOD_SCOPED`; six mutation tests pass. Repeated candidate output is byte-identical.
- **C:** These are authored finite traces with root plus three modal IDs and generations 1–2, and a declared maximum depth of three. The FSM is a canonical tuple-state encoding of that bounded stack; equality is expected, not evidence of stack superiority. Source-bound event observability is assumed by construction.
- **U:** No live GUI/event instrumentation, task outcome, input authority, safety, performance, arbitrary/unbounded-depth proof, arbitrary-ID/register-stack semantics, or cross-app generalization. Non-LIFO and independently interleaved windows fail closed rather than being modeled as one stack.

## Results

| Policy | ACCEPT | `UNKNOWN_NESTING` | Interpretation |
|---|---:|---:|---|
| Stack | 4 | 10 | Matches oracle for the full corpus |
| Depth-3 finite-state encoding | 4 | 10 | Exactly matches stack/oracle on this bounded domain |
| Flat modal flag | 10 | 4 | Falsely accepts 6 invalid traces; wrong-parent-close counterexample is retained |

The 42 total event transitions cover all 14 traces. The largest observed per-trace FSM state count is four; this is trace accounting only, not a minimized automaton-size or runtime-cost result.

## Construction history and provenance

Preparation and run base: main `f0139613cb96d5f2d84e803b75961dff549d58c8`. Freeze timestamp, exact source/protocol/test SHA-256 values, image digest, Docker Engine and platform are in `FREEZE.json`.

The first construction auditor rejected 10 FSM failure rows because its independent expected error-row schema omitted the candidate’s transition count. Candidate raw and the failing initial audit are preserved as `construction_raw_initial.jsonl` and `construction_audit_initial.json`; this was an auditor/candidate-output contract mismatch, not a scientific candidate result. The auditor was corrected before freeze, then the complete construction rerun passed. Those initial artifacts are not overwritten or pooled with the frozen run.

Official execution used OrbStack Docker Engine 29.4.0, Linux ARM64, pinned `python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, `--network=none`:

```sh
python simulate.py raw.jsonl
python audit.py raw.jsonl > audit.json
python simulate.py raw-repeat.jsonl
cmp raw.jsonl raw-repeat.jsonl
python -m unittest -v test_modal_monitor.py
python -m py_compile simulate.py audit.py test_modal_monitor.py
```

The byte-identical repeat, independent audit, all construction/official outputs and their SHA-256 values are retained in this directory and listed in `SHA256SUMS`. No Obstac-specific executable or MCP interface was available in this session; OrbStack Docker was used for the isolated container runs.
