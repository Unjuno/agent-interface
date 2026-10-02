# #6285 T5 — independent reconciliation of T2's false stops

**H:** T2's candidate rows cover all 10 model states and 13 outcomes; a correct all-row forward universal check therefore reproduces the preimage. `ready_simple` and `already_committed` share the `pixels` cue but have opposite preimage labels. T2's errors are its comparison assertions, not evidence of candidate/oracle disagreement.

**T:** Allocation `BACKWARD-OBSERVABLE-GUARDS-6256-T5-RECONCILIATION-20261002-01`. First inspect actual JSON shape and path resolution in construction tests. Then freeze all input/source hashes and run one independent audit of T2's recorded output, without rerunning T2.

**D/C:** Scoped PASS only if hashes, 10/13 row coverage, independently recomputed preimage, mixed-label pixel pair, T2 raw errors, and unmeasured one-row cost record all reconcile. Otherwise retain STOP/HOLD. This does not define every fair forward comparator or complete #6256's original comparison gate.

**U:** Authored finite fixture only; no measured cost or real GUI/model/effect/safety claim. Docker service stopped and CLI unresponsive; CPU-only read-only audit, no Docker change.

T0/T1/T2/T3/T4 historical outcomes remain immutable. T3 stopped on bad root resolution; T4 stopped on candidate row schema mismatch, both before their audits completed.
