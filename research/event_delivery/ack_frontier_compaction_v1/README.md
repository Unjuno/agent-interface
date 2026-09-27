# ACK frontier after compaction — Issue #4026

**Formal result: HOLD_FORMAL_INCOMPLETE. Execution: STOP_SUPERVISOR_TIMEOUT.**

This is archival research evidence, not a production inbox implementation.
The one preregistered 48-case allocation stopped at its fixed 30-second
supervision limit: 40 complete cases, 188 complete operation-process receipts,
one partial case, no terminal record. No formal rerun was performed.

Read [REPORT.md](REPORT.md) and [SUMMARY.json](SUMMARY.json) for the exact
observed counterexamples and limitations. [PREREGISTRATION.md](PREREGISTRATION.md)
contains H/T/D/C/U, the conditional proof, variables and units.
[CHANGES.diff](CHANGES.diff) identifies the only tested model changes.

The 99 original files, including the unchanged failing full auditor, full
sources, construction evidence, all retained formal rows and database bytes,
are preserved in the nine-part lossless archive described by
[CAPSULE.json](CAPSULE.json). Each binary Git blob matched its independently
computed local object ID at upload. Hashes attest byte identity, not independent
experimental authorship or a separate trust root.

## Inspect without rerunning the experiment

From this directory, choose a destination that does not already exist:

```sh
python -I -S -B unpack.py /tmp/ack4026-review
cd /tmp/ack4026-review
python -I -S -B test_contract.py -v
python -I -S -B audit_prefix.py formal-01 > /tmp/ack4026-prefix.json
cmp PREFIX_AUDIT.json /tmp/ack4026-prefix.json
python -I -S -B audit.py formal-01 --controls
```

The last command MUST fail at `case denominator`. Prefix reconstruction and
construction tests do not change the formal HOLD. Do not rerun `run.py` against
the consumed allocation. The unpacker writes files only; it never executes
archived code. Python 3.13.5 / SQLite 3.46.1 were used originally in the provided
Linux x86_64 container; no Docker/OrbStack engine or image identity is claimed.

This PR preserves a stopped allocation under the existing scientific question.
It neither closes #4026's full acceptance gates nor #3876/#57/#2789/global
ROADMAP. No shared runtime, workflow or predecessor result is changed.
