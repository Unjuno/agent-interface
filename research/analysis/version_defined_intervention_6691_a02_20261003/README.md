# Issue #6691 — A02 audit-only OrbStack successor

This new allocation addresses the exact unresolved boundary in A01: candidate and raw output were retained, but the auditor container did not start. It copies A01's source and outputs byte-for-byte, then runs only the raw-only auditor in a fresh OrbStack container. A01 remains unchanged; A02 candidate invocation count is fixed at zero.

H/T/D/C/U, input hashes, runtime and one-shot counts are frozen in `FREEZE.json`. This is an audit-only successor, not a rerun of the consumed A01 candidate allocation and not a blind new-data replication. Formal execution pending.
