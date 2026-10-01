# Primary pair: immediate image versus existing completion cue

Disposition: FUNCTIONAL_PAIR_WITH_PRIMARY_FRAME_REVIEW_ERROR;
HOLD_GENERAL_EFFICIENCY. One baseline-first pair, seed 1001072, exact same initial
PNG, app/Save point, 3000 ms acknowledgment and native five-operation click shape.
Frozen source 5933e45ebe713e9e51682fb13069b8e8f7f979ee; archive SHA256
75f51372d5ccf5a161cbce1a355a594095dc8de3be3185ca983c0368d7a7bcb7.
Primary used the same packaged caller/host/relay/public MCP/native X11 path in
Ubuntu/WSL. Each arm allocated once sequentially; no remint/replay/restart.
No production code changes were needed: inputWithFeedback is already implemented.

| Observed endpoint | Immediate image | Explicit cue wait, 5000 ms budget |
|---|---:|---:|
| Input reply local host duration | 85.756 ms | 3169.757 ms |
| Independent Save acknowledgment delay | 3001.060 ms | 3001.842 ms |
| First Saved source capture after acknowledgment | 25646.385 ms | 44.791 ms |
| First Saved reply after acknowledgment | 25672.364 ms | 95.064 ms |
| Saved review-record publication after acknowledgment | 47277.109 ms | 19216.183 ms |
| Public requests, including close | 5 | 4 |
| Primary images | 3 | 2 |
| Native captures | 7 | 6 |
| Input programs / Save effects / acknowledgments | 1 / 1 / 1 | 1 / 1 / 1 |

Immediate response returned verified completed input, but its stored original
image shows READY, not Saved. Primary initially described it as all black;
independent audit disproved that pixel claim and a re-view showed READY. The
original wrong review/decision and first audit failure are retained. See
FRAME_REVIEW_ERRATUM.md. No image was replaced and no live attempt was rerun.
Primary requested one fresh observation instead of replaying Save and viewed Saved.

Cue arm returned matched title and Saved in its first post-input response, with
no extra observation. App events, read only after terminal owner/children, prove
exact-once Save and one Saved acknowledgment in both arms. Title matching alone
is not that oracle. STOP stayed absent and neutral releases were verified.

The cue wait deliberately delayed the first response by the app's ~3 s processing,
while eliminating one primary observation round trip in this task. It is not a
universal speed win: immediate status is earlier input feedback, cue response is
later effect-visible feedback. The baseline had a primary frame-review error and
large primary/control/review delays. Review-record publication is an attribution
boundary, not provider semantic-awareness timing. The ~45 ms acknowledgment-to-
capture result is local app/capture evidence, not a human reaction comparison.
One pair, fixed order, identical known fixture and unmeasured cache/model/provider
revision effects cannot establish general latency, cost or token savings. Actual
combined usage is now source-projected in [USAGE.md](USAGE.md); billing and
arm-specific cost are unavailable. Do not subtract these wall-clock intervals
and call the difference model reasoning improvement.

Decision for integration: keep explicit per-task cue waiting available alongside
immediate observation; do not globally lengthen/default waits. Completion-aware
waiting can prevent an extra primary round trip when there is a bounded reliable
app cue; it cannot replace visible-state review or independent effects. Evaluate
richer apps and absent/unstable cues before a broad recommendation.

verify.py checks original host metadata/native PNG identity, terminal cleanup,
exact effects, release neutrality, same input shape and initial pixels, frozen
request/capture counts and capture/app ordering. Three effect counterexamples are
rejected. Normal and -O audits passed after removing the disproven black-frame
assumption; first failure remains. This finite audit is not a general safety proof.
The live scaffolds and all raw first outcomes are retained. Parent #6077 and draft
#6101 remain separately pending; this additive report is local for the next batch.
