# Report — AI-6147-T1-ORB-X11-20261003-01

**Disposition: STOP / NOT_EVALUATED.** The formal allocation did not complete and supports neither H_PASS_SCOPED nor H_FAIL_SCOPED.

The pinned OrbStack run reached only the adaptive arm. One candidate container ran once and exited 1 while closing its Xlib display: `Xlib.error.ConnectionClosedError: Display connection closed by server`. The fixture had already completed all ten hidden cases, emitted 44 oracle events, and exited 0. Candidate inspect records `OOMKilled=false`; fixture inspect records `OOMKilled=false`. The candidate emitted ten JSONL rows, but no independent auditor ran and the frozen gate requires both clean execution and independent raw-only replay. No claim is made from the apparent choices in those rows.

Per the frozen no-retry rule, `no_probe` and `one_step` were not launched, no auditor was launched, and this allocation was not rerun or tuned. Partial evidence is preserved under `raw/formal_01/` with a separate SHA-256 manifest. The stop diagnosis and detailed process accounting are in [STOP.md](STOP.md) and [RUN_RECORD.json](RUN_RECORD.json). Construction-only GUI and test passes remain construction evidence, not substitutes for the incomplete formal allocation.

A future successor allocation may address the client/fixture display teardown race, but must use a distinct allocation identity and preserve this STOP and its raw bytes unchanged.

The post-run README status update changed its frozen documentation hash entry. The preregistered manifest was not rewritten; execution-bearing sources and inputs remain verified. See [POST_RUN_PROVENANCE.md](POST_RUN_PROVENANCE.md).
