# Integration handoff — locally complete, remote publication not performed

TASK: cache-stream-verification-4029-20260922-01
INTAKE MAIN: 2308b8301d69b7089a2e0636486736ed59b61537
FINAL READ MAIN: 33e86e997d02b769af17a3f03f6035c68927da6e
ADDITIVE NAMESPACE: research/observation_tiles/cache_stream_verification_v1/
PROPOSED BRANCH (not created): research/cache-stream-verification-4029-20260922
REMOTE ISSUE / PR / HEAD: NONE

Contract result PASS_STREAMING_REUSE_CONTRACT_SCOPED; separate time and Python
traced-allocation gates pass.87 cases,525 attempted publications,519 exact outputs,
6 expected exclusive-create refusals.87 actual worker exits0 and7 actual outer
exits0.12 frozen semantic corruption controls rejected.10 excluded construction
methods pass. No formal rerun, replacement, exclusion or post-freeze tuning.

This is a different implementation/resource question following closed #4029 and
the prior chat-local size-cost experiment. Preserve all predecessor outcomes and
original archives. Do not repeat the same raw cases for publication. A later
Issue may describe this scientific successor but must mark GitHub publication as
retrospective: the source freeze was LOCAL before execution, not public on GitHub.
Do not create wrapper-only successor Issues for uploading these bytes.

## Reconstruct then audit (no Pillow needed for audit)

The delivery directory contains directly readable source/report plus a
content-addressed lossless copy of every original file. No original case image
was deleted from the experiment tree; duplicate bytes are stored once only in
the delivery objects. restore.py never imports or executes experiment code.

From the delivery directory:

```sh
python -B restore.py /tmp/cache-stream-reconstruction-01
cd /tmp/cache-stream-reconstruction-01
python -B audit.py --controls > /tmp/cache-stream-reaudit.json
cmp AUDIT.json /tmp/cache-stream-reaudit.json
sha256sum -c SHA256SUMS
```

Use a new destination. `python -B -m unittest -v test_study` is an excluded
construction/regression check and needs Pillow. Do NOT invoke execute_batch.py,
run_batch.py or worker.py against the consumed allocation. Their existing output
and consumed markers are retained. New experiments need different questions or
justified prospectively frozen allocations, not a retry until PASS.

## Adoption boundary

The new wrapper is research-only, not a mainline runtime patch. FULL_PIN and
STREAM_PIN both restore byte-pin reuse above the legacy cap; chunking mainly
reduces validation's traced allocation. Full-file comparison remains required.
The existing immutable current Frame, cooperative quiescent regular-file storage,
known length and digest,4MiB support cap and no-authority meaning must be retained.
Concurrent mutation/check-use atomicity, arbitrary codecs, source freshness,
model delivery, task success and hard deadlines are not solved. For640x480,
traced peak925089->67754B concerns the inspection interval, not whole-process RSS.
Small-input wall time slightly worsened; do not advertise general speedup.

## Remote delivery

Re-read current main, matching open/closed Issues/PRs and ownership immediately
before applying the additive patch. The patch is generated from a synthetic local
Git index; it is NOT a commit descended from actual main. Run git apply --check
on a real clean checkout and inspect that only the owned namespace is added.
Use the included ISSUE_DRAFT.md / PR_BODY_DRAFT.md only as drafts, not remote refs.
Run restored raw audits, actual repository checks and required review before a
merge. Same-author audit is not independent human approval. Do not delete any
other agent branch. No owned remote branch exists in this session to clean.

Source freeze a49e0e746cfbb5bf657006a4c4d99aac1e498d27bef921641e28206fb1fef8ad.
Original audit d0f33cf29c6237f6cb175e4c1879d428c1e4b34bb3f3ca6512686c5ec02b1a94.
Scientific result, evidence completeness, publication, and product acceptance
remain separate. Global ROADMAP is not completed by this evidence.
