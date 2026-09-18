# Ordered interrupt batching A2 — #1876

Task: `EVENT-ORDERED-INTERRUPT-BATCHING-A2-20260919-002`

Direct predecessor #1871 stopped before durable scientific rows because a later in-function import shadowed `ordered_batch`. A2 preserves batch_size4, event semantics, directed controls, exhaustive corpus, metadata, gates and independent-audit semantics. The only harness repair is module-scope import binding in `run_formal.py`.

H: removing local import shadowing permits the frozen #1871 scientific corpus to execute without changing batching semantics.

T: stdlib-only deterministic container. Construction: py_compile PASS, unchanged tests 10/10 PASS, nonformal one-case smoke PASS. Formal: exact #1871 exhaustive sequences length0..6 over four event kinds x two sessions, plus directed controls, one invocation only. Independent audit remains structurally independent.

D: `PASS_ORDERED_INTERRUPT_BATCHING_A2_SCOPED` iff all #1871 sequence/identity/session/metadata/order/reduction/malformed/integrity gates pass with formal1/reruns0/replacements0/tuning0. Harness stop before durable rows is scientific NONE.

C/U: representation-only after scheduler decisions; no model, token, latency, transport atomicity, natural event rate, ACK/retry/task-success or production claim.
