# A03 construction record

This is construction evidence only; no formal candidate output was written.

The first regression run showed the predecessor's failure-forward event had
`failure_entries=2` but an empty snapshot (`2 != 0`). It also showed the
predecessor auditor had no safe mutation helper for the broker's `B:A` record.
A separate scenario-structure test then failed because the unknown-clock case
looked up tier B without first forwarding the receipt from A. The initial
unittest path-style command was malformed and failed module import; rerunning
with the dotted unittest module path produced these intended red results.

A03 detaches cache/failure snapshots when events are emitted, mutates the
typed `B:A` retry record in the auditor's planted corruption control, and
adds an A→B copy at time 4 before the unknown-clock lookup at time 5. The
construction suite then passed all four tests, including an in-memory run of
all cases and all six corruption controls. This does not substitute for the
post-freeze candidate run or independent audit.
