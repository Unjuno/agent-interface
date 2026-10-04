# A03 report — scorer-tail command readiness at an OS socket boundary

**Disposition:** scoped construction PASS for tail command readiness on the frozen PR #7692 source snapshot.

Three Windows socketpair cases used the frozen 3cc9fb83d15c8066386c4c4af3c10699f1829417 adapter, select.select, monotonic clock, and real socket reads. A pre-ready command caused zero tail samples; a command made ready during a 25 ms synchronous callback and one sent during the regular wait each caused one tail sample. All three tails returned CENSORED / command_ready, preserved the complete command bytes, and later delivered exactly one decoded command through the ordinary iterator. Four source snapshots match their recorded Git blobs and hashes; the corrected independent audit passed 28/28 checks and four mutation tests pass.

The candidate output is unchanged. A01 audit/test failures are retained: A01 compared the iterator's decoded line to the wire representation including newline, whereas the iterator correctly removes that delimiter. A02's first test run also imported the A01 module by its unqualified name; its failed test output is retained. The corrected test imports A02 explicitly and passes all six tests. Neither auditor/test repair changed or reran candidate bytes.

The candidate and auditor implementation files were not included in the pre-run FREEZE.json. Their post-run hashes are retained in POST_RUN_READBACK.json, but that readback cannot establish pre-run runner identity; this is a reproducibility limitation of the construction packet.

This is host construction evidence, not a test of process stdin, DoomGame integration, gameplay, GUI or keyboard input, model behavior, recovery, safety, timing distributions, or MAP01 progress. The measured individual durations are descriptive only. The existing live #59 allocation remains unassigned; this probe does not change or consume it.
