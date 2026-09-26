# Validation-completion age (#4010)

Result: **PASS_VALIDATION_COMPLETION_AGE_BOUNDARY_SCOPED**,21/21 cases,
zero retries; independent audit errors0,12/12 corruption controls rejected.
See [REPORT.md](REPORT.md) for evidence, limits and audit-only reproduction,
[PLAN.md](PLAN.md) for the premeasurement H/T/D/C/U and conditional proof,
and [FREEZE.json](FREEZE.json) for exact source and binary identities.

The old FRAME_FRESH label means fresh at receipt. The candidate additionally
qualifies a recorded post-validation sample; neither implies unchanged scene,
action authority, later model consumption, or general GUI success. All6 delayed
validation cases refused at the later sample;3 prompt changed-scene controls
were still age-qualified, explicitly demonstrating the semantic-currentness limit.

Readable Python/C source is accompanied by lossless native.so.xz and four raw
evidence fragments. [ARCHIVE.json](ARCHIVE.json) binds all fragments and their
84-file evidence archive. Use unpack_evidence.py with a NEW destination, then
run audit.py and the unit tests; these operations do not launch an experiment.
Do not execute the consumed formal allocation or use Python -O for its auditor.

Earlier construction failures and the previous13/32 performance HOLD remain
unaltered. This bundle contains the earlier receipts and selected examples,
not the full old performance archive. No shared runtime or parent acceptance
is promoted. #2117/#2789 and the broad roadmap remain open.
