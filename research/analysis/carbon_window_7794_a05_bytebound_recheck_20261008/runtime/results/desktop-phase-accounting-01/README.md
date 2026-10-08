# Post-hoc session accounting of the frozen desktop comparison

Source evidence is immutable commit `3646d99f28f2ec391c2826445f2538d400d4d6d7`,
merged through #6441. This additive analysis launches no GUI, emits no input,
changes no frozen source/result and repeats no scientific allocation.

## Result: HOLD; no observed economic threshold crossing

| Route | Owners | Uncached input | Output | Uncached + output | Issue-to-terminal-audit-output proxy (s) |
|---|---:|---:|---:|---:|---:|
| A | 5 | 49,889 | 18,167 | 68,056 | 838.003 |
| B | 5 | 57,150 | 16,106 | 73,256 | 762.690 |
| C | 5 | 53,453 | 16,170 | 69,623 | 768.417 |

Compared with A, C has 2.30% more uncached-plus-output tokens and an 8.30%
lower issue-to-terminal-audit-output duration proxy. B has 7.64% more tokens
and an 8.99% lower duration proxy. Neither meets both frozen 20% descriptive
thresholds. This is not a causal or fair-acquisition comparison and does not
prove an actual latency improvement. All routes had 27 commands and 15 input
programs; no roundtrip reduction. Correctness remains 5/5 saved workbooks per
route within this one known task; stronger compiled per-key guards differ.

The five per-route cumulative owner rows are acquisition, warm1, warm2,
changed/refusal plus bounded repair in one owner, and subsequent reuse.
Paired phases are not two independently scored successes. Full per-owner rows
and exact call-ID selections are in report.json / selection.json. Selection is
post-hoc from original allocation-launch calls through original terminal saved
file audit/commit output, with no new execution. Fifteen windows are disjoint;
response IDs are checked for cross-window overlap. Whole-context response usage
is chronological, not provider-attested per-tool charge.

## Costs outside owner windows

Within the earlier joint build/readiness/freeze/all18-through-final-score window,
360,562 uncached input and 17,282 output tokens lie outside these owner windows.
These include preparation and intervening controller/accounting work and are
retained separately, not zero and not assigned to a particular route. Per-owner
sums must not be added again to the joint total. Pre-build planning, earlier
construction and later publication remain outside both and are not free.

## Measurement limits and next integration concern

Both duration columns use their own clocks: original source UTC allocation-call
issuance to terminal-audit tool output, and execution-host ready-owner monotonic
time to post-terminal independent file read. They include model/control pauses
and audit work, exclude differing earlier acquisition/construction, and are not
application semantic completion, primary screenshot ingestion, provider inference
latency, or a human-speed baseline. Semantic awareness and first useful model
feedback stay null. Billing is unavailable; cache/reasoning counters are subsets.
Source turn contexts record gpt-6.1-sol / medium throughout the selected owner
windows; exact provider build/configuration and context/cache equivalence are
unproved. The first A owner also has substantially longer retained audit delay.

The strongest practical integration concern remains useful final feedback:
stale/unpainted modal captures, partial/black repeated rendering and target-change
withholding. Existing #3700 already retained a four-row 50/250ms wait comparison
with HOLD, so repeating it or raising defaults without missing host/model evidence
would not establish improvement. A next fresh WSL-native integration successor
should explicitly distinguish caller-selected final wait from one permitted
read-only post-input observation, count both model-boundary costs, and retain
no-redraw-acknowledgement and no-replay semantics. No change to runtime defaults
or automatic polling/sensor is justified by this report.

## Verification

Normal and optimized Python executions reconstruct exactly identical selection,
projection and report hashes from retained source records. Existing projector
validates response identities and counters; this collector explicitly rejects
missing/duplicate owner boundaries, overlapping response IDs, incomplete usage
and negative joint remainder. This verifies accounting of the retained window,
not live perception, model completion, billing or generalization.
