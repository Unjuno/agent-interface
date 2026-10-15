# PR #7109 convergence and saved boundary qualification

Preserve all 261 original PR paths from exact head
`8394ab7f4a82cafc29a851c28afd56d7a1c8f804` on current main without adopting
historical runtime code or rerunning experiments. `ORIGINAL_PATHS.json` records
their original Git blob identities. Six additive scoped attribute files preserve
raw byte images. The only archived `.py` is `construction-initial/selftest.py`:
it launches Xvfb at module import, so it is retained as source and was **not
imported or executed**. It does not match the `test*.py` discovery convention.
Other producer/native sources remain in inert text/envelopes. No workflow,
runtime, dependency or input permission is changed.

The first local archive import converted line endings in 241 paths. Custody
verification detected that mismatch before publication. A corrective commit
restored raw bytes directly from Git blobs; all 261 now match. The mismatch list
is retained in the host consolidation directory as
`pr7109-first-import-custody-failure.json`. The auditor also recomputes every
original Git blob ID from file bytes, without invoking Git or any producer.

Historical C01 HOLD, C02 dummy-FD finite PASS, C04 STOP and C05 finite comparison
remain separate. C05's metric ends when the owned key is up while the bystander
remains held; whole-map neutrality is only after fixture cleanup. Two samples
per mode do not establish reliability or a physical bound. Later metadata
qualification finds five contradictory copied records accepted by the frozen
oracle and rejects them with its alternate reader; neither original raw nor
first scientific verdict is rewritten. Old review/allocation notes are historical
records, not current permissions or a new reviewer-quorum requirement.

## New saved-only check

`audit.py` reads the original base64/gzip/JSON envelope, verifies fixed container
hashes and sizes, and validates all 274 public member hashes against their
projection records. It never imports any saved producer, opens a socket/display,
starts a process/container/VM, or emits input. Public projections are verified as
published bytes; private-original custody claims in metadata are not independently
verified by this check.

Two named result bodies are checked with a distinct implementation:

- Server-global stop: both queries remain pending, local shutdown retires only
  the main query, independent completion follows server resume, the returned map
  is neutral, no input was emitted, and final threads/server are terminal.
- Python-Xlib 0.33 socket timeout: a 50 ms socket setting coexists with both
  requests pending across the recorded additional >=200 ms no-reply hold;
  the independent connection completes before the gate and blocked requests
  complete only afterward. All three recorded peer requests are read-only opcode
  106. This is a socketpair fixture, not an X-server or held-input run.

Four test methods check originals, member tampering, duplicate/missing projection
coverage, and 14 copied boundary contradictions, including boolean/integer
substitution. Original timestamps/conditions/gates are preserved; this is a new
qualification of saved evidence, not an independent producer replication.

```sh
python research/concurrency/xlib_boundary_consolidation_20261016/audit.py
python -m unittest research.concurrency.xlib_boundary_consolidation_20261016.test_saved_boundary_audit
python -O -m unittest research.concurrency.xlib_boundary_consolidation_20261016.test_saved_boundary_audit
```

## Consequence for the current control goal

The read-only worker integrated in #8950/#8952 addresses named connection-local
identity/focus blocking. This saved evidence does not qualify current MAP01 input
send/sync/readback or show an independent connection can bypass a stopped server.
Socket shutdown retires a request; it does not prove release, healthy reuse, or
the absence of unknown task effects. C05's ctypes retained-GIL stress is not proof
that the current Python-Xlib backend retains the GIL in the same way. Do not
mandate a process watchdog or claim a physical bound from these results alone.

Next finite implementation check: trace a stalled native input request through
the current selected caller to its unverified obligation/reuse gate, keeping one
input writer and fencing late replies. A hard bound needs an explicitly stated
fault model and resource-side mechanism; task effect/recovery and matched
efficiency remain open in #17/#59. No new live allocation was used.
