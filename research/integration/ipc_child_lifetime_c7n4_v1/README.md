# Retained IPC child-lifetime evidence — Issue #4421

Retrospective publication of the conversation-local c7n4 allocation. This is not GitHub preregistration and does not rerun the consumed experiment.

Scientific boundary result: **PASS_LOCAL_CHILD_LIFETIME_BOUNDARY**. Production adoption remains **HOLD_CHILD_DESCRIPTOR_CONTRACT_UNVALIDATED**.

The complete original evidence ZIP is retained losslessly as Base64 text parts described by `ARCHIVE.json`.

- ZIP bytes: 613219
- ZIP members: 832
- Expanded bytes: 1113260
- ZIP SHA-256: `2a8ab85627e313b66d9767e39a6bcec58a5abe67f2d8de80c22148bc636e4a9d`

Read-only restoration into a new directory:

```sh
python -S -B restore_evidence.py /tmp/c7n4-review
cd /tmp/c7n4-review/research/integration/ipc_child_lifetime_c7n4_v1
python -S -B verify.py
```

`restore_evidence.py` verifies every text-part hash, the exact ZIP hash, member count/expanded bytes, and canonical regular member paths before writing. It never executes archived code. The restored `verify.py` reruns only retained-data audits, mutation controls and pure gate tests; do not rerun the consumed formal allocation.

No shared runtime or workflow is changed by this publication. #4372 and all predecessor results remain unchanged. The original report's historical statements that GitHub publication had not happened describe the original execution session and are preserved rather than rewritten.
