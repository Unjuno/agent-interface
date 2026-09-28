# W2 lease-close and terminal-order candidate v2

This additive revision leaves candidate v1 and its original six-case result unchanged. It adds a terminal interval boundary after the lease-open/lease-close checks and an independent raw-row oracle implementation. Candidate and oracle remain construction-only; neither is the frozen production verifier.

Run the boundary probe with Python 3.12.10 from this directory:

```powershell
python probe_terminal_order.py
```

The five scenarios are retained in `TERMINAL_ORDER_PROBE.json`: edge before terminal, after terminal, overlapping terminal time, unknown terminal time, and multiple terminal events. Expected outputs are respectively authorization, post-terminal rejection, uncertainty hold, unknown-time hold, and rejection when any terminal interval is strictly before the edge. Candidate/oracle agreement is necessary but is not formal acceptance.

`FREEZE_candidate_v2.json` pins source and fixture identities. `RESULT_candidate_v2.json` includes the probe hash and individual candidate/oracle source hashes. Host-only evidence; no Docker, runtime authority, GUI/model action, or integrated claim.
