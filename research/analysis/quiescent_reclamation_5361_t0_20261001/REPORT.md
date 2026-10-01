# Issue #5361 T0 — quiescent authority reclamation

## Result

`PASS_METHOD_SCOPED` for the frozen two-reader finite-state model only.

- Candidate: `py -3.11 -B run_model.py` — one invocation, exit 0.
- Independent audit: `py -3.11 -B audit_raw.py` — one invocation, exit 0,
  `errors=[]`, all 5/5 mutation controls rejected.
- Reachability: 32 states and 288 directed event transitions.
- Revoke-only counterexample: `A0 → R → U0`; the old active reader uses the
  epoch after REMOVE was treated as immediate reclamation. Independent
  enumeration found 8 baseline active-reader uses after its claimed reclaim.
- Two-phase result: 8 uses remain allowed after REMOVE while a reader is still
  active (the protocol is not conflating revocation with quiescence), then no
  use is admitted after that reader quiesces or is fenced. No reachable state
  permits active old-generation use after the model's actual reclaim point.
- A stale-epoch quiescence receipt changed 0 states. A current-generation
  fence moved active readers to FENCED and blocks their later use.
- Raw candidate SHA-256:
  `0ca7432af56eb035b1a88fcf122a81596c7113c49a65c01f68ca9e450b135f1e`.

## Frozen execution

The preregistration and source hashes are in `FREEZE.json`, based on main
`3d6ffc76d535309cf3820ed33cb9327354f03648`. CPython 3.11.9 ran the
deterministic CPU-only model on Windows. Docker/OrbStack and GPU were not used:
no shared-container or GPU lease was assigned to this task, and neither is
needed for this exhaustive finite-state replay. No retries, model, network,
GUI, OS input, or external effects occurred. Construction tests passed 3/3;
Python compilation and `git diff --check` passed before execution.

## Scope and follow-up

This validates only the encoded protocol distinction under a complete reader
set, truthful quiescence, and trusted generation fence. It does not establish
reader registration completeness, crash/malicious-reader handling, distributed
lease expiry, memory reclamation correctness, production safety, or availability.
An implementation experiment would need concrete reader/authority identities,
replay-resistant ACK provenance, failure/timeout rules, and a source-bound
runtime boundary. The result does not close #5361 or #59.
