# Issue #8553 A02 — recovery-policy observation binding

This additive audit-only follow-up checks whether the merged A01 auditor binds serialized policy branch values to authorized observations and concrete transitions. A01's frozen candidate, report, and result are preserved unchanged under `input/`.

The protocol and exact gates are in [`PROTOCOL.md`](PROTOCOL.md). The new raw-only checker is [`branch_audit.py`](branch_audit.py); [`legacy_probe.py`](legacy_probe.py) characterizes the A01 checker on the unmodified artifact and two in-memory diagnostic mutations. Neither script generates a candidate policy.

The formal allocation runs each diagnostic process once after the freeze is committed and recorded on Issue #8553. It preserves the five-case A01 inputs, two probe dispositions, stdout/stderr, exit codes, one-shot record, and checksums. Construction tests are not formal invocations.

The protocol needs only standard-library JSON and finite-state replay. Docker's read-only image listing currently fails on the OrbStack content-store with `operation not supported`; no container is necessary for this file-only audit and no daemon change or image pull is attempted. Runtime scope is the observed host Python, recorded in the run receipt.
