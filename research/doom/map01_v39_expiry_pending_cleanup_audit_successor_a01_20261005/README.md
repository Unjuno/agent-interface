# ExecutorV12 A02 raw-audit successor

## H / T / D / C / U

**H.** The merged #7819 A02 audit can accept a malformed emitted release receipt or a non-neutral owner cleanup record because it omits emitted step/token checks, event-order checking, and `buttons_down` emptiness. The retained raw output may nevertheless satisfy those stronger predicates.

**T.** Preserve the merged #7819 A02 candidate JSON byte-for-byte from main `dccf55e264f434ca27f2948fe53be09919047819`. First run six negative mutation controls against the exact predecessor auditor; then run a separate raw-only successor auditor against the unchanged raw and seven end-to-end mutation controls against the successor. Candidate/runtime executions: 0; retries: 0.

**D.** Successor raw audit passes only if the emitted receipt's `(id, step, intent_token, key, owner_id)` matches both admission and owner cleanup, its confirmed-up evidence and actuation match, its event precedes terminal, both owner key/button ledgers and terminal release are verified empty, and final fake/bridge state is empty. Every negative mutation must be rejected.

**C.** The predecessor's six false-accepts are auditor weaknesses, not proof that the original raw result is wrong. The successor rechecks that original raw against the stricter contract; it does not repair or rerun #7819's candidate.

**U.** This is offline raw-evidence auditing of one fake-display schedule. No live X11, OS input, gameplay, task effect, useful feedback, recovery, or Issue #59 completion is established.

## Findings

The exact unmodified A02 JSON is retained at `results/formal_02/candidate.json`. The predecessor auditor accepted six corrupted copies: wrong emitted step, wrong intent token, wrong owner ID, non-physical-up classification, receipt after terminal, and held button in the expiry owner record. The unchanged raw passes the successor audit, and all seven controls (the six mutations plus unchanged positive control) behave as declared.

The stronger raw audit confirms the observed receipt already matches full identity and precedes the terminal; the predecessor's PASS happened to describe this raw correctly, but its auditor could not distinguish those corruptions.

## Environment

The current macOS OrbStack Docker daemon returned `operation not supported` reading a content-store blob even for read-only `docker image ls`; the preceding research PR recorded the same pre-start failure. No identical Docker command was retried. This successor's audit and mutations therefore ran as an explicitly host-only CPython 3.14.5 construction check, not a container-equivalent result. `CONTAINER_STOP.txt` preserves the exact stop boundary.

Run:

```sh
python3 audit_successor.py
python3 test_mutation_gate.py inputs/audit_a02_original.py
python3 test_mutation_gate.py audit_successor.py
```

The first mutation run is expected to exit nonzero with six false-accept test failures; the successor run is expected to pass 7/7. All test mutations are isolated temporary JSON copies; the frozen raw file is never edited.

