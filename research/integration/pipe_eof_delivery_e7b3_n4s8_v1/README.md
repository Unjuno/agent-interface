# EOF settlement evidence publication STOP — #4334

**HOLD_PENDING_PERMITTED_PUBLICATION. Metadata only; do not merge as complete evidence or close #4334.**

This directory contains only this README, PUBLICATION_STOP.json and REVALIDATION.json.
It does not contain original source, byte payloads, process traces, audit code or an evidence capsule.
No shared runtime, workflow, index or predecessor was changed.

## What was actually verified

The already executed e7b3 local pilot remains PASS_LOCAL_PIPE_EOF_SETTLEMENT_BOUNDARY:
24 cases,108 actor processes,38 data pipes,six batches. Sender-exit snapshot settlement
exceeded the4096-byte per-case budget in8 cases; EOF-count settlement exceeded it in0.
The latter reclaimed12288 unused bytes across its12 cases. Partial bytes are not complete
message success. These are retained historical measurements, not new samples or a formal,
model-utility, task-effect or production PASS.

This continuation restored all1020 original files (1457506 bytes), checked1019 manifest
entries and13 frozen files, and ran the unchanged read-only verifier. The3506-check pilot
audit and both construction audits reproduced byte-for-byte. All24 saved mutation outputs
reproduced and10 unit methods passed. Scientific transport actors,GUI,human and model trials:0.
These are local checks, not GitHub CI or independent human review.

## Why publication stopped

Issue and branch creation succeeded. Readable actor.py was registered as one unreferenced
Git blob. The next create_blob request, for readable UTF-8 source/policy.py, was blocked:

> This tool call was blocked by OpenAI because we couldn't determine the safety status of the request.

No further reason was supplied. The source was not retried through another operation,
path or encoding; no capsule containing it was uploaded. The actor blob is not attached
by this branch or PR. Object existence is not complete reachable evidence delivery.
This is an operation-specific publication stop, not a scientific FAIL or general GitHub
write/authentication failure. The original local evidence and earlier publication records
remain unchanged. Unrelated blocks in #4322/#4333 are not retried here.

## H / T / D / C / U and roadmap

H: retained exact evidence can be reconstructed without repeating consumed science.
T: all original identities,three audits,24 saved controls and10 units,then permitted
publication and exact Git-object readback. D: local reconstruction passed; full remote
delivery remains unmet,so retain Draft/HOLD. C: same-author separate audit,not external
review; metadata hashes do not establish remote raw retention. U: authentication,
reader/ledger restart,writer-never-closes liveness,model viewing,task benefit and performance
remain untested. Anonymous-pipe EOF is not full-message or task success.

Completed: intake and ownership check -> immutable revalidation -> Issue/branch ->
publication STOP metadata. Remaining: permitted complete source/raw delivery -> exact
remote reconstruction -> applicable checks/review -> qualified evidence-only main merge.
Keep the owned branch while the Draft depends on it. No scientific rerun is authorized
merely to improve publication status. Global ROADMAP and all other allocations stay separate.
