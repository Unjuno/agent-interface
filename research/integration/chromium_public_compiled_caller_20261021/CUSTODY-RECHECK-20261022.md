# r09 custody recheck (2026-10-22)

This additive note records a read-only recheck of the packet before transfer to
the current-main repository. The original source worktree and its files were
not modified, and no browser, provider, or experiment runner was started.

The retained `audit-recheck-r09.json` records that on 2026-10-21 its temporary
copy recomputed `PASS_POLLING_BRANCH_SCOPED_SINGLE_TRIAL`, matched the stored
audit, and found all 317 then-listed artifact hashes. A later packet README
update changed `README.md` without refreshing `artifact-sha256-r09.txt`. On
2026-10-22, the current packet therefore matches 316/317 artifact entries; the
only mismatch is `README.md`. All 316 matching files, including the r09 raw
inputs, remain byte-identical to the manifest. The earlier recheck is retained
as a historical result, not rewritten to agree with this later state.
The README's opening sentence also still says the packet contains r01-r08,
although the r09 section follows; this is a stale scope line, not a change to
the retained r09 raw result.

The frozen source manifest contains 179 entries. Comparing it with the extant
source worktree finds 161 matches and 18 changed files, including the runtime
caller, supervisor, X11 backend, and compiled-GUI implementation. The packet
identifies its source as dirty branch
`research/owned-cancel-supervisor-prototype-r01`, HEAD
`ef768ac74517d70c43c7b673b6ea4319db87d4f4`, based on `bc10001a7a5e5648360d5cfa209248b65f15aacd`.
The exact dirty source snapshot is not reconstructed by this transfer. Do not
describe r09 as a run on current `main`, and do not treat its implementation
as current without a separate source audit.

The packet remains useful as one scoped live Chromium/App Server result: its
prior independent audit passed, the public compiled caller exercised the
pending/poll/reobserve path, and an independent fixture scorer verified the
single expected submission. It remains one synthetic localhost-fixture trial,
not a matched comparison, reliability estimate, physical-desktop/MAP01 result,
or WSLc result. The run is consumed and must not be repeated. Recheck the
source against the intended integration before using it to support adoption.

The transfer is additive. The original dirty worktree, its unrelated changes,
and this packet's original manifest and audit remain preserved.
