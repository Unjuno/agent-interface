# R07 corrected exact-call timeout drain check

R06 was a harness-design failure: the successful generic observation report does not contain a call ID, and a one-shot server has no `interface_close` tool. The failed R06 runs remain preserved and unscored. This is a separately numbered two-sample follow-up against the corrected test source.

The caller is still forced to time out at 8 seconds while the fake observer is event-blocked. The test obtains the call ID from the read-only current-server call list, releases the one observer, awaits the same Future for up to 30 seconds, verifies the finalized report and exact-call readback, then lets the temporary directory close. No dispatch occurs. Run one normal and one `-O` process, no retries. Full conditions and source digest are in `conditions.json`.

A pass validates only this deterministic fake test-harness callback path. It does not establish production recovery reliability or explain R04's action-result timeouts.
