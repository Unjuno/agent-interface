# Batched stopped-inspection publication readiness

Reviewed/tested source: fe7bb0c06, stacked on parent PR #6077 exact head
0c20566f59a2bc65b8a945c162d57febef053189. Publishing as a draft against its
branch preserves the parent commit and queued CI. This is review availability,
not main adoption. Older local-only plans are historical; PLAN.md records why
batched stacked publication now supersedes them.

Shared local native CI passed (374 protocol tests, 176 harness tests). Full
selected Node host suite passed 156 tests. Frozen stopped-observe, stopped-results
and interval-eligibility checksum ledgers passed; no old live case was rerun.
All retained first attempts remain unchanged. Local contract checks are not
GitHub runner completion, new model evidence, or latency/cost improvement.

The code exposes only explicit stopped read-only entry points: fresh guarded
observation with no arguments, and full no-image retained receipt retrieval for
one validated ID. Private caller STOP exception cannot be requested through
ordinary call's extra arguments. Input and mint stay blocked; STOP stays sticky.
Original response evidence/error fields, transport failures and no-retry behavior
remain retained. Broken host/evidence storage can prevent even explicit reads.

Two source-frozen self-use allocations show exact-once Save and eventual Saved
while retaining STOP, without remint/replay/reconnect. One read-only historical
retrieval preserved input/cue/source/session and added no image or operation report.
There is no controlled efficiency comparison; token/billing attribution is absent.
The separate #6074 eligibility note reports invalid input handling and recommends
HOLD_RUNTIME_INTEGRATION; that research classifier is not promoted into runtime.
