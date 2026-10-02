# Result: FAIL_METHOD

The preregistered synthetic comparison ran once in Microsoft WSL Containers
(WSLc) using the frozen local Python image. Construction tests passed 7/7;
candidate exited 0 and emitted 4,096 grid rows plus 28 fault rows. The one-shot
independent auditor exited 1 with 8,224 audit errors. Therefore neither
candidate behavior nor apparent comparative wins are validated evidence.

The auditor's failures are concentrated in JSON round-trip representation:
importance-label dictionaries use string keys after serialization while the
auditor expected integer keys, and invalid-context decoded_by_deadline
serializes as an empty object while the independent model expected null. This
is a method failure, not evidence of real FEC or transport performance. The raw
candidate output and audit report are immutable evidence; hashes and exact
container IDs are in FREEZE.json. Runtime warning about missing swap-limit/cgroup
support is retained there verbatim.

The frozen summary reports 128 wins / 0 losses / 896 ties for unequal versus
equal repair, and 77 / 7 / 940 for mandatory-first versus raw-all retransmit.
These are exploratory values only because the independent audit failed. No
advantage claim passes the preregistered gate.

No retry or in-place repair was performed. A future attempt must be a new
successor allocation and preserve this result unchanged.
