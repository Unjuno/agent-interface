# Issue #8553 A03 — recovery-policy observation binding

This additive audit-only follow-up checks whether the merged A01 auditor binds serialized policy branch values to authorized observations and concrete transitions. A01's frozen candidate, report, and result are preserved unchanged under `input/`.

The protocol and exact gates are in [`PROTOCOL.md`](PROTOCOL.md). The new raw-only checker is [`branch_audit.py`](branch_audit.py); [`legacy_probe.py`](legacy_probe.py) characterizes the A01 checker on the unmodified artifact and two in-memory diagnostic mutations. Neither script generates a candidate policy.

The formal allocation runs each diagnostic process once after the freeze is committed and recorded on Issue #8553. It preserves the five-case A01 inputs, two probe dispositions, stdout/stderr, exit codes, one-shot record, and checksums. Construction tests are not formal invocations.

The protocol needs only standard-library JSON and finite-state replay. A02's same-host read-only Docker image listing failed on the OrbStack content store with `operation not supported`; it is documented on Issue #8553 and was not retried. No container is required for this file-only audit. The runtime is pinned to host CPython 3.12.13, recorded in the freeze and run receipt.

A02 was held before formal execution when main advanced after its freeze. Its source, pre-run record, and zero formal invocation counts remain in the A02 branch. A03 starts from the resulting current main and preserves the same A01 inputs byte-for-byte.
