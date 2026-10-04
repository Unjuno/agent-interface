# Audit correction record

The first independent audit (`AUDIT_ATTEMPT_V1.json`; preserved byte-for-byte
from `AUDIT.json`) returned `FAIL_AUDIT`. Its frozen checker incorrectly
required `input_admission.grants_input_authority` to be explicitly `false`.
The frozen record omits that top-level key; the strict schema defines its
absence as `false`, and the nested physical measurement and edge both explicitly
record `false`. Candidate source, raw trace, test output, and freeze were not
changed to obtain a pass.

`audit_v2.py` is a separate versioned checker. It retains the exact false
default, independently validates the raw event pair and actuation/physical
intervals, confirms both test logs and the socket no-consumption case, and
preserves the first auditor failure. `AUDIT_V2.json` is the current audit
disposition; A01's initial checker failure remains part of the result history.

The first two V2 audit outputs are also retained as `AUDIT_V2_ATTEMPT.json` and
`AUDIT_V2_ATTEMPT_2.json`; their result parser did not account for the test
runner inserting the test class/module between the method name and status.
The test itself passed in both logs. The final V2 parser validates the full
method-to-status pattern after removing whitespace.
