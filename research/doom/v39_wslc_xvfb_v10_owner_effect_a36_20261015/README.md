# V10 owner-to-V39 integration A36

A36 is a new WSLc one-shot following A35's predispatch STOP. It tests the merged V10 successful-release record against both PR #8771's strict known-empty receipt predicate and MAP01 V39's strict terminal predicate, with an independent X11 application process and server connection.

A35's stdout readiness transport did not preserve the failing line. A36 moves app events to a dedicated JSONL file and retains separate app stdout/stderr logs. Its full hypothesis, decision rules, and input hashes are frozen in [PREREGISTRATION.md](PREREGISTRATION.md) and `INPUT/FREEZE.json`. A36 is still synthetic X11 evidence; it cannot establish Doom/MAP01 or physical-input behavior.
