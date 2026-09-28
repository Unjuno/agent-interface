# Issue #5134 — fresh OrbStack publication allocation after #5073 audit STOP

This is a new successor allocation, not a retry or relabel of #5073's consumed
`-01` formal run. Preserve #5073, PR #5109, its source/raw/audit outputs, and
predecessors #5045/#5066 byte-for-byte. The first formal run captured raw
observations, but its independently launched auditor stopped on defects in the
frozen audit/receipt contract. No scientific PASS/FAIL was established.

## H / T / D / C / U

The exact hypothesis, source identities, outcomes, and limits are frozen in
`FREEZE.json`. This additive recovery path preserves the untracked path that was
already under parallel ownership; only this `_successor/` copy is being edited.
In brief: on one macOS-host OrbStack bind mount, test seven
monotonic publication phases using one fresh formal run and one separate
raw-only audit. The frozen denominator is 56 concurrent reads plus 28 atomic
post-replacement reads (84 total) and 28 unsafe diagnostic reads.

## Corrected source/receipt boundary

The independent auditor reads only raw observations, host invocation receipt,
seed input, frozen source files and Docker inspection receipt; it imports
neither `runner.py` nor `protocol.py`. Before formal, construction tests require
an exact `linux/arm64` value to pass the prefix predicate, reject a wrong
platform, resolve frozen source basenames relative to the mounted experiment
directory, and verify both formal/audit Docker argv by reconstructing each
command from the host receipt. Raw observations do not duplicate host-only
`docker_argv`; the host receipt is its single authoritative source.

## Formal boundary

Construction checks are host-only and never invoke Docker or create formal
outputs. A formal launch requires current-main/source/output identity, explicit
latest owner release markers on both #5074 and #5085 naming this allocation
and frozen main, the pinned OrbStack image/platform, correct Docker context,
and an empty shared inventory. Only then may one formal container run; only a
zero exit allows one separate independent raw-audit container. Both use
network none, read-only root/source/input, one fresh dedicated writable output
mount, bounded resources, dropped capabilities and no-new-privileges. Any
formal invocation/output consumes this allocation; preserve every STOP and do
not retry.

## Queue and integration

Registration is not a resource lease. The previous #5073 slot returned to
arbitration after both containers exited. Do not infer a new lease from that
release, an idle daemon, or a clean inventory. Reconcile active requests on
#5085 and await an exact named assignment before any container construction or
execution. Afterward retain raw outputs, execution/inspection receipts,
hashes, independent audit and scope limits; run local CI and publish through a
reviewable PR. A STOP is not a scientific conclusion.
