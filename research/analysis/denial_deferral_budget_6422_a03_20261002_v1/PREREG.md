# A03 preregistration — one-use deferral evidence (Issue #6422)

## Question and scope

This is a distinct, finite, synthetic, no-effect CPU method test of the gap documented after merged PR #6473: can a source-stated, independently verified deferral receipt be replayed under a new request ID to obtain another fresh approval prompt? A03 tests one-use evidence consumption separately from a per-scope presentation cap. It does not change or replace A01 (#6449), A02 (#6465), or #6473's 20-case matrix.

- **H:** A bounded policy consumes a verified deferral evidence ID when it permits one clearly labeled fresh request; the same ID cannot cause another prompt even if the requester changes the request ID or resets the per-scope presentation count. A distinct, valid, unused evidence ID may permit its first request. Safety release remains available and never authorizes the effect.
- **T:** Nine frozen cases; each is evaluated under an unbounded legacy comparator and the bounded policy. Cases cover first use, presentation-budget exhaustion, same-evidence replay with a new request ID and fresh presentation scope, distinct evidence first use, observer source, unstated condition, agent assertion, mismatched budget binding, and safety release at cap. Candidate once; independent raw-only audit once; five mutations: omitted label, wrong scope, forged presentation count, effect authorization, suppressed safety release.
- **D:** `PASS_METHOD_SCOPED` only if the independent auditor exactly reconstructs all nine raw cases and both policy rows, validates evidence consumption and request identity/scope, sees zero effect authorization, and rejects every frozen corruption. Otherwise preserve the failure; no retries or seed substitution.
- **C:** Authored finite records and deterministic rules; no stochasticity, implementation extraction, or user interaction. The evidence lifecycle is stipulated.
- **U:** No inference about production agent behavior, real user burden/coercion, comprehension, security, safety guarantees, model quality, or completion of #6422 T0. No T1.

## Frozen inputs and execution boundary

- Repository `Unjuno/agent-interface`, `main` observed immediately before freeze: `121f531be30c3169ebdf49ac06556496896ff28d`.
- Normative source: Issue #6422 body at that intake and the gap statement in [comment #5944813495](https://github.com/Unjuno/agent-interface/issues/6422#issuecomment-5944813495); merged PR #6473 identifies the missing one-use replay case. A03 uses only that newly identified gap.
- Fixture, candidate, independent auditor, and tests are included in this directory. Candidate has no network, model, GPU, CUDA, GUI, or external-effect calls.
- Host: Windows 11, CPython 3.11.9; finite standard-library JSON computation. The candidate/auditor are intentionally host CPU processes: a container/GPU would add no scientific variable to this method-only test. No Docker/OrbStack/WSL command is part of this allocation.
- Attempt budget: candidate 1; independent auditor 1 and only if candidate exits 0; retries 0. Start only after the recorded construction suite passes. Preserve exact outputs, exit codes, and hashes; do not edit or repeat a formal result.
