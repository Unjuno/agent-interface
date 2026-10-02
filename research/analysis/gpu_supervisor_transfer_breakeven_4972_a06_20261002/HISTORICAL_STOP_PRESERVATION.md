# Allocation-06 historical STOP preservation

Allocation `GPU-SUPERVISOR-TRANSFER-BREAK-EVEN-4972-20261002-06` is terminal as `STOP_BEFORE_CANDIDATE_CAPACITY_DECREASE`. This retrospective sidecar preserves the owner and queue reports associated with PR #6293, original head `94b2fc18c9fe724b09557ab1e689b19891290d3a`. The 11 original source/preparation files remain unchanged.

## Terminal receipt

The frozen window was 2026-10-01 22:45–23:00 UTC. Recorded C: free space declined from 4,356,206,592 bytes at 22:44:29.850 UTC to 4,342,300,672 bytes at 22:46:10.222 UTC, a drop of 13,905,920 bytes. Both readings exceeded 1 GiB, but the preregistered no-decrease gate failed. The slot was released effective 22:46:16 UTC.

Recorded invocations: candidate=0; CUDA=0; formal independent auditor=0; retries=0. No candidate container was launched and no crossover/scientific result exists.

Sources:
- [Owner terminal disposition](https://github.com/Unjuno/agent-interface/issues/5882#issuecomment-5942204103)
- [Queue STOP and release](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5942203858)
- [Original slot assignment](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5941896722)
- [Earlier inventory correction](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5941966016): the pre-assignment inventory was 4,671,324,160 bytes at 22:17 UTC; the original 22:14/4,703,203,328 wording was corrected before the terminal readings above.

## Preservation qualifications

The terminal readings and other start-gate successes are owner/queue reports; raw start-gate and external readback logs are not included in the original package. This review did not recompute the frozen SHA-256 values or rerun preflight. README and RUN_COMMANDS describe historical preparation, not permission to resume this allocation.

PREREGISTRATION requires six formal auditor corruption controls, while frozen audit.py main defines five; `wrong_image_ref` appears only in test_full_auditor_controls.py's construction harness. A reported construction 6/6 does not establish that the formal entrypoint runs six. No formal auditor ran, so this is an implementation limitation of an unexecuted allocation, not an executed audit failure or formal audit PASS.

The auditor compares reported prepare/runner hashes with FREEZE rather than independently hashing those mounted source files; its main verifies its own file hash. Preserve this provenance boundary alongside the reported external readback, whose raw log is absent here.

Historical source, dataset, freeze/base/seed and previous allocation outcomes remain unchanged. No experiment, resource action, cleanup, allocation revival or optional test suite was performed for this integration review.
