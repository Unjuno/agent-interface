# Retrospective reclamation evidence — Issue #3978

This publishes the ALREADY EXECUTED e58c allocation; no formal experiment was rerun.
REPORT.md and all113 capsule members retain their original bytes, including the old
STOP_GITHUB_WRITE_TOOL_UNAVAILABLE handoff. This README is the separate publication
addendum. Local hashes were frozen before that original experiment; GitHub issue
#3978 was created afterward and is not a preregistration claim.

The original63-case/126-worker study passed its scoped retained-handle boundary.
Resolved path, directory FD and stream FD produced6,3,0 cross-epoch attributions,
respectively. Nine reclamation/replacement stream-FD cases returned exact old data.
Historical consistency is neither latest-state authority nor ACK/model consumption.
No shared-offset/concurrent preparation/production-host guarantee is implied.

## Restore and re-audit, without running old cases

Seven binary parts encode one lossless XZ UTF-8 file map. PACK.json binds order,
size and hashes; unpack.py validates and restores into a NEW directory only.
From this directory, using fresh destinations:

```sh
python -I -S -B unpack.py /tmp/e58c-retained-review
cd /tmp/e58c-retained-review
sha256sum -c SHA256SUMS
python -I -S -B test_contract.py
python -I -S -B audit.py --input formal/allocation-01 --freeze FREEZE.json --out /tmp/e58c-retained-audit.json
cmp AUDIT.json /tmp/e58c-retained-audit.json
```

The full113-file source/raw/failure bundle restores byte-exact. Re-audit matches the
original AUDIT.json;12 tests pass. PUBLICATION_CHECK.json retains revalidation plus
seven packaging refusal controls. Original ZIP SHA256:
312bd483a9fefa5da341721e7895b0cbb341ae421447b2e7adbed4087c41fdb1.
Checksums are integrity, not authenticity. The supplied Linux execution container had
no Docker engine/image identity. No Docker/OrbStack, GUI/model/task, performance or
production result follows. Keep #3876 and the global ROADMAP open. Shared-descriptor
positions are tested separately in #3984/#3995; neither rewrites this history.
